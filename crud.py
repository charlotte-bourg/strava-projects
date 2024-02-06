"""Create, read, update, delete operations"""
from model import db, User, connect_to_db
from werkzeug.security import generate_password_hash, check_password_hash

def get_user_by_id(id):
    """Retrieve user by id."""
    return User.query.get(id)

def get_user_by_email(email):
    """Retrieve user by email."""
    return User.query.filter(User.email == email).first()

def create_user(email, password):
    user = User(email, password)
    return user 

def set_password(user, password):
    user.password_hash = generate_password_hash(password)

def check_password(user, password):
    return check_password_hash(user.password_hash, password)

if __name__ == '__main__':
    from server import app
    connect_to_db(app)
    app.app_context().push()