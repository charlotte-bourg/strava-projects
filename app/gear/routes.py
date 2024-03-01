"""Server for the running helper app."""

import os
import requests
from flask import Flask, flash, render_template, request, redirect, jsonify, Blueprint
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from celery import Celery, Task
import logging
import app.crud as crud
from app.model import db
from datetime import datetime, timedelta

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

# Flask-Mail configuration

mail = Mail(app)

SHOE_ACTIVITIES = {'Run', 'VirtualRun', 'TrailRun', 'Hike', 'Walk'}
THIRD_PARTY_ACTIVITIES = {'EBikeRide', 'Ride', 'Run', 'Swim', 'VirtualRide', 'VirtualRun'}
# All activities reference: AlpineSki, BackcountrySki, Canoeing, Crossfit, EBikeRide, Elliptical, Golf, Handcycle, Hike, IceSkate, InlineSkate, Kayaking, Kitesurf, NordicSki, Ride, RockClimbing, RollerSki, Rowing, Run, Sail, Skateboard, Snowboard, Snowshoe, Soccer, StairStepper, StandUpPaddling, Surfing, Swim, Velomobile, VirtualRide, VirtualRun, Walk, WeightTraining, Wheelchair, Windsurf, Workout, Yoga
# TODO consider capitalization for use cases
USER_FRIENDLY_SPORT_NAMES = {'Run': 'run', 'VirtualRun': 'virtual run', 'TrailRun': 'trail run', 'Hike': 'hike', 'Walk': 'walk'}
#USER_FRIENDLY_SPORT_NAMES = {'Run': 'run', 'VirtualRun': 'virtual run', 'TrailRun': 'trail run', 'Hike': 'hike', 'Walk': 'walk', 'EBikeRide': 'E Bike Ride'}

@app.route('/gear-reminders')
def display_gear_reminders_home():
    return render_template('home.html')

# display and update gear defaults routes
@app.route('/update-gear')
def updateGear():
    """Display gear update page."""
    return render_template('update-gear.html')

@app.route('/retrieve-gear')
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
    return render_template('set-default-gear.html', default_shoe = default_shoe, shoes = active_shoes)

@app.route('/set-default-run-gear', methods=['POST'])
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