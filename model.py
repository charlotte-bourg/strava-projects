"""Models for running-helper app."""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()    

class User(UserMixin, db.Model):
    """A user."""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, 
                        autoincrement = True,
                        primary_key = True)
    strava_athlete_id = db.Column(db.Integer)
    email = db.Column(db.String, unique = True)
    password_hash = db.Column(db.String, nullable=False)
    created_on = db.Column(db.DateTime, nullable=False)

    def __init__(self, email, password):
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.created_on = datetime.now()

    def __repr__(self):
        return f'<User user_id = {self.user_id} email = {self.email}>'
    
class AccessToken(db.Model):
    """A short-lived access token."""

    __tablename__ = "access_tokens"

    access_token_id = db.Column(db.Integer, 
                        autoincrement = True,
                        primary_key = True)
    code = db.Column(db.String)
    scope_activity_read_all = db.Column(db.Boolean)
    expires_at = db.Column(db.DateTime)
    athlete_id = db.Column(db.Integer, db.ForeignKey("user.strava_athlete_id"))

    def __repr__(self):
        return f'<AccessToken code = {self.code}>'

class RefreshToken(db.Model):
    """A refresh token."""

    __tablename__ = "refresh_tokens"

    refresh_token_id = db.Column(db.Integer, 
                        autoincrement = True,
                        primary_key = True)
    code = db.Column(db.String)
    scope_activity_read_all = db.Column(db.Boolean)
    athlete_id = db.Column(db.Integer, db.ForeignKey("user.strava_athlete_id"))

    def __repr__(self):
        return f'<RefreshToken code = {self.code}>'
    
def connect_to_db(flask_app, db_uri="postgresql:///gearupdaterdb", echo=True):
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    flask_app.config["SQLALCHEMY_ECHO"] = echo
    flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.app = flask_app
    db.init_app(flask_app)

    print("Connected to the db!")

if __name__ == "__main__":
    from server import app
    connect_to_db(app)
    app.app_context().push()