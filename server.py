"""Server for the running helper app."""

import os
import requests
from flask import Flask, flash, render_template, request, redirect, session, jsonify
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
app.config['MAIL_USERNAME'] = 'stravagearupdater@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ['EMAIL_PASS']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

@app.route('/')
def login_entry():
    """Display login page."""
    return render_template('login.html')

@app.route('/update-gear')
def updateGear():
    """Display gear update page."""
    return render_template('update-gear.html')

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login."""
    return crud.get_user_by_id(user_id)

@app.route('/sign-up')
def display_sign_up():
    """Display sign-up page."""
    return render_template('sign-up.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        remember = True if request.form.get('remember') else False
        user = crud.get_user_by_email(email) 
        if not user:
            flash("There's no account associated with that email!")
            return redirect('/sign-up')
        if user and crud.check_password(user, password):
            login_user(user, remember=remember)
            flash("Logged in!")
            if crud.strava_authenticated(user.id):
                return redirect('/home')
            return redirect('/update-gear/strava-auth')
        else: 
            flash("Incorrect username/password combination")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash("Logged out!")
    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if request.method == 'POST':
        email = request.form['email']
        if crud.get_user_by_email(email):
            flash("There's already an account associated with that email!")
            return redirect('/login')
        password = request.form['password']
        new_user = crud.create_user(email, password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/update-gear/strava-auth')
def authenticate():
    """Redirect to Strava authentication."""
    return redirect(f'{AUTHORIZE_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope={SCOPES}')

@app.route('/update-gear/callback')
@login_required
def callback():
    """Handle callback from Strava after authentication."""
    user = current_user 
    err = request.args.get('error', '')
    if err: 
        flash("Can't set up gear updater without your Strava authentication")
        return redirect('/update-gear')
    
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
    
    response = requests.post(TOKEN_URL, data=data)

    if response.status_code == 200:
        token_data = response.json()
        expiration_offset = token_data['expires_in']
        expires_at = datetime.now() + timedelta(seconds = expiration_offset)
        access_token = crud.create_access_token(token_data['access_token'], scope_activity_read_all, scope_profile_read_all, expires_at, user.id)
        refresh_token = crud.create_refresh_token(token_data['refresh_token'], scope_activity_read_all, scope_profile_read_all, user.id)
        user.strava_id = token_data['athlete']['id']
        db.session.add_all([access_token, refresh_token])
        db.session.commit()
        return redirect('/home')

    return 'Authentication failed.'

@app.route('/retrieve-gear')
@login_required
def retrieve_gear():
    """Retrieve gear data from Strava."""
    user = current_user
    access_token_code = retrieve_valid_access_code(user.id)
    headers = {'Authorization': f'Bearer {access_token_code}'}
    resp = requests.get(f'{BASE_URL}/athlete', headers=headers)
    resp = resp.json() 
    print(resp)
    shoes = resp.get('shoes', '')
    shoe_objects = []
    active_shoes = []
    for shoe in shoes: 
        print(shoe)
        if crud.get_shoe_by_strava_id(shoe['id']):
            shoe_obj = crud.get_shoe_by_strava_id(shoe['id'])
            if shoe_obj.name != shoe['name']:
                shoe_obj.name = shoe['name']
            if shoe_obj.retired != shoe['retired']:
                shoe_obj.retired = shoe['retired']
                # if a shoe is retired, it won't be returned with athlete, handle that
                print('HEY theres a discrepancy in shoe retirement')
            if shoe_obj.nickname != shoe['nickname']:
                shoe_obj.nickname = shoe['nickname']
        else: 
            shoe_obj = crud.create_shoe(shoe['id'], shoe['name'], shoe['nickname'], shoe['retired'], user.id)
            shoe_objects.append(shoe_obj)
        if not shoe_obj.retired:
            active_shoes.append(shoe_obj)
    db.session.add_all(shoe_objects)
    db.session.commit()
    print(active_shoes)
    return render_template('gear_setup.html', shoes = active_shoes)

@app.route('/set-default-gear', methods=['POST'])
@login_required
def update_default_gear():
    """Update default gear settings."""
    shoe_id = request.json['shoe_id']
    activity_types = request.json['activity_types']
    print(activity_types)
    print(shoe_id)

    # Checks and unchecks
    # If any other gear is default for that activity for that user, uncheck
    # If...
    # shoe_id = request.form['shoe_id']
    # activity_types = request.form['activity_types']
    # print(f"HEYYYYYY!!!!!!!! set {shoe_id} as default for {activity_types}")
    return {
        "success": True}

@app.route('/home')
@login_required
def logged_in_home(): 
    """Display home page for logged-in user."""
    return render_template('home.html')

@app.route('/webhook', methods=['GET','POST'])
def webhook():
    """Handle Strava webhook."""
    if request.method == 'GET':
        print("hello :)")
        hub_challenge = request.args.get('hub.challenge', '')
        hub_verify_token = request.args.get('hub.verify_token', '')
        if hub_verify_token == STRAVA_VERIFY_TOKEN:
            print("we out here")
            return jsonify({'hub.challenge': hub_challenge})
        elif hub_verify_token:
            print("we here actually")
            return 'Invalid verify token', 403
        else:
            print("there's a problem")
            return 'Invalid request'
    elif request.method == 'POST':
        data = request.get_json()
        print("we got a post request on our webhook")
        user = crud.get_user_by_strava_id(data['owner_id'])
        process_new_activity.delay(data, user.id, user.email)
        print(data)
        return jsonify({"status": "success"})
    else:
        return "Invalid request"

def retrieve_valid_access_code(user_id):
    """Retrieve a valid access code."""
    if crud.user_has_active_access_token(user_id): 
        access_token = crud.get_access_token(user_id)
        print(f"existing access code: {access_token.code}")
    # Use refresh token to retrieve new access token 
    else: 
        print("exchanging for new access token")
        refresh_token = crud.get_refresh_token(user_id)

        data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token.code,
        }

        response = requests.post(TOKEN_URL, data=data)  # Make request for new access code
        response = response.json()

        # Process response to update codes and expiration time in database
        expiration_offset = response['expires_in']
        expires_at = datetime.now() + timedelta(seconds = expiration_offset)
        access_token = crud.get_access_token(user_id)
        access_token.expires_at = expires_at
        access_token.code = response['access_token']
        refresh_token.code = response['refresh_token']
        db.session.add_all([access_token,refresh_token])
        db.session.commit()

    return access_token.code

@celery.task
def process_new_activity(data, user_id, user_email):
    """Process new Strava activity."""
    with app.app_context():
        print(f"HEY UR USER IS {user_id}")
        activity_id = data['object_id']
        print(f'hey! thanks for telling me to process activity {activity_id}')
        access_token_code = retrieve_valid_access_code(user_id)
        headers = {'Authorization': f'Bearer {access_token_code}'}
        params = {'include_all_efforts': False}
        resp = requests.get(f'{BASE_URL}/activities/{activity_id}', headers=headers, params=params)
        respData = resp.json()
        gearDeets = respData['gear']
        print(f'hello? {gearDeets}')
        if respData['gear']['primary'] == True: 
            print("you used your primary gear! no email needed :)")
        else:
            print("this should fire an email to check your gear!")
            send_email(user_email, data)
        # else: 
        #     print("can't process activity without access token!")

def send_email(recipient_address, data):
    """Send email notification."""
    sport_type = data['sport_type']
    activity_date = datetime.fromisoformat(data['start_date_local']).date
    msg = Message(f'Check your gear on your {sport_type} on {activity_date}', sender = 'stravagearupdater@gmail.com', recipients = [recipient_address])
    msg.body = f"Hello athlete!<br> \
        You logged a {sport_type} on {activity_date} using your default gear, .<br> \
        If that's the gear you used, you can ignore this message! \
        Otherwise, this is your reminder to update your gear. \
        You can update your gear in Strava or use the buttons below."

    mail.send(msg)
    return "sent"

@app.route('/update-activity-gear', methods=['PUT']) 
@login_required
def update_activity_gear():
    """Update activity gear settings."""
    request.form.get(activity)

if __name__ == '__main__':
    connect_to_db(app)
    app.run('0.0.0.0', debug=True)
    app.app_context().push()