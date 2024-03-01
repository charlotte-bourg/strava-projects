"""Script for setup and maintenance of Strava webhook"""

import requests 
from app import constants

def create_webhook_subscription():
    """Create a new webhook subscription"""
    webhook_data = {
        'client_id': constants.CLIENT_ID,
        'client_secret': constants.CLIENT_SECRET,
        'callback_url': constants.CALLBACK_URL,
        'verify_token': constants.STRAVA_VERIFY_TOKEN
    }

    response = requests.post(f'{constants.BASE_URL}/push_subscriptions', data=webhook_data)
    subscription_data = response.json()
    print(subscription_data)

def view_webhook_subscription():
    """View the details of a webhook subscription"""
    params = {
        'client_id': constants.CLIENT_ID,
        'client_secret': constants.CLIENT_SECRET,
    }

    response = requests.get(f'{constants.BASE_URL}/push_subscriptions/', params=params)
    subscription_data = response.json()

    print(subscription_data)

def delete_webhook_subscription():
    """Delete a webhook subscription"""
    subscription_id = input('Enter the subscription ID to delete (run view_webhook_subscription() to check as needed!): ')

    url = f"{constants.BASE_URL}/push_subscriptions/{subscription_id}"
    params = {
        "client_id": constants.CLIENT_ID,
        "client_secret": constants.CLIENT_SECRET
    }

    response = requests.delete(url, params=params)
    print(response)
   