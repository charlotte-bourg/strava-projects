"""Server for running helper app."""
import os 
import requests
from flask import Flask, render_template, request, redirect, session, jsonify 
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = os.environ['FLASK_KEY']

CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']
REDIRECT_URI = os.environ['REDIRECT_URI']
STRAVA_VERIFY_TOKEN = os.environ['STRAVA_VERIFY_TOKEN']

AUTHORIZE_URL = 'https://www.strava.com/oauth/authorize'
TOKEN_URL = 'https://www.strava.com/api/v3/oauth/token'
DEAUTHORIZE_URL = 'https://www.strava.com/oauth/deauthorize'

SCOPES = 'read'


app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'stravagearupdater@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ['EMAIL_PASS']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

@app.route('/test-email')
def test_email():
    msg = Message('Hello from strava gear updater', sender = 'stravagearupdater@gmail.com', recipients = ['charlotte.bourg@gmail.com'])
    msg.body = "testing from flask-mail"
    mail.send(msg)
    return "sent"

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
    token_data = response.json()
    print(token_data)
    # Store the tokens in the session (in a production environment, use a secure storage)
    # session['access_token'] = token_data['access_token']
    # session['refresh_token'] = token_data['refresh_token']

    return f'Authentication successful! Welcome {token_data["athlete"]["firstname"]}!'

@app.route('/update-gear/create-webhook')
def create_webhook():
    webhook_data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'callback_url': 'https://c2d6-23-118-109-73.ngrok.io/webhook',
        'verify_token': STRAVA_VERIFY_TOKEN
    }

    response = requests.post('https://www.strava.com/api/v3/push_subscriptions', data=webhook_data)
    subscription_data = response.json()

    print(subscription_data)

    return f'Webhook subscription created?'

@app.route('/webhook', methods=['GET', 'POST'])
def strava_webhook():
    print("*****HEYHELLOHI*****")
    if request.method == 'GET':
        hub_challenge = request.args.get('hub.challenge','')
        hub_verify_token = request.args.get('hub.verify_token', '')
        print("hello")
        if hub_verify_token == STRAVA_VERIFY_TOKEN:
            return jsonify({'hub.challenge': hub_challenge})
        else:
            return 'Invalid verify token', 403
    else:
        data = request.json
        if data.get('hub.verify_token') == STRAVA_VERIFY_TOKEN:
            return jsonify({'hub.challege': data.get('hub.challenge')})
        else:
            return 'Invalid verify token', 403

if __name__ == '__main__':
    # connect_to_db(app)
    app.run('0.0.0.0', debug=True)