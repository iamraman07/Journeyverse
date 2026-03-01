from app import app, db, MyCollab

with app.app_context():
    projects = MyCollab.query.all()
    print("Remaining Projects in MyCollab:")
    for p in projects:
        print(f"- {p.project_name}")
