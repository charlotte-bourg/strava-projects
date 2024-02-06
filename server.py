"""Server for running helper app."""

import os 
import requests
from flask import Flask, render_template, request, redirect, session, jsonify 
from flask_mail import Mail, Message
from celery import Celery, Task
import logging 

app = Flask(__name__)
app.secret_key = os.environ['FLASK_KEY']

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
SCOPES = 'read_all,activity:read_all'

# flask-mail configuration
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'stravagearupdater@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ['EMAIL_PASS']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

# TODO replace with DB
users = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/update-gear')
def updateGear():
    return render_template('update-gear.html')

@app.route('/update-gear/login')
def authenticate():
    return redirect(f'{AUTHORIZE_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope={SCOPES}')

@app.route('/update-gear/callback')
def callback():
    # Handle the callback from Strava after user authorization
    code = request.args.get('code')

    # Exchange the authorization code for access and refresh tokens
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
    }
    
    response = requests.post(TOKEN_URL, data=data)

    if response.status_code == 200:
        token_data = response.json()
        # TODO move to db
        session['access_token'] = token_data['access_token']
        session['refresh_token'] = token_data['refresh_token']
        print('your session data is as follows')
        print(session)
        return f'Authentication successful! Welcome {token_data["athlete"]["firstname"]}!'

    return 'Authentication failed.'

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    process_new_activity.delay(data)
    return jsonify({"status": "success"}), 200

@celery.task
def process_new_activity(data):
    activity_id = data['object_id']
    print(f'hey! thanks for telling me to process activity {activity_id}')
    # if 'access_token' in session:
    #   access_token = session['access_token']
    access_token = 'f16e2ceb5a6b2f9f62d18e9773f7439031b5b58d'
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'include_all_efforts': False}
    print("what's happening")
    resp = requests.get(f'{BASE_URL}/activities/{activity_id}', headers=headers, params=params)
    respData = resp.json()
    gearDeets = respData['gear']
    print(f'hello? {gearDeets}')
    if respData['gear']['primary'] == True: 
        print("you used your primary gear! no email needed :)")
    else:
        print("this should fire an email to check your gear!")

def send_email():
    msg = Message('Hello from strava gear updater', sender = 'stravagearupdater@gmail.com', recipients = ['charlotte.bourg@gmail.com'])
    msg.body = "testing from flask-mail"
    mail.send(msg)
    return "sent"

if __name__ == '__main__':
    # connect_to_db(app)
    app.run('0.0.0.0', debug=True)