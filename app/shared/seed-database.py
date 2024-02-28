"""Script to seed the database."""

import os
from app import db 
from app.model import connect_to_db, db
import server

# Drop and recreate the database
os.system("dropdb gearupdaterdb")
os.system("createdb gearupdaterdb")

# Connect to the database and create tables
connect_to_db(server.app)
server.app.app_context().push()
db.create_all()

db.session.commit()