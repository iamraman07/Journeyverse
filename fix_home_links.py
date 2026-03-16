from app import app, db
from models import Notification

with app.app_context():
    notifs = Notification.query.filter_by(link='/home').all()
    count = 0
    for n in notifs:
        n.link = '/'
        count += 1
        
    db.session.commit()
    print(f"Updated {count} notifications with link='/home' to '/'")
