from app import app, db, User, MyJourney, MyJourneyRequest
from flask import session

def verify_collab_flow():
    with app.test_client() as client:
        with app.app_context():
            # Setup
            admin_user = User.query.filter_by(name="AdminUser").first() or User(name="AdminUser", email="admin@test.com", password="pw")
            target_user = User.query.filter_by(name="TargetUser").first() or User(name="TargetUser", email="target@test.com", password="pw")
            
            db.session.add(admin_user)
            db.session.add(target_user)
            db.session.commit()
            
            # Target User creates a project (MyJourney)
            from datetime import datetime
            project = MyJourney(
                project_name="TargetProject",
                project_date_time=datetime.now(),
                project_description="Test Description",
                members=target_user.name,
                admin_name=target_user.name
            )
            db.session.add(project)
            db.session.commit()
            
            print(f"Project created by {target_user.name} (ID: {project.id})")
            
            # Admin User logs in and requests to join
            with client.session_transaction() as sess:
                sess['user_id'] = admin_user.id
                sess['user_name'] = admin_user.name
                
            print(f"Admin {admin_user.name} requesting to join project {project.id}...")
            # Simulate clicking "Request" on Home (which uses request_join_project route)
            resp = client.post(f'/project/request/{project.id}')
            print(f"Request Response: {resp.get_json()}")
            
            # Verify Request created
            req = MyJourneyRequest.query.filter_by(my_journey_id=project.id, user_id=admin_user.id, status='pending').first()
            if req:
                print("SUCCESS: Pending request found in DB.")
            else:
                print("FAILURE: No pending request found.")
                return

            # Target User logs in to accept
            with client.session_transaction() as sess:
                sess['user_id'] = target_user.id
                sess['user_name'] = target_user.name
                
            print(f"Target User {target_user.name} accepting request...")
            # Simulate clicking Accept on Pending page
            resp = client.post(f'/accept_request/{req.id}')
            print(f"Accept Response: {resp.get_json()}")
            
            # Verify Membership
            updated_project = MyJourney.query.get(project.id)
            print(f"Project Members: {updated_project.members}")
            
            if admin_user.name in updated_project.members:
                print("SUCCESS: Admin added to members.")
            else:
                print("FAILURE: Admin not in members.")

            # Admin User logs in to check My Collabs
            with client.session_transaction() as sess:
                sess['user_id'] = admin_user.id
                sess['user_name'] = admin_user.name
                
            print(f"Admin checking My Collabs...")
            resp = client.get('/my_collabs')
            if b'TargetProject' in resp.data:
                print("SUCCESS: Project found in Admin's My Collabs.")
            else:
                print("FAILURE: Project NOT found in Admin's My Collabs.")

            # Cleanup
            db.session.delete(req)
            db.session.delete(updated_project)
            db.session.commit()

if __name__ == "__main__":
    verify_collab_flow()
