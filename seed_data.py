from app import app, db, JourneyDay, Project
from datetime import datetime

def seed_data():
    with app.app_context():
        # Ensure DB is created
        db.create_all()
        
        # --- Project 1: "The Great Hike" ---
        p1 = Project.query.filter_by(username="Hiker Group").first()
        if not p1:
            print("Creating Project 1...")
            p1 = Project(
                username="Hiker Group",
                date_and_time=datetime.now(),
                project_description="A group journey through the mountains. Documenting every step of the way.",
                likes=150,
                comments=20,
                members="Alice, Bob, Charlie"
            )
            db.session.add(p1)
            db.session.commit()
            
            # Journey Days for Project 1
            days_p1 = [
                # Day 1: Alice and Bob
                {"day": 1, "member": "Alice", "desc": "Started the hike early morning. The weather is perfect."},
                {"day": 1, "member": "Bob", "desc": "Packed all the gear. My backpack is heavier than expected but spirits are high!"},
                # Day 2: Charlie (Long Desc)
                {"day": 2, "member": "Charlie", "desc": "Day 2 was tough. We encountered some rain and had to set up camp early. This is a longer description to test the read more functionality because it explains in detail how we managed to keep our gear dry and the challenges we faced during the sudden downpour."},
                # Day 3: All
                {"day": 3, "member": "Alice", "desc": "Reached the summit!"},
                {"day": 3, "member": "Bob", "desc": "What a view. Totally worth the struggle."},
                {"day": 3, "member": "Charlie", "desc": "Took some amazing drone shots."}
            ]
            
            for d in days_p1:
                db.session.add(JourneyDay(project_id=p1.id, day_number=d['day'], member_name=d['member'], description=d['desc']))
            db.session.commit()
            print("Project 1 data added.")
        else:
             print("Project 1 already exists.")

        # --- Project 2: "Solo coding" ---
        p2 = Project.query.filter_by(username="DevSolo").first()
        if not p2:
            print("Creating Project 2...")
            p2 = Project(
                username="DevSolo",
                date_and_time=datetime.now(),
                project_description="Building a solo startup in 30 days.",
                likes=5,
                comments=2,
                members="DevSolo"
            )
            db.session.add(p2)
            db.session.commit()
            
            # Journey Days for Project 2
            days_p2 = [
                {"day": 1, "member": "DevSolo", "desc": "Initial commit. Setup the repo."},
                {"day": 2, "member": "DevSolo", "desc": "Built the login page. Encountered some bugs with auth but fixed them."},
                {"day": 3, "member": "DevSolo", "desc": "Deployed to staging. It is looking good."}
            ]
             
            for d in days_p2:
                db.session.add(JourneyDay(project_id=p2.id, day_number=d['day'], member_name=d['member'], description=d['desc']))
            db.session.commit()
            print("Project 2 data added.")
        else:
            print("Project 2 already exists.")
            
        print("Seed data check complete.")

if __name__ == '__main__':
    seed_data()
