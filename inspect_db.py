import sys
from app import app, db, MyJourney, MyJourneyRequest, User

def inspect():
    with app.app_context():
        # User is likely not removed correctly from the requests table previously
        # Let's check 'air piano'
        project = MyJourney.query.filter_by(project_name="air piano").first()
        if not project:
            print("Project 'air piano' not found")
            return
            
        print(f"Project: {project.project_name}, ID: {project.id}, Admin: {project.admin_name}")
        print(f"Members: {project.members}")
        
        requests = MyJourneyRequest.query.filter_by(my_journey_id=project.id).all()
        for req in requests:
            u = User.query.get(req.user_id)
            print(f"Request User: {u.name}, Status: {req.status}")

if __name__ == "__main__":
    inspect()
