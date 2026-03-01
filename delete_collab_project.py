from app import app, db, MyCollab

with app.app_context():
    project = MyCollab.query.filter_by(project_name="Mars base alpha").first()
    if project:
        print(f"Found project: {project.project_name}")
        db.session.delete(project)
        db.session.commit()
        print("Project deleted successfully.")
    else:
        print("Project 'Mars base alpha' not found in MyCollab table.")
