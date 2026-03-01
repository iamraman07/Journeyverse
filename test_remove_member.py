import sys
import os
from app import app, db, User, MyJourney, MyJourneyRequest, Notification

def test_member_removal():
    with app.app_context():
        # Setup test data
        admin = User.query.filter_by(name="TestAdmin").first()
        if not admin:
            admin = User(name="TestAdmin", email="admin@test.com", password="pwd")
            db.session.add(admin)
            
        member = User.query.filter_by(name="TestMember").first()
        if not member:
            member = User(name="TestMember", email="member@test.com", password="pwd")
            db.session.add(member)
            
        db.session.commit()
        
        project = MyJourney.query.filter_by(project_name="TestProject").first()
        if not project:
            from datetime import datetime
            project = MyJourney(
                project_name="TestProject",
                project_date_time=datetime.now(),
                project_description="Test Description",
                admin_name=admin.name,
                members="TestMember,OtherMember"
            )
            db.session.add(project)
            db.session.commit()
            
        # Add a mock request
        req = MyJourneyRequest.query.filter_by(my_journey_id=project.id, user_id=member.id).first()
        if not req:
            req = MyJourneyRequest(my_journey_id=project.id, user_id=member.id, status='accepted')
            db.session.add(req)
            db.session.commit()

        print(f"Before removal: Project members = {project.members}")
        print(f"Request exists: {MyJourneyRequest.query.filter_by(my_journey_id=project.id, user_id=member.id).first() is not None}")
        
    # Simulate the request
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = admin.id
            sess['user_name'] = admin.name
            
        response = client.post(f'/remove_member/{project.id}', json={'member_name': 'TestMember'})
        print(f"Response: {response.json}")
        
    with app.app_context():
        project_after = MyJourney.query.get(project.id)
        print(f"After removal: Project members = {project_after.members}")
        req_after = MyJourneyRequest.query.filter_by(my_journey_id=project.id, user_id=member.id).first()
        print(f"Request removed: {req_after is None}")
        
        notifs = Notification.query.filter_by(recipient_id=member.id).all()
        print(f"Notifications: {[n.message for n in notifs]}")
        
        # Cleanup
        db.session.delete(project_after)
        for n in notifs: db.session.delete(n)
        db.session.delete(admin)
        db.session.delete(member)
        db.session.commit()
        print("Cleanup done.")

if __name__ == "__main__":
    test_member_removal()
