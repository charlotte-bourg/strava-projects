"""Server for the running helper app."""

import requests
from flask import render_template, request, redirect, jsonify
from flask_login import current_user
import app.crud as crud
from app.model import db
from app.gear import gear_bp
from .. import tokens
from .. import constants
from . import helpers

@gear_bp.route('/webhook', methods=['POST'])
def webhook():
    # handle event
    # gather information required to process event 
    data = request.get_json()
    user = crud.get_user_by_strava_id(data['owner_id'])
    access_token_code = tokens.retrieve_valid_access_code(user.id)
    user_default_shoe = crud.get_user_default_shoe(user.id)
    user_default_shoe_strava_id = user_default_shoe.strava_gear_id
    user_default_shoe_name = user_default_shoe.name
    
    # process event asynchronously with celery task 
    helpers.process_new_event.delay(data, user.email, user_default_shoe_strava_id, user_default_shoe_name, access_token_code)

    # acknowledge new event with status code 200 (required within 2 seconds)
    return jsonify({"status": "success"})

@gear_bp.route('/gear-reminders')
def display_gear_reminders_home():
    return render_template('home.html')

# display and update gear defaults routes
@gear_bp.route('/update-gear')
def updateGear():
    """Display gear update page."""
    return render_template('update-gear.html')

@gear_bp.route('/retrieve-gear')
def retrieve_gear():
    """Retrieve gear data from Strava."""
    user = current_user
    access_token_code = tokens.retrieve_valid_access_code(user.id)

    # retrieve user's shoes from strava
    headers = {'Authorization': f'Bearer {access_token_code}'}
    athlete_details_response = requests.get(f'{constants.BASE_URL}/athlete', headers=headers)
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

@gear_bp.route('/set-default-run-gear', methods=['POST'])
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