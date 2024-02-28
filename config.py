import os

class Config:
    SECRET_KEY = os.environ.get('FLASK_KEY')
    SQLALCHEMY_DATABASE_URI = 'postgresql:///gearupdaterdb'
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USERNAME = os.environ['SENDING_ADDRESS']
    MAIL_PASSWORD = os.environ['EMAIL_PASS']
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True