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

# Strava endpoints 
BASE_URL = 'https://www.strava.com/api/v3'
AUTHORIZE_URL = 'https://www.strava.com/oauth/authorize'
TOKEN_URL = 'https://www.strava.com/api/v3/oauth/token'
DEAUTHORIZE_URL = 'https://www.strava.com/oauth/deauthorize'

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

        return f'Authentication successful! Welcome {token_data["athlete"]["firstname"]}!'

    return 'Authentication failed.'

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        hub_challenge = request.args.get('hub.challenge', '')
        hub_verify_token = request.args.get('hub.verify_token', '')
        if hub_verify_token == STRAVA_VERIFY_TOKEN:
            return jsonify({'hub.challenge': hub_challenge})
        elif hub_verify_token:
            return 'Invalid verify token', 403
        data = request.args.get('object_type', '')
        print(data)
        return "hello."
    elif request.method == 'POST':
        data = request.get_json()
        print(data)
        print("this is where'd we'd fire off async work to send an email!")
        return jsonify({"status": "success"}), 200
    return 'Invalid request'

# @app.route('/test-process-new')
# def process_new_activity_test():
#     # should receive new activity ID
#     # get details of activity
#     activity_id = 10236610394
#     process_new_activity(activity_id)
#     return "nice"
    
# def process_new_activity(activity_id):
#     if 'access_token' in session:
#         access_token = session['access_token']
#     else:
#         pass # add error handling
#     headers = {'Authorization': f'Bearer {access_token}'}
#     params = {'include_all_efforts': False}
#     resp = requests.get(f'{BASE_URL}/activities/{activity_id}', headers=headers, params=params)
#     respData = resp.json()
#     # get athlete's default gear at time of activity
#     print(respData)
#     if 'gear' not in respData:
#         pass #error
#     else:
#         if respData['gear']['primary'] == True:
#             test_email()
#     return 1 
    
# @app.route('/test-email')
# def test_email():
#     msg = Message('Hello from strava gear updater', sender = 'stravagearupdater@gmail.com', recipients = ['charlotte.bourg@gmail.com'])
#     msg.body = "testing from flask-mail"
#     mail.send(msg)
#     return "sent"


# @app.route('/update-gear/create-webhook')
# def create_webhook():
#     webhook_data = {
#         'client_id': CLIENT_ID,
#         'client_secret': CLIENT_SECRET,
#         'callback_url': 'https://ea7d-23-118-109-73.ngrok.io/webhook',
#         'verify_token': STRAVA_VERIFY_TOKEN
#     }

#     response = requests.post('{BASE_URL}/push_subscriptions', data=webhook_data)
#     subscription_data = response.json()

#     print("HEY YOUR SUBSCRIPTION DATA IS HERE")
#     print(subscription_data)
#     session['subscription_id'] = subscription_data.get('id', '')
#     return f'Webhook subscription created?'

# @app.route('/update-gear/view-webhook')
# def view_webhook():
#     # View details of the webhook subscription
#     subscription_id = 252249

#     params = {
#         'client_id': CLIENT_ID,
#         'client_secret': CLIENT_SECRET,
#     }

#     response = requests.get(f'{BASE_URL}/push_subscriptions/', params=params)
#     subscription_data = response.json()

#     return jsonify(subscription_data)



if __name__ == '__main__':
    # connect_to_db(app)
    app.run('0.0.0.0', debug=True)