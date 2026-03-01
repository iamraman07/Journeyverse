from app import app, db, MyCollab, MyCollabDay

with app.app_context():
    # Find the project
    project = MyCollab.query.filter_by(project_name="Mars Base Alpha").first()
    
    if project:
        print(f"Found project: {project.project_name} (ID: {project.id})")
        
        # Find all day descriptions
        days = MyCollabDay.query.filter_by(my_collab_id=project.id).all()
        count = len(days)
        
        if count > 0:
            print(f"Found {count} day descriptions. Deleting...")
            for day in days:
                db.session.delete(day)
            
            db.session.commit()
            print("All day descriptions removed successfully.")
        else:
            print("No day descriptions found for this project.")
            
    else:
        print("Project 'Mars Base Alpha' not found.")
