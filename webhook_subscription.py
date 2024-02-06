"""Script for setup and maintenance of Strava webhook"""

import os 
import requests 
from flask import Flask, request, jsonify 

app = Flask(__name__)
app.secret_key = os.environ['FLASK_KEY']

CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']
REDIRECT_URI = os.environ['REDIRECT_URI']
CALLBACK_URL = os.environ['CALLBACK_URL']
STRAVA_VERIFY_TOKEN = os.environ['STRAVA_VERIFY_TOKEN']

BASE_URL = 'https://www.strava.com/api/v3'

def create_webhook_subscription():
    """Create a new webhook subscription"""
    webhook_data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'callback_url': CALLBACK_URL,
        'verify_token': STRAVA_VERIFY_TOKEN
    }

    response = requests.post(f'{BASE_URL}/push_subscriptions', data=webhook_data)
    subscription_data = response.json()
    print(subscription_data)

@app.route('/webhook', methods=['GET'])
def webhook():
    hub_challenge = request.args.get('hub.challenge', '')
    hub_verify_token = request.args.get('hub.verify_token', '')
    if hub_verify_token == STRAVA_VERIFY_TOKEN:
        return jsonify({'hub.challenge': hub_challenge})
    elif hub_verify_token:
        return 'Invalid verify token', 403

def view_webhook_subscription():
    """View the details of a webhook subscription"""
    params = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }

    response = requests.get(f'{BASE_URL}/push_subscriptions/', params=params)
    subscription_data = response.json()

    print(subscription_data)

def delete_webhook_subscription():
    """Delete a webhook subscription"""
    subscription_id = input('Enter the subscription ID to delete (run view_webhook_subscription() to check as needed!): ')

    url = f"https://www.strava.com/api/v3/push_subscriptions/{subscription_id}"
    params = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    response = requests.delete(url, params=params)
    print(response)