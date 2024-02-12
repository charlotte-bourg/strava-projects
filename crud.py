"""CRUD operations for interacting with the database."""

from model import db, User, AccessToken, RefreshToken, Shoe, ActivityType, DefaultShoe, connect_to_db
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
    shoe = Shoe(strava_gear_id=strava_id, name=name, nickname=nickname, retired=retired, user_id=user_id)
    return shoe

def get_shoe_by_strava_id(strava_id):
    """Retrieve a shoe by Strava ID."""
    return Shoe.query.filter_by(strava_gear_id=strava_id).first()

def create_default_association(shoe_id, activity_name, user_id):
    """Create a default association between a shoe and an activity type."""
    activity_type_id = ActivityType.query.filter_by(name = activity_name).first().id
    default_shoe = DefaultShoe(shoe_id = shoe_id, activity_type_id = activity_type_id, user_id = user_id)
    return default_shoe

def get_defaults_for_user(user_id):
    """Get any default associations for the user."""
    return DefaultShoe.query.filter_by(user_id = user_id).all()

# TODO
def user_has_default_for_activity():
    """Check if a user has a default activity."""
    pass

# TODO
def get_user_default_for_activity():
    """Retrieve the default activity for a user."""
    pass

def get_user_by_strava_id(strava_id):
    """Retrieve a user by Strava ID."""
    return User.query.filter_by(strava_id=strava_id).first()

def get_activity_type_by_name(name):
    """Retrieve an activity type by name."""
    return ActivityType.query.filter_by(name=name).first()

def create_user(email, password):
    """Create a new user."""
    user = User(email=email, password=password)
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

if __name__ == '__main__':
    from server import app
    connect_to_db(app)
    app.app_context().push()