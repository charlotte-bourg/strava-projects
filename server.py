"""Server for the running helper app."""

import os
import requests
from flask import Flask, flash, render_template, request, redirect, jsonify
from flask_mail import Mail, Message
from celery import Celery, Task
import logging
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import crud
from model import db, connect_to_db
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.environ['FLASK_KEY']

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)

# Celery setup
def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app

app.config.from_mapping(
    CELERY=dict(
        broker_url="redis://localhost",
        result_backend="redis://localhost"
    ),
)
celery = celery_init_app(app)
celery.log.setup(loglevel=logging.DEBUG)

# Retrieve secrets
CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']
REDIRECT_URI = os.environ['REDIRECT_URI']
STRAVA_VERIFY_TOKEN = os.environ['STRAVA_VERIFY_TOKEN']

# Strava endpoints
BASE_URL = 'https://www.strava.com/api/v3'
AUTHORIZE_URL = 'https://www.strava.com/oauth/authorize'
TOKEN_URL = 'https://www.strava.com/api/v3/oauth/token'
DEAUTHORIZE_URL = 'https://www.strava.com/oauth/deauthorize'

# Permission scopes for Strava authentication
SCOPES = 'activity:read_all,profile:read_all'

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.environ['SENDING_ADDRESS']
app.config['MAIL_PASSWORD'] = os.environ['EMAIL_PASS']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

SHOE_ACTIVITIES = {'Run', 'VirtualRun', 'TrailRun', 'Hike', 'Walk'}
USER_FRIENDLY_SPORT_NAMES = {'Run': 'run', 'VirtualRun': 'virtual run', 'TrailRun': 'trail run', 'Hike': 'hike', 'Walk': 'walk'}

