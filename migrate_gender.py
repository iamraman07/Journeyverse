from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE users ADD COLUMN gender VARCHAR(20) DEFAULT NULL;"))
        db.session.commit()
        print("Column 'gender' added successfully.")
    except Exception as e:
        print(f"Error (maybe column exists): {e}")
