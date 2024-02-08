"""Create, read, update, delete operations"""
from model import db, User, AccessToken, RefreshToken, Shoe, connect_to_db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

def get_user_by_id(id):
    """Retrieve user by id."""
    return User.query.get(id)

def get_user_by_email(email):
    """Retrieve user by email."""
    return User.query.filter(User.email == email).first()

def create_shoe(strava_id, name, nickname, retired, user_id):
    shoe = Shoe(strava_gear_id = strava_id, name = name, nickname = nickname, retired = retired, user_id = user_id)
    return shoe 

def create_user(email, password):
    user = User(email, password)
    return user 

def set_password(user, password):
    user.password_hash = generate_password_hash(password)

def check_password(user, password):
    return check_password_hash(user.password_hash, password)

def create_access_token(code, scope_activity_read_all, scope_profile_read_all, expires_at, user_id):
    access_token = AccessToken(code = code, scope_activity_read_all = scope_activity_read_all, scope_profile_read_all = scope_profile_read_all, expires_at = expires_at, user_id = user_id) 
    return access_token 

def create_refresh_token(code, scope_activity_read_all, scope_profile_read_all, user_id):
    refresh_token = RefreshToken(code = code, scope_activity_read_all = scope_activity_read_all, scope_profile_read_all = scope_profile_read_all, user_id = user_id) 
    return refresh_token

def strava_authenticated(user_id):
    if AccessToken.query.filter_by(user_id = user_id).first():
        return True
    else: 
        return False

def user_has_active_access_token(user_id):
    token = get_access_token(user_id)
    return token.expires_at > datetime.now() - timedelta(minutes = 5)

def get_access_token(user_id):
    return AccessToken.query.filter_by(user_id = user_id).one()

def get_refresh_token(user_id):
    return RefreshToken.query.filter_by(user_id = user_id).one()

if __name__ == '__main__':
    from server import app
    connect_to_db(app)
    app.app_context().push()