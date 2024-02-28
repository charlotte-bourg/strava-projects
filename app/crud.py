"""CRUD operations for interacting with the database."""

from app import db
from app.model import User, AccessToken, RefreshToken, Shoe
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

def get_user_by_id(user_id):
    """Retrieve a user by user ID."""
    return User.query.get(user_id)

def get_user_by_email(email):
    """Retrieve a user by email."""
    return User.query.filter(User.email == email).first()

def create_shoe(strava_id, name, nickname, retired, user_id):
    """Create a shoe instance."""
    shoe = Shoe(strava_gear_id=strava_id, name=name, nickname=nickname, retired=retired, user_id=user_id, run_default=False)
    return shoe

def get_shoe_by_id(id):
    """Retrieve a shoe by internal ID."""
    return Shoe.query.get(id)

def get_shoe_by_strava_id(strava_id):
    """Retrieve a shoe by Strava ID."""
    return Shoe.query.filter_by(strava_gear_id=strava_id).first()

def get_user_default_shoe(user_id):
    """Retrieve a user's default shoe."""
    return Shoe.query.filter_by(user_id = user_id, run_default = True).first() 

def get_user_by_strava_id(strava_id):
    """Retrieve a user by Strava ID."""
    return User.query.filter_by(strava_id=strava_id).first()

def create_user(strava_id):
    """Create a new user."""
    user = User(strava_id=strava_id)
    return user

def set_password(user, password):
    """Set the password for a user."""
    user.password_hash = generate_password_hash(password)

def check_password(user, password):
    """Check if the provided password matches the user's password."""
    return check_password_hash(user.password_hash, password)

def create_access_token(code, scope_activity_read_all, scope_profile_read_all, expires_at, user_id):
    """Create an access token."""
    access_token = AccessToken(code=code, scope_activity_read_all=scope_activity_read_all,
                               scope_profile_read_all=scope_profile_read_all, expires_at=expires_at, user_id=user_id)
    return access_token

def create_refresh_token(code, scope_activity_read_all, scope_profile_read_all, user_id):
    """Create a refresh token."""
    refresh_token = RefreshToken(code=code, scope_activity_read_all=scope_activity_read_all,
                                 scope_profile_read_all=scope_profile_read_all, user_id=user_id)
    return refresh_token

def strava_authenticated(user_id):
    """Check if the user is authenticated with Strava."""
    return bool(AccessToken.query.filter_by(user_id=user_id).first())

def user_has_active_access_token(user_id):
    """Check if the user has an active access token."""
    token = get_access_token(user_id)
    return token.expires_at > datetime.now() + timedelta(minutes=5)

def get_access_token(user_id):
    """Retrieve the access token for a user."""
    return AccessToken.query.filter_by(user_id=user_id).one()

def get_refresh_token(user_id):
    """Retrieve the refresh token for a user."""
    return RefreshToken.query.filter_by(user_id=user_id).one()

# if __name__ == '__main__':
#     from server import app
#     connect_to_db(app)
#     app.app_context().push()