# user handling routes 
@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login."""
    return crud.get_user_by_id(user_id)

@app.route('/')
def login_entry():
    """Display login page."""
    return render_template('log-in.html')

@app.route('/log-in', methods=['POST'])
def login():
    """Handle user login."""
    email = request.form.get('email', '')
    password = request.form.get('password', '')
    if not email or not password: 
        return redirect('/')
    remember = True if request.form.get('remember') else False
    user = crud.get_user_by_email(email) 
    if not user:
        flash("There's no account associated with that email! You may sign up for a new account below")
        return redirect('/sign-up')
    if user and crud.check_password(user, password):
        login_user(user, remember=remember)
        flash("Logged in!")
        if crud.strava_authenticated(user.id):
            return redirect('/home')
        # return redirect('/strava-auth')
        return render_template('strava-auth.')
    else: 
        flash("Incorrect username/password combination")

@app.route('/log-out')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash("Logged out!")
    return redirect('/')

@app.route('/sign-up')
def display_sign_up():
    """Display sign-up page."""
    return render_template('sign-up.html')

@app.route('/sign-up', methods=['POST'])
def sign_up():
    """Handle user account creation."""
    email = request.form['email']
    if crud.get_user_by_email(email):
        flash("There's already an account associated with that email!")
        return redirect('/')
    password = request.form['password']
    new_user = crud.create_user(email, password)
    db.session.add(new_user)
    db.session.commit()
    return redirect('/')

@app.route('/home')
@login_required
def logged_in_home(): 
    """Display home page for logged-in user."""
    return render_template('home.html')

# strava authentication routes
@app.route('/strava-auth')
def authenticate():
    """Redirect to Strava authentication."""
    return redirect(f'{AUTHORIZE_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope={SCOPES}')

@app.route('/callback')
@login_required
def callback():
    """Handle callback from Strava after authentication."""
    user = current_user 
    err = request.args.get('error', '')
    if err: 
        flash("Can't set up gear updater without your Strava authentication")
        return redirect('/strava-auth')
    
    # Handle the callback from Strava after user authorization
    code = request.args.get('code')
    scopes = request.args.get('scope')
    scope_activity_read_all = "activity:read_all" in scopes
    scope_profile_read_all = "profile:read_all" in scopes

    # Exchange the authorization code for access and refresh tokens
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code, # obtained from redirect 
        'grant_type': 'authorization_code', # always 'authorization_code' for initial authentication
    }
    
    token_response = requests.post(TOKEN_URL, data=data)

    if token_response.status_code == 200:
        token_data = token_response.json()
        expiration_offset = token_data['expires_in']
        expires_at = datetime.now() + timedelta(seconds = expiration_offset)
        access_token = crud.create_access_token(token_data['access_token'], scope_activity_read_all, scope_profile_read_all, expires_at, user.id)
        refresh_token = crud.create_refresh_token(token_data['refresh_token'], scope_activity_read_all, scope_profile_read_all, user.id)
        user.strava_id = token_data['athlete']['id']
        db.session.add_all([access_token, refresh_token])
        db.session.commit()
        return redirect('/home')

    return 'Authentication failed.'

@app.route('/webhook', methods=['GET','POST'])
def webhook():
    """Handle Strava webhook.""" 
    # handle webhook subscription validation request 
    if request.method == 'GET': 
        hub_challenge = request.args.get('hub.challenge', '')
        hub_verify_token = request.args.get('hub.verify_token', '')
        if hub_verify_token == STRAVA_VERIFY_TOKEN:
            return jsonify({'hub.challenge': hub_challenge})
        elif hub_verify_token:
            return 'Invalid verify token', 403
        else:
            return 'Invalid request'
    # handle event 
    elif request.method == 'POST':
        # gather information required to process event 
        data = request.get_json()
        user = crud.get_user_by_strava_id(data['owner_id'])
        access_token_code = retrieve_valid_access_code(user.id)
        user_default_shoe = crud.get_user_default_shoe(user.id)
        user_default_shoe_strava_id = user_default_shoe.strava_gear_id
        user_default_shoe_name = user_default_shoe.name
        

        # process event asynchronously with celery task 
        process_new_event.delay(data, user.email, user_default_shoe_strava_id, user_default_shoe_name, access_token_code)

        # acknowledge new event with status code 200 (required within 2 seconds)
        return jsonify({"status": "success"})
    else:
        return "Invalid request"

def retrieve_valid_access_code(user_id):
    """Retrieve a valid access code."""
    # return existing valid access code 
    if crud.user_has_active_access_token(user_id): 
        print("using existing access token")
        return crud.get_access_token(user_id).code 
    
    # use refresh token to retrieve new access token 
    token_data = refresh_tokens(user_id)
    print(token_data)
    access_token_code = update_tokens_in_db(user_id, token_data)
    print(f"your new access token is {access_token_code}")
    return access_token_code

def refresh_tokens(user_id):
    """Use user's refresh token to retrieve updated tokens."""
    refresh_token = crud.get_refresh_token(user_id)
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token.code,
    }

    token_response = requests.post(TOKEN_URL, data=data) 
    token_data = token_response.json()
    return token_data

def update_tokens_in_db(user_id, token_data):
    """Update database with new token expiration and codes and return new access token."""
    # retrieve current tokens for user
    refresh_token = crud.get_refresh_token(user_id)
    access_token = crud.get_access_token(user_id)

    # parse relevant data from json response from tokens API
    access_token_code = token_data['access_token']
    refresh_token_code = token_data['refresh_token']
    expires_at = datetime.now() + timedelta(seconds = token_data['expires_in'])
    
    # update token attributes 
    access_token.expires_at = expires_at
    access_token.code = access_token_code
    refresh_token.code = refresh_token_code 
    db.session.add_all([access_token,refresh_token])
    db.session.commit()

    return access_token_code

# display and update gear defaults routes
@app.route('/update-gear')
def updateGear():
    """Display gear update page."""
    return render_template('update-gear.html')

