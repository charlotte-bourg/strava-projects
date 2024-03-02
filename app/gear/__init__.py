from flask import Blueprint

gear_bp = Blueprint('gear', __name__)

from . import routes