from app import app, db, MyJourneyRequest, User, MyJourney

with app.app_context():
    requests = MyJourneyRequest.query.all()
    print(f"Total requests: {len(requests)}")
    for req in requests:
        user = User.query.get(req.user_id)
        journey = MyJourney.query.get(req.my_journey_id)
        print(f"ID: {req.id}, User: {user.name if user else 'Unknown'}, Project: {journey.project_name if journey else 'Unknown'}, Status: {req.status}")
