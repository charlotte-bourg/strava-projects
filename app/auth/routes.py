import os
import requests
from flask import flash, render_template, request, redirect, jsonify
from flask_login import login_user, logout_user, login_required
from app import crud
from app.auth import auth_bp
from app import db 
from datetime import datetime, timedelta
from app import login_manager
from . import helpers
from . import constants

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login."""
    return crud.get_user_by_id(user_id)

@auth_bp.route('/')
def login_entry():
    """Display login page."""
    return render_template('log-in.html')

@auth_bp.route('/log-out')
def logout():
    """Handle user logout."""
    logout_user()
    flash("Logged out!")
    return redirect('/')

@auth_bp.route('/home')
@login_required
def logged_in_home(): 
    """Display home page for logged-in user."""
    return render_template('home.html')
 
@auth_bp.route('/strava-auth')
def authenticate():
    """Redirect to Strava authentication."""
    return redirect(f'{AUTHORIZE_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope={SCOPES}')

@auth_bp.route('/callback')
def callback():
    """Handle callback from Strava after authentication."""
    err = request.args.get('error', '')
    if err: 
        flash("Can't set up gear updater without your Strava authentication")
        return redirect('/strava-auth')
    
    # Handle the callback from Strava after user authorization
    code = request.args.get('code')
    scopes = request.args.get('scope')
    scope_activity_read_all = "activity:read_all" in scopes
    scope_profile_read_all = "profile:read_all" in scopes

    # Exchange the authorization code for access and refresh tokens
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code, # obtained from redirect 
        'grant_type': 'authorization_code', # always 'authorization_code' for initial authentication
    }
    
    token_response = requests.post(TOKEN_URL, data=data)

    if token_response.status_code == 200:
        token_data = token_response.json()
        strava_id = token_data['athlete']['id']
        user = crud.get_user_by_strava_id(strava_id)
        if not user: 
            user = crud.create_user(strava_id)
            db.session.add(user)
            db.session.commit() 
            expiration_offset = token_data['expires_in']
            expires_at = datetime.now() + timedelta(seconds = expiration_offset)
            access_token = crud.create_access_token(token_data['access_token'], scope_activity_read_all, scope_profile_read_all, expires_at, user.id)
            refresh_token = crud.create_refresh_token(token_data['refresh_token'], scope_activity_read_all, scope_profile_read_all, user.id)
            db.session.add_all([access_token, refresh_token])
            db.session.commit()

        login_user(user)

        return redirect('/home')
    
    return 'Authentication failed.'

@auth_bp.route('/webhook', methods=['GET','POST'])
def webhook():
    """Handle Strava webhook.""" 
    # handle webhook subscription validation request 
    if request.method == 'GET': 
        hub_challenge = request.args.get('hub.challenge', '')
        hub_verify_token = request.args.get('hub.verify_token', '')
        if hub_verify_token == STRAVA_VERIFY_TOKEN:
            return jsonify({'hub.challenge': hub_challenge})
        elif hub_verify_token:
            return 'Invalid verify token', 403
        else:
            return 'Invalid request'
    # handle event 
    elif request.method == 'POST':
        # gather information required to process event 
        data = request.get_json()
        user = crud.get_user_by_strava_id(data['owner_id'])
        access_token_code = helpers.retrieve_valid_access_code(user.id)
        user_default_shoe = crud.get_user_default_shoe(user.id)
        user_default_shoe_strava_id = user_default_shoe.strava_gear_id
        user_default_shoe_name = user_default_shoe.name
        
        # process event asynchronously with celery task 
        process_new_event.delay(data, user.email, user_default_shoe_strava_id, user_default_shoe_name, access_token_code)

        # acknowledge new event with status code 200 (required within 2 seconds)
        return jsonify({"status": "success"})
    else:
        return "Invalid request"