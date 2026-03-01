from app import app, db, MyCollab, User
from datetime import datetime

with app.app_context():
    # Get the first user to make them a collaborator
    user = User.query.first()
    
    if not user:
        print("No users found! Please signup/login first.")
    else:
        user_name = user.name
        print(f"Adding sample collaborations for user: {user_name} to MyCollab table")
        
        # Sample Project 1
        collab1 = MyCollab(
            project_name="Mars Base Alpha",
            project_date_time=datetime(2024, 5, 20, 10, 0),
            project_description="Establishing the first sustainable colony on Mars. A joint effort between multiple agencies.",
            likes=5400,
            comments=320,
            members=f"Elon, {user_name}, Sarah",
            admin_name="Elon"
        )
        
        # Sample Project 2
        collab2 = MyCollab(
            project_name="Ocean Cleanup Initiative",
            project_date_time=datetime(2023, 8, 15, 14, 30),
            project_description="Deploying System 003 to clean up the Great Pacific Garbage Patch.",
            likes=1200,
            comments=85,
            members=f"Boyan, {user_name}, Davin",
            admin_name="Boyan"
        )
        
        db.session.add(collab1)
        db.session.add(collab2)
        db.session.commit()
        
        print("Sample collaboration data added successfully into MyCollab table!")
