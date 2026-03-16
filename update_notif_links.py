from app import app, db
from models import Notification

with app.app_context():
    # Find all 'member_removed' notifications
    notifs = Notification.query.filter_by(type='member_removed').all()
    count = 0
    for n in notifs:
        if n.link and 'notifications' in n.link:
            # We want to change the link from /notifications to /
            n.link = '/' # / is the route for 'home' based on typical Flask setup
            count += 1
            
    db.session.commit()
    print(f"Updated {count} notifications.")
