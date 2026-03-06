from app import app, db
from models import MyJourney, Project

with app.app_context():
    print('Project 1:', Project.query.get(1))
    print('MyJourney 1:', MyJourney.query.get(1))
