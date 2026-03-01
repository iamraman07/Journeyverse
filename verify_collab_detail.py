from app import app, db, User, MyJourney
from datetime import datetime
import traceback

def verify_collab_detail():
    with app.test_client() as client:
        with app.app_context():
            # Setup
            owner = User.query.filter_by(name="CollabOwner").first() or User(name="CollabOwner", email="cowner@test.com", password="pw")
            member = User.query.filter_by(name="CollabMember").first() or User(name="CollabMember", email="cmember@test.com", password="pw")
            db.session.add(owner)
            db.session.add(member)
            db.session.commit()
            
            project = MyJourney(
                project_name="Collab Project",
                project_date_time=datetime.now(),
                project_description="Collab Desc",
                members=f"{owner.name},{member.name}", # Simple CSV
                admin_name=owner.name
            )
            db.session.add(project)
            db.session.commit()
            
            # Login as Member
            with client.session_transaction() as sess:
                sess['user_id'] = member.id
                sess['user_name'] = member.name
            
            print(f"Member ({member.name}) accessing Collab Detail /my_collab_detail/{project.id}...")
            
            try:
                resp = client.get(f'/my_collab_detail/{project.id}')
                
                if resp.status_code == 200:
                    print("SUCCESS: Collab Detail page loaded (200 OK).")
                    if b'Collab Project' in resp.data:
                        print("SUCCESS: Project name visible.")
                    else:
                        print("FAILURE: Project name missing.")
                else:
                    print(f"FAILURE: Page load failed with status {resp.status_code}")
            except:
                traceback.print_exc()

            # Cleanup
            db.session.delete(project)
            db.session.commit()

if __name__ == "__main__":
    verify_collab_detail()
