from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from config import Config
from celery import Celery
import logging

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    celery.conf.update(app.config)
    celery.log.setup(loglevel=logging.DEBUG)

    # Celery setup
    # def celery_init_app(app: Flask) -> Celery: 
    #     class FlaskTask(Task):
    #         def __call__(self, *args: object, **kwargs: object) -> object:
    #             with app.app_context():
    #                 return self.run(*args, **kwargs)

    #     celery_app = Celery(app.name, task_cls=FlaskTask)
    #     celery_app.config_from_object(app.config["CELERY"])
    #     celery_app.set_default()
    #     app.extensions["celery"] = celery_app
    #     return celery_app

    # app.config.from_mapping(
    #     CELERY=dict(
    #         broker_url="redis://localhost",
    #         result_backend="redis://localhost"
    #     ),
    # )

    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.gear import gear_bp
    app.register_blueprint(gear_bp)

    return app