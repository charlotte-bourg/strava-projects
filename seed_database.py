"""Script to seed database."""

import os
import json
from random import choice, randint
from datetime import datetime

import crud
from model import connect_to_db, db, ActivityType
import server

os.system("dropdb gearupdaterdb")
os.system("createdb gearupdaterdb")

connect_to_db(server.app)
server.app.app_context().push()
db.create_all()

db.session.add_all([ActivityType(name="Run"), ActivityType(name="Trail Run"), ActivityType(name="Walk"), ActivityType(name="Hike"), ActivityType(name="Virtual Run")])
db.session.commit()