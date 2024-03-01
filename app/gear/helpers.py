import requests
from flask_mail import Message
from datetime import datetime
from .. import constants
from . import celery, mail 

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
    activity_details_response = requests.get(f'{constants.BASE_URL}/activities/{activity_id}', headers=headers, params=params)

    # parse gear and sport type 
    activity_details_data = activity_details_response.json()
    strava_gear_id = activity_details_data['gear_id']
    sport_type = activity_details_data['sport_type']

    # check if activity type is out of scope for gear checker (only activity types that can have a default shoe are in scope)
    if sport_type not in constants.SHOE_ACTIVITIES: 
        return

    # check if gear used is the default for the sport per user settings in app 
    if strava_gear_id == user_default_shoe_strava_id:
        sport_type_user_friendly = constants.USER_FRIENDLY_SPORT_NAMES[sport_type]
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