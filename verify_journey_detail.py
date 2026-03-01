from app import app, db, User, MyJourney, MyJourneyDay
from datetime import datetime

def verify_detail_page():
    with app.test_client() as client:
        with app.app_context():
            # Setup User and Project
            user = User.query.filter_by(name="DetailVerifier").first() or User(name="DetailVerifier", email="detail@verify.com", password="pw")
            db.session.add(user)
            db.session.commit()
            
            project = MyJourney(
                project_name="DetailProject",
                project_date_time=datetime.now(),
                project_description="Test Desc",
                members=user.name,
                admin_name=user.name
            )
            db.session.add(project)
            db.session.commit()
            
            # Add a day entry
            day = MyJourneyDay(
                my_journey_id=project.id,
                journey_date=datetime.now().date(),
                member_name=user.name,
                description="Test Day Description"
            )
            db.session.add(day)
            db.session.commit()
            
            # Login
            with client.session_transaction() as sess:
                sess['user_id'] = user.id
                sess['user_name'] = user.name
                
            print(f"Accessing /journey/{project.id}...")
            resp = client.get(f'/journey/{project.id}')
            
            if resp.status_code == 200:
                print("SUCCESS: Page loaded successfully (200 OK).")
                if b'Test Day Description' in resp.data:
                     print("SUCCESS: Day description found.")
                else:
                     print("FAILURE: Day description missing.")
                     
                if b'Admin</span>' in resp.data:
                    print("SUCCESS: Admin badge found.")
                else:
                    print("FAILURE: Admin badge missing.")
            else:
                print(f"FAILURE: Page load failed with status {resp.status_code}")
                # print(resp.data) # Uncomment if debugging needed

            # Cleanup
            db.session.delete(day)
            db.session.delete(project)
            db.session.commit()

if __name__ == "__main__":
    verify_detail_page()
