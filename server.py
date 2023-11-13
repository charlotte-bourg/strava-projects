"""Server for running helper app."""
import os 
import requests
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = os.environ['FLASK_KEY']

CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']
REDIRECT_URI = os.environ['REDIRECT_URI']

AUTHORIZE_URL = 'https://www.strava.com/oauth/authorize'
TOKEN_URL = 'https://www.strava.com/api/v3/oauth/token'
DEAUTHORIZE_URL = 'https://www.strava.com/oauth/deauthorize'

SCOPES = 'read'

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

if __name__ == '__main__':
    # connect_to_db(app)
    app.run('0.0.0.0', debug=True)