@app.route('/retrieve-gear')
@login_required
def retrieve_gear():
    """Retrieve gear data from Strava."""
    user = current_user
    access_token_code = retrieve_valid_access_code(user.id)

    # retrieve user's shoes from strava
    headers = {'Authorization': f'Bearer {access_token_code}'}
    athlete_details_response = requests.get(f'{BASE_URL}/athlete', headers=headers)
    athlete_details_data = athlete_details_response.json() 
    shoes = athlete_details_data.get('shoes', '')

    shoe_objects = []
    active_shoes = []
    for shoe in shoes: 
        # if the shoe is in the app database, ensure all data is up to date 
        if crud.get_shoe_by_strava_id(shoe['id']):
            shoe_obj = crud.get_shoe_by_strava_id(shoe['id'])
            if shoe_obj.name != shoe['name']:
                shoe_obj.name = shoe['name']
            if shoe_obj.retired != shoe['retired']:
                shoe_obj.retired = shoe['retired']
            if shoe_obj.nickname != shoe['nickname']:
                shoe_obj.nickname = shoe['nickname']
        # if shoe isn't yet in app database, add it
        else: 
            shoe_obj = crud.create_shoe(shoe['id'], shoe['name'], shoe['nickname'], shoe['retired'], user.id)
            shoe_objects.append(shoe_obj)
        # only display active shoes on the front end 
        if not shoe_obj.retired:
            active_shoes.append(shoe_obj)
    db.session.add_all(shoe_objects)
    db.session.commit()
    default_shoe = crud.get_user_default_shoe(user.id)
    return render_template('set_default_gear.html', default_shoe = default_shoe, shoes = active_shoes)

@app.route('/set-default-run-gear', methods=['POST'])
@login_required
def set_default_run_shoes():
    """Update the default running shoes for a user. """
    user = current_user
    previous_default_shoe = crud.get_user_default_shoe(user.id)
    new_default_shoe_id = int(request.form['dropdown'])
    if previous_default_shoe and previous_default_shoe.id == new_default_shoe_id:
        return redirect('/retrieve-gear')
    else:
        if previous_default_shoe:
            previous_default_shoe.run_default = False
        shoe_obj = crud.get_shoe_by_id(new_default_shoe_id)
        shoe_obj.run_default = True
        db.session.commit()
    return redirect('/retrieve-gear')

# process new activity routes 
@celery.task
def process_new_event(data, user_email, user_default_shoe_strava_id, user_default_shoe_name, access_token_code):
    """Process new event from Strava webhook."""
    # ignore events that don't represent creation of a new activity 
    if data['object_type'] != 'activity' or data['aspect_type'] != 'create':
        return 

    # retrieve detailed information on newly created activity from activities API
    activity_id = data['object_id']
    headers = {'Authorization': f'Bearer {access_token_code}'}
    params = {'include_all_efforts': False}
    activity_details_response = requests.get(f'{BASE_URL}/activities/{activity_id}', headers=headers, params=params)

    # parse gear and sport type 
    activity_details_data = activity_details_response.json()
    strava_gear_id = activity_details_data['gear_id']
    sport_type = activity_details_data['sport_type']

    # check if activity type is out of scope for gear checker (only activity types that can have a default shoe are in scope)
    if sport_type not in SHOE_ACTIVITIES: 
        return

    # check if gear used is the default for the sport per user settings in app 
    if strava_gear_id == user_default_shoe_strava_id:
        sport_type_user_friendly = USER_FRIENDLY_SPORT_NAMES[sport_type]
        activity_date = datetime.strptime(activity_details_data['start_date_local'], '%Y-%m-%dT%H:%M:%SZ')
        activity_date_friendly = activity_date.strftime('%m/%d')
        send_email(user_email, sport_type_user_friendly, user_default_shoe_name, activity_date_friendly)

def send_email(recipient_address, sport_type, user_default_shoe_name, activity_date):
    """Send email notification."""
    # build message
    msg = Message(f'Check your gear on your {sport_type} on {activity_date}', sender = 'stravagearupdater@gmail.com', recipients = [recipient_address])
    msg.html = f"Hello athlete!<br> \
        You logged a {sport_type} on {activity_date} using your default gear ({user_default_shoe_name}). <br> \
        If that's the gear you used, you can ignore this message! \
        Otherwise, this is your reminder to update your gear."  
    print(msg.recipients)
    mail.send(msg)

if __name__ == '__main__':
    connect_to_db(app)
    app.run('0.0.0.0', debug=True)
    app.app_context().push()