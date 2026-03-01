from app import app, db, MyJourneyRequest
from sqlalchemy import func

with app.app_context():
    # Find duplicates: group by user_id and my_journey_id, having count > 1
    duplicates = db.session.query(
        MyJourneyRequest.user_id, 
        MyJourneyRequest.my_journey_id, 
        func.count(MyJourneyRequest.id)
    ).group_by(
        MyJourneyRequest.user_id, 
        MyJourneyRequest.my_journey_id
    ).having(
        func.count(MyJourneyRequest.id) > 1
    ).all()

    print(f"Found {len(duplicates)} duplicate groups.")

    deleted_count = 0
    for user_id, my_journey_id, count in duplicates:
        # Get all requests for this pair
        requests = MyJourneyRequest.query.filter_by(
            user_id=user_id, 
            my_journey_id=my_journey_id
        ).order_by(MyJourneyRequest.id.desc()).all()
        
        # Keep the latest one (first in the list due to desc order), delete the rest
        requests_to_delete = requests[1:]
        
        for req in requests_to_delete:
            db.session.delete(req)
            deleted_count += 1
            
    db.session.commit()
    print(f"Deleted {deleted_count} duplicate requests.")
