from app import app, db
from models import GeneratedStory

with app.app_context():
    db.create_all()
    print("Table generated_stories created successfully.")
