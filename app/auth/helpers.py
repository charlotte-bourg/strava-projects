import os
import requests
from app import crud
from app import db 
from datetime import datetime, timedelta

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