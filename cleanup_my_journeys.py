from app import app, db, MyJourney

with app.app_context():
    projects_to_delete = ["Mars Base Alpha", "Ocean Cleanup Initiative"]
    
    for name in projects_to_delete:
        journey = MyJourney.query.filter_by(project_name=name).first()
        if journey:
            print(f"Deleting {journey.project_name}...")
            db.session.delete(journey)
    
    db.session.commit()
    print("Cleanup completed successfully.")
