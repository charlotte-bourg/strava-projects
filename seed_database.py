"""Script to seed the database."""

import os
import json
from random import choice, randint
from datetime import datetime

import crud
from model import connect_to_db, db, ActivityType
import server

# Drop and recreate the database
os.system("dropdb gearupdaterdb")
os.system("createdb gearupdaterdb")

# Connect to the database and create tables
connect_to_db(server.app)
server.app.app_context().push()
db.create_all()

# Seed activity types into the database
activity_types = ["Run", "TrailRun", "Walk", "Hike", "VirtualRun"]

for activity_type in activity_types:
    db.session.add(ActivityType(name=activity_type))

db.session.commit()