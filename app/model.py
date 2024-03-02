"""Models for the running-helper app."""

from flask_login import UserMixin
from datetime import datetime
from app import db 

class User(UserMixin, db.Model):
    """A user."""

    __tablename__ = "users"

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    strava_id = db.Column(db.Integer)
    email = db.Column(db.String, unique=True)
    password_hash = db.Column(db.String)
    created_on = db.Column(db.DateTime, nullable=False)
    email_consent = db.Column(db.Boolean)

    def __init__(self, strava_id):
        self.strava_id = strava_id 
        self.created_on = datetime.now()
        self.email_consent = False

    access_tokens = db.relationship("AccessToken", back_populates="user")
    refresh_tokens = db.relationship("RefreshToken", back_populates="user")
    shoes = db.relationship("Shoe", back_populates="user")

    def __repr__(self):
        return f'<User id={self.id} email={self.email}>'
class Shoe(db.Model):
    """A shoe from Strava gear."""

    __tablename__ = "shoes"

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    strava_gear_id = db.Column(db.String)
    name = db.Column(db.String)
    nickname = db.Column(db.String)
    retired = db.Column(db.Boolean)
    run_default = db.Column(db.Boolean)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    user = db.relationship("User", back_populates="shoes")

    def __repr__(self):
        return f'<Shoe id={self.id} name={self.name}>'

class AccessToken(db.Model):
    """A short-lived access token."""

    __tablename__ = "access_tokens"

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    code = db.Column(db.String)
    scope_activity_read_all = db.Column(db.Boolean)
    scope_profile_read_all = db.Column(db.Boolean)
    expires_at = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    user = db.relationship("User", back_populates="access_tokens")

    def __repr__(self):
        return f'<AccessToken id={self.id} code={self.code}>'

class RefreshToken(db.Model):
    """A refresh token."""

    __tablename__ = "refresh_tokens"

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    code = db.Column(db.String)
    scope_activity_read_all = db.Column(db.Boolean)
    scope_profile_read_all = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    user = db.relationship("User", back_populates="refresh_tokens")

    def __repr__(self):
        return f'<RefreshToken id={self.id} code={self.code}>'