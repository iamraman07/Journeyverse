from app import app, db, User, MyJourney
from datetime import datetime

def verify_home_filtering():
    with app.test_client() as client:
        with app.app_context():
            # Setup
            me = User.query.filter_by(name="MeUser").first() or User(name="MeUser", email="me@test.com", password="pw")
            other = User.query.filter_by(name="OtherUser").first() or User(name="OtherUser", email="other@test.com", password="pw")
            db.session.add(me)
            db.session.add(other)
            db.session.commit()
            
            my_project = MyJourney(
                project_name="My Project",
                project_date_time=datetime.now(),
                project_description="My Desc",
                members=me.name,
                admin_name=me.name
            )
            other_project = MyJourney(
                project_name="Other Project",
                project_date_time=datetime.now(),
                project_description="Other Desc",
                members=other.name,
                admin_name=other.name
            )
            db.session.add(my_project)
            db.session.add(other_project)
            db.session.commit()
            
            # Login as Me
            with client.session_transaction() as sess:
                sess['user_id'] = me.id
                sess['user_name'] = me.name
                
            print(f"Me ({me.name}) checking Home page...")
            resp = client.get('/dashboard')
            content = resp.data.decode('utf-8')
            
            if 'Other Project' in content:
                print("SUCCESS: Other Project is visible.")
            else:
                print("FAILURE: Other Project is MISSING.")
                
            if 'My Project' in content:
                print("FAILURE: My Project is visible (should be hidden).")
            else:
                print("SUCCESS: My Project is HIDDEN.")

            # Cleanup
            db.session.delete(my_project)
            db.session.delete(other_project)
            db.session.commit()

if __name__ == "__main__":
    verify_home_filtering()
