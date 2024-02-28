import os
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    print(app.config)
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    return app