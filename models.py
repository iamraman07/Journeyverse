from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<User {self.email}>"

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    date_and_time = db.Column(db.DateTime, nullable=False)
    project_description = db.Column(db.Text, nullable=False)
    likes = db.Column(db.Integer, default=0)
    comments = db.Column(db.Integer, default=0)
    members = db.Column(db.String(255), nullable=True) # Storing as string for flexibility

    @property
    def member_count(self):
        if not self.members:
            return 0
        return len([m for m in self.members.split(',') if m.strip()])

    def __repr__(self):
        return f"<Project {self.project_description[:20]}...>"

class JourneyDay(db.Model):
    __tablename__ = 'journey_days'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    day_number = db.Column(db.Integer, nullable=False)
    member_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    project = db.relationship('Project', backref=db.backref('journey_days', lazy=True))

    def __repr__(self):
        return f"<JourneyDay Day {self.day_number} - {self.member_name}>"

class ProjectRequest(db.Model):
    __tablename__ = 'project_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    project = db.relationship('Project', backref=db.backref('requests', lazy=True))
    user = db.relationship('User', backref=db.backref('psroject_requests', lazy=True))

    def __repr__(self):
        return f"<ProjectRequest Project {self.project_id} User {self.user_id} Status {self.status}>"

class ProjectLike(db.Model):
    __tablename__ = 'project_likes'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    # Storing just the name for simplicity in this sample, or link to User if strictly relational
    user_name = db.Column(db.String(100), nullable=False) 

class ProjectComment(db.Model):
    __tablename__ = 'project_comments'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_name = db.Column(db.String(100), nullable=False)
    comment_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class MyJourney(db.Model):
    __tablename__ = 'my_journey'
    
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(100), nullable=False)
    project_date_time = db.Column(db.DateTime, nullable=False)
    project_description = db.Column(db.Text, nullable=False)
    likes = db.Column(db.Integer, default=0)
    comments = db.Column(db.Integer, default=0)
    members = db.Column(db.String(255), nullable=True) # Storing member names as comma-separated string
    admin_name = db.Column(db.String(100), nullable=True) # Store the creator's name as admin

    @property
    def member_count(self):
        if not self.members:
            return 0
        return len([m for m in self.members.split(',') if m.strip()])

    def __repr__(self):
        return f"<MyJourney {self.project_name}>"

class MyJourneyDay(db.Model):
    __tablename__ = 'my_journey_days'
    
    id = db.Column(db.Integer, primary_key=True)
    my_journey_id = db.Column(db.Integer, db.ForeignKey('my_journey.id'), nullable=False)
    # Storing date of the journey. 
    # User requirement: Dates drop down from "first date" to current date.
    journey_date = db.Column(db.Date, nullable=False) 
    member_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # We might still want day_number for ordering or display, 
    # but the user emphasized dates. We can calculate day_number dynamically 
    # relative to the start date if needed, or store it.
    # Let's verify if day_number is strictly needed. 
    # The current UI displays "Day 1", "Day 2". 
    # If we have a date, we can calculate Day X = (journey_date - start_date).days + 1.
    
    journey = db.relationship('MyJourney', backref=db.backref('days', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<MyJourneyDay {self.journey_date} - {self.member_name}>"

class MyJourneyLike(db.Model):
    __tablename__ = 'my_journey_likes'
    id = db.Column(db.Integer, primary_key=True)
    my_journey_id = db.Column(db.Integer, db.ForeignKey('my_journey.id'), nullable=False)
    user_name = db.Column(db.String(100), nullable=False)

class MyJourneyComment(db.Model):
    __tablename__ = 'my_journey_comments'
    id = db.Column(db.Integer, primary_key=True)
    my_journey_id = db.Column(db.Integer, db.ForeignKey('my_journey.id'), nullable=False)
    user_name = db.Column(db.String(100), nullable=False)
    comment_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# --- My Collab Models ---

class MyCollab(db.Model):
    __tablename__ = 'my_collab'
    
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(100), nullable=False)
    project_date_time = db.Column(db.DateTime, nullable=False)
    project_description = db.Column(db.Text, nullable=False)
    likes = db.Column(db.Integer, default=0)
    comments = db.Column(db.Integer, default=0)
    members = db.Column(db.String(255), nullable=True) 
    admin_name = db.Column(db.String(100), nullable=True)

    @property
    def member_count(self):
        if not self.members:
            return 0
        return len([m for m in self.members.split(',') if m.strip()])

    def __repr__(self):
        return f"<MyCollab {self.project_name}>"

class MyCollabDay(db.Model):
    __tablename__ = 'my_collab_days'
    
    id = db.Column(db.Integer, primary_key=True)
    my_collab_id = db.Column(db.Integer, db.ForeignKey('my_collab.id'), nullable=False)
    journey_date = db.Column(db.Date, nullable=False) 
    member_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    collab = db.relationship('MyCollab', backref=db.backref('days', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<MyCollabDay {self.journey_date} - {self.member_name}>"

class MyCollabLike(db.Model):
    __tablename__ = 'my_collab_likes'
    id = db.Column(db.Integer, primary_key=True)
    my_collab_id = db.Column(db.Integer, db.ForeignKey('my_collab.id'), nullable=False)
    user_name = db.Column(db.String(100), nullable=False)

class MyCollabComment(db.Model):
    __tablename__ = 'my_collab_comments'
    id = db.Column(db.Integer, primary_key=True)
    my_collab_id = db.Column(db.Integer, db.ForeignKey('my_collab.id'), nullable=False)
    user_name = db.Column(db.String(100), nullable=False)
    comment_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class MyJourneyRequest(db.Model):
    __tablename__ = 'my_journey_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    my_journey_id = db.Column(db.Integer, db.ForeignKey('my_journey.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, accepted, rejected
    request_message = db.Column(db.Text, nullable=True) # Optional message from the requester
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    my_journey = db.relationship('MyJourney', backref=db.backref('requests', lazy=True, cascade="all, delete-orphan"))
    user = db.relationship('User', backref=db.backref('my_journey_requests', lazy=True))

    def __repr__(self):
        return f"<MyJourneyRequest Journey {self.my_journey_id} User {self.user_id} Status {self.status}>"

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False) # 'like', 'comment', 'request_received', 'request_update'
    link = db.Column(db.String(255), nullable=True) # URL to redirect to
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    recipient = db.relationship('User', backref=db.backref('notifications', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Notification {self.type} for User {self.recipient_id}>"
