from app import app, db
from models import Project
from datetime import datetime

def seed_data():
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Check if projects already exist
        if Project.query.first():
            print("Projects already exist. Skipping seed.")
            return

        projects = [
            Project(
                username="Alice",
                date_and_time=datetime(2025, 12, 20, 10, 30),
                project_description="AI-powered efficient Personal Assistant",
                likes=120,
                comments=45,
                members="Alice, Bob, Charlie"
            ),
            Project(
                username="Raman",
                date_and_time=datetime(2025, 12, 22, 14, 15),
                project_description="JourneyVerse - A futuristic social platform",
                likes=250,
                comments=89,
                members="Raman, Team"
            ),
            Project(
                username="JohnDoe",
                date_and_time=datetime(2025, 12, 24, 9, 0),
                project_description="E-commerce Website Redesign",
                likes=85,
                comments=12,
                members="John, Design Team"
            )
        ]

        db.session.add_all(projects)
        db.session.commit()
        print("Sample projects added successfully!")

if __name__ == "__main__":
    seed_data()
