from app import app, db, User, MyJourney, MyJourneyRequest
import time

def verify_flow():
    with app.test_client() as client:
        with app.app_context():
            # Setup: Ensure we have a user and a journey
            admin = User.query.filter_by(name="AdminVerifier").first()
            if not admin:
                from flask_bcrypt import Bcrypt
                bcrypt = Bcrypt(app)
                admin = User(name="AdminVerifier", email="admin@verify.com", password=bcrypt.generate_password_hash("password").decode('utf-8'))
                db.session.add(admin)
                db.session.commit()
                
            requester = User.query.filter_by(name="Requester").first()
            if not requester:
                from flask_bcrypt import Bcrypt
                bcrypt = Bcrypt(app)
                requester = User(name="Requester", email="req@verify.com", password=bcrypt.generate_password_hash("password").decode('utf-8'))
                db.session.add(requester)
                db.session.commit()
                
            # Create a journey for Admin
            from datetime import datetime
            journey = MyJourney(
                project_name="Verify Project",
                project_date_time=datetime.now(),
                project_description="Test Project",
                members=admin.name,
                admin_name=admin.name
            )
            db.session.add(journey)
            db.session.commit()
            
            # Create a request
            req = MyJourneyRequest(my_journey_id=journey.id, user_id=requester.id, status='pending')
            db.session.add(req)
            db.session.commit()
            req_id = req.id
            
            print(f"Created request {req_id} for project {journey.id}")
            
            # Log in as Admin
            with client.session_transaction() as sess:
                sess['user_id'] = admin.id
                sess['user_name'] = admin.name
                
            # Test Accept
            print("Testing Accept...")
            response = client.post(f'/accept_request/{req_id}')
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.get_json()}")
            
            # Verify DB state
            updated_req = MyJourneyRequest.query.get(req_id)
            updated_journey = MyJourney.query.get(journey.id)
            
            print(f"Request Status: {updated_req.status}")
            print(f"Journey Members: {updated_journey.members}")
            
            if updated_req.status == 'accepted' and requester.name in updated_journey.members:
                print("SUCCESS: Request accepted and member added.")
            else:
                print("FAILURE: Accept logic failed.")

            # Test Decline (Create another request)
            req2 = MyJourneyRequest(my_journey_id=journey.id, user_id=requester.id, status='pending')
            db.session.add(req2)
            db.session.commit()
            req2_id = req2.id
            
            print("Testing Decline...")
            response = client.post(f'/decline_request/{req2_id}')
            updated_req2 = MyJourneyRequest.query.get(req2_id)
            
            print(f"Request 2 Status: {updated_req2.status}")
            
            if updated_req2.status == 'rejected':
                print("SUCCESS: Request rejected.")
            else:
                print("FAILURE: Decline logic failed.")
                
            # Cleanup
            db.session.delete(updated_req)
            db.session.delete(updated_req2)
            db.session.delete(updated_journey)
            db.session.commit() # Users kept for reuse or manual cleanup

if __name__ == "__main__":
    verify_flow()
