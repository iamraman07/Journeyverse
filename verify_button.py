from app import app, db, User, MyJourney
from datetime import datetime

def verify_button_logic():
    with app.test_client() as client:
        with app.app_context():
            # Setup
            owner = User.query.filter_by(name="OwnerUser").first() or User(name="OwnerUser", email="owner@test.com", password="pw")
            visitor = User.query.filter_by(name="VisitorUser").first() or User(name="VisitorUser", email="visitor@test.com", password="pw")
            db.session.add(owner)
            db.session.add(visitor)
            db.session.commit()
            
            project = MyJourney(
                project_name="OwnerProject",
                project_date_time=datetime.now(),
                project_description="Test Desc",
                members=owner.name,
                admin_name=owner.name
            )
            db.session.add(project)
            db.session.commit()
            
            # 1. Owner views logic
            with client.session_transaction() as sess:
                sess['user_id'] = owner.id
                sess['user_name'] = owner.name
                
            print(f"Owner checking project {project.id}...")
            resp = client.get(f'/journey/{project.id}')
            content = resp.data.decode('utf-8')
            
            # Check for button ID presence
            if 'id="requestBtn"' in content:
                # Should NOT be there for owner
                print("FAILURE: Request button visible to Owner.")
                # We can check if it's conditioned out.
                # Since we wrapped it in {% if project.admin_name != user_name %}, it should be gone from HTML entirely.
            else:
                print("SUCCESS: Request button HIDDEN for Owner.")

            # 2. Visitor views logic
            with client.session_transaction() as sess:
                sess['user_id'] = visitor.id
                sess['user_name'] = visitor.name
                
            print(f"Visitor checking project {project.id}...")
            resp = client.get(f'/journey/{project.id}')
            content = resp.data.decode('utf-8')
            
            if 'id="requestBtn"' in content:
                print("SUCCESS: Request button VISIBLE for Visitor.")
            else:
                print("FAILURE: Request button HIDDEN for Visitor.")

            # Cleanup
            db.session.delete(project)
            db.session.commit()

if __name__ == "__main__":
    verify_button_logic()
