"""Script to seed database."""

import os
import json
from random import choice, randint
from datetime import datetime

import crud
import model
import server

os.system("dropdb gearupdaterdb")
os.system("createdb gearupdaterdb")

model.connect_to_db(server.app)
server.app.app_context().push()
model.db.create_all()