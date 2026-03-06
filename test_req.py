import traceback
from app import app, db
from models import User, MyJourney, MyJourneyRequest, Notification

app.config['TESTING'] = True

with app.app_context():
    try:
        # Create a user and a project first to avoid constraint errors
        user = User.query.first()
        if not user:
            user = User(name='admin_test', email='test@test.com', password='pwd')
            db.session.add(user)
            db.session.commit()
            
        journey = MyJourney.query.first()
        if not journey:
            from datetime import datetime
            journey = MyJourney(project_name='Test', project_date_time=datetime.now(), project_description='Desc', admin_name=user.name)
            db.session.add(journey)
            db.session.commit()

        j_id = journey.id

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess['user_id'] = user.id
                sess['user_name'] = user.name
            response = c.post(f'/project/request/{j_id}', json={'message': 'hello'})
            print("Response Status:", response.status_code)
            print("Response Data:", response.get_json() or response.data.decode())
    except Exception as e:
        traceback.print_exc()
