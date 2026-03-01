from flask import Flask, render_template, redirect, url_for, flash, session, request, jsonify
from flask_bcrypt import Bcrypt
from config import Config
from models import db, User, Project, JourneyDay, ProjectRequest, ProjectLike, ProjectComment, MyJourney, MyJourneyDay, MyJourneyLike, MyJourneyComment, MyCollab, MyCollabDay, MyCollabLike, MyCollabComment, MyJourneyRequest, Notification

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
bcrypt = Bcrypt(app)

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Check your email and password.', 'danger')
            
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validation checks
        if not name or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('signup'))
            
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists.', 'warning')
            return redirect(url_for('signup'))
            
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(name=name, email=email, password=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))
    
    from datetime import datetime
    hour = datetime.now().hour
    if 5 <= hour < 12:
        greeting = "Good Morning"
    elif 12 <= hour < 17:
        greeting = "Good Afternoon"
    elif 17 <= hour < 21:
        greeting = "Good Evening"
    else:
        greeting = "Hello"
        
    projects = MyJourney.query.filter(MyJourney.admin_name != session['user_name']).all()
    
    # Get IDs of projects liked by the user
    liked_project_ids = []
    if 'user_name' in session:
        user_likes = MyJourneyLike.query.filter_by(user_name=session['user_name']).all()
        liked_project_ids = [like.my_journey_id for like in user_likes]
        
    return render_template('home.html', projects=projects, user_name=session['user_name'], greeting=greeting, liked_project_ids=liked_project_ids)

@app.route('/journey/<int:project_id>')
def journey_detail(project_id):
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))
        
    # Use MyJourney instead of Project
    project = MyJourney.query.get_or_404(project_id)
    
    # Use MyJourneyDay instead of JourneyDay
    real_days = MyJourneyDay.query.filter_by(my_journey_id=project.id).order_by(MyJourneyDay.journey_date, MyJourneyDay.id).all()
    journey_days = []
    
    # Calculate Day Numbers logic (same as my_journey_detail)
    dropdown_start_date = project.project_date_time.date()
    calc_start_date = dropdown_start_date
    if real_days:
        first_entry_date = real_days[0].journey_date
        if first_entry_date < calc_start_date:
            calc_start_date = first_entry_date
            
    for day in real_days:
        delta = (day.journey_date - calc_start_date).days
        day_num = delta + 1
        journey_days.append({
            'day_number': day_num,
            'member_name': day.member_name,
            'description': day.description,
            'date': day.journey_date
        })
    
    # Fetch Social Data
    likes_list = MyJourneyLike.query.filter_by(my_journey_id=project.id).all()
    comments_list = MyJourneyComment.query.filter_by(my_journey_id=project.id).order_by(MyJourneyComment.created_at.desc()).all()
    
    # Check request status
    user_id = session['user_id']
    current_user_name = session.get('user_name')
    existing_request = MyJourneyRequest.query.filter_by(my_journey_id=project.id, user_id=user_id).first()
    
    # Self-heal logic: If request is "accepted", but user is NOT in the project.members string, 
    # it means they were removed previously without the request being cleared.
    request_status = existing_request.status if existing_request else None
    
    if request_status == 'accepted':
        member_list = [m.strip() for m in project.members.split(',')] if project.members else []
        if current_user_name not in member_list and current_user_name != project.admin_name:
            # User is treated as a ghost member. Clear the request so they can join again.
            db.session.delete(existing_request)
            db.session.commit()
            request_status = None

    # Check if liked by current user
    is_liked = False
    if current_user_name:
        is_liked = MyJourneyLike.query.filter_by(my_journey_id=project.id, user_name=current_user_name).first() is not None


    return render_template('journey_detail.html', 
                           project=project, 
                           journey_days=journey_days, 
                           user_name=current_user_name, 
                           request_status=request_status,
                           likes_list=likes_list,
                           comments_list=comments_list,
                           is_liked=is_liked)

@app.route('/project/request/<int:project_id>', methods=['POST'])
def request_join_project(project_id):
    if 'user_id' not in session:
        return {'status': 'error', 'message': 'Unauthorized'}, 401
    
    user_id = session['user_id']
    existing_request = MyJourneyRequest.query.filter_by(my_journey_id=project_id, user_id=user_id).first()
    
    if existing_request:
        return {'status': 'success', 'request_state': existing_request.status, 'message': 'Request already exists'}
        
    data = request.get_json() or {}
    req_msg = data.get('message', '').strip()
        
    new_request = MyJourneyRequest(my_journey_id=project_id, user_id=user_id, request_message=req_msg)
    db.session.add(new_request)
    
    # Notify Admin
    project = MyJourney.query.get(project_id)
    admin_user = User.query.filter_by(name=project.admin_name).first()
    if admin_user:
        notif = Notification(
            recipient_id=admin_user.id,
            message=f"<b>{session['user_name']}</b> requested to join <b>{project.project_name}</b>.",
            type='request_received',
            link=url_for('pending_requests')
        )
        db.session.add(notif)
        
    db.session.commit()
    
    return {'status': 'success', 'request_state': 'pending', 'message': 'Request sent successfully'}

@app.route('/my_journeys')
def my_journeys():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if sample data needs to be inserted
    if MyJourney.query.count() == 0:
        from datetime import datetime
        sample_data = [
            MyJourney(
                project_name="Deep Sea Exploration",
                project_date_time=datetime(2023, 10, 15, 9, 30),
                project_description="Exploring the depths of the Mariana Trench.",
                likes=120,
                comments=45,
                members="Alice, Bob, Charlie"
            ),
            MyJourney(
                project_name="Mountain Trekking",
                project_date_time=datetime(2023, 11, 2, 8, 0),
                project_description="A 5-day trek through the Himalayas.",
                likes=85,
                comments=20,
                members="David, Eve"
            ),
            MyJourney(
                project_name="City Photography",
                project_date_time=datetime(2023, 12, 10, 16, 45),
                project_description="Capturing the urban lifestyle.",
                likes=200,
                comments=60,
                members="Frank, Grace, Heidi"
            )
        ]
        db.session.bulk_save_objects(sample_data)
        db.session.commit()

    user_name = session.get('user_name')
    if user_name:
        journeys = MyJourney.query.filter_by(admin_name=user_name).all()
        # Fallback for old data without admin_name, or just show all if no filtering intended previously?
        # User wants "My Journeys" to NOT show "My Collab's".
        # Assuming "My Journeys" = Created by me.
        # If admin_name is NULL (for old sample data), we might lose them if we strict filter.
        # Let's check if we need to handle None.
        # But for now, strict filtering by admin_name seems to be what is requested to separate them.
    else:
        journeys = []
    return render_template('my_journeys.html', user_name=session.get('user_name'), journeys=journeys)

@app.route('/create_my_journey', methods=['POST'])
def create_my_journey():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    project_name = request.form.get('project_name')
    project_date_time_str = request.form.get('project_date_time')
    project_description = request.form.get('project_description')
    
    if not project_name or not project_date_time_str or not project_description:
        flash('All fields are required.', 'danger')
        return redirect(url_for('my_journeys'))
        
    from datetime import datetime
    try:
        project_date_time = datetime.strptime(project_date_time_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        flash('Invalid date format.', 'danger')
        return redirect(url_for('my_journeys'))
        
    new_journey = MyJourney(
        project_name=project_name,
        project_date_time=project_date_time,
        project_description=project_description,
        likes=0,
        comments=0,
        members=session.get('user_name', 'Me'),
        admin_name=session.get('user_name')
    )
    
    db.session.add(new_journey)
    db.session.commit()
    
    flash('Project created successfully!', 'success')
    return redirect(url_for('my_journeys'))

@app.route('/delete_my_journey/<int:journey_id>', methods=['POST'])
def delete_my_journey(journey_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    journey = MyJourney.query.get_or_404(journey_id)
    
    # Permission Check: Only Admin can delete
    if journey.admin_name and journey.admin_name != session.get('user_name'):
        flash('Only the admin can delete this project.', 'danger')
        return redirect(url_for('my_journeys'))
    
    db.session.delete(journey)
    db.session.commit()
    
    flash('Project deleted successfully!', 'success')
    return redirect(url_for('my_journeys'))

@app.route('/edit_my_journey/<int:journey_id>', methods=['POST'])
def edit_my_journey(journey_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    journey = MyJourney.query.get_or_404(journey_id)
    
    # Permission Check: Only Admin can edit
    if journey.admin_name and journey.admin_name != session.get('user_name'):
        flash('Only the admin can edit this project.', 'danger')
        return redirect(url_for('my_journeys'))
    
    project_name = request.form.get('project_name')
    project_date_time_str = request.form.get('project_date_time')
    project_description = request.form.get('project_description')
    
    if not project_name or not project_date_time_str or not project_description:
        flash('All fields are required.', 'danger')
        return redirect(url_for('my_journeys'))

    from datetime import datetime
    try:
        project_date_time = datetime.strptime(project_date_time_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        flash('Invalid date format.', 'danger')
        return redirect(url_for('my_journeys'))
        
    journey.project_name = project_name
    journey.project_date_time = project_date_time
    journey.project_description = project_description
    
    db.session.commit()
    
    flash('Project updated successfully!', 'success')
    return redirect(url_for('my_journeys'))

@app.route('/remove_member/<int:journey_id>', methods=['POST'])
def remove_member(journey_id):
    if 'user_id' not in session:
        return {'status': 'error', 'message': 'Unauthorized'}, 401
    
    journey = MyJourney.query.get_or_404(journey_id)
    
    # Permission Check: Only Admin can remove members
    if journey.admin_name and journey.admin_name != session.get('user_name'):
         return {'status': 'error', 'message': 'Only admin can remove members'}, 403
    data = request.get_json()
    member_to_remove = data.get('member_name')
    
    if not member_to_remove:
         return {'status': 'error', 'message': 'Member name required'}, 400
         
    if journey.members:
        members = [m.strip() for m in journey.members.split(',')]
        if member_to_remove in members:
            members.remove(member_to_remove)
            journey.members = ", ".join(members)
            
            # --- Side Effects ---
            removed_user = User.query.filter_by(name=member_to_remove).first()
            if removed_user:
                # 1. Clear existing pending/accepted request so "Request to Join" works again
                existing_request = MyJourneyRequest.query.filter_by(my_journey_id=journey_id, user_id=removed_user.id).first()
                if existing_request:
                    db.session.delete(existing_request)
                
                # 2. Add Notification
                notif = Notification(
                    recipient_id=removed_user.id,
                    message=f"You have been removed from the project <b>{journey.project_name}</b> by the admin.",
                    type='member_removed',
                    link=url_for('notifications')
                )
                db.session.add(notif)
                
            db.session.commit()
            return {'status': 'success', 'message': 'Member removed'}
            
    return {'status': 'error', 'message': 'Member not found'}





@app.route('/my_collabs')
def my_collabs():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_name = session.get('user_name')
    # Use MyJourney instead of MyCollab
    all_journeys = MyJourney.query.all()
    my_collabs_list = []
    
    for journey in all_journeys:
        # Don't show own projects as collabs (optional preference, usually desired)
        if journey.admin_name == user_name:
            continue
            
        if journey.members:
             members_list = [m.strip() for m in journey.members.split(',')]
             if user_name in members_list:
                 my_collabs_list.append(journey)
    
    return render_template('my_collabs.html', user_name=user_name, journeys=my_collabs_list)


@app.route('/pending_requests')
def pending_requests():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_name = session.get('user_name')
    
    # Sample Data Logic
    if MyJourneyRequest.query.count() == 0:
        def get_or_create_user(name, email, password="password"):
            u = User.query.filter_by(name=name).first()
            if not u:
                pwd = bcrypt.generate_password_hash(password).decode('utf-8')
                u = User(name=name, email=email, password=pwd)
                db.session.add(u)
                db.session.commit()
            return u
            
        alice = get_or_create_user("Alice", "alice@example.com")
        bob = get_or_create_user("Bob", "bob@example.com")
        
        my_project = MyJourney.query.filter_by(admin_name=user_name).first()
        
        if my_project:
            req1 = MyJourneyRequest(my_journey_id=my_project.id, user_id=alice.id, status='pending')
            req2 = MyJourneyRequest(my_journey_id=my_project.id, user_id=bob.id, status='pending')
            db.session.add(req1)
            db.session.add(req2)
            db.session.commit()
            
    my_projects = MyJourney.query.filter_by(admin_name=user_name).all()
    my_project_ids = [p.id for p in my_projects]
    
    requests = MyJourneyRequest.query.filter(MyJourneyRequest.my_journey_id.in_(my_project_ids), MyJourneyRequest.status == 'pending').all()
    
    return render_template('pending_requests.html', requests=requests, user_name=user_name)

@app.route('/accept_request/<int:request_id>', methods=['POST'])
def accept_request(request_id):
    if 'user_id' not in session:
        return {'status': 'error', 'message': 'Unauthorized'}, 401
        
    req = MyJourneyRequest.query.get_or_404(request_id)
    journey = req.my_journey
    
    # Permission Check: Only Admin can accept
    if journey.admin_name and journey.admin_name != session.get('user_name'):
         return {'status': 'error', 'message': 'Only admin can accept requests'}, 403
         
    # 1. Update Request Status
    req.status = 'accepted'
    
    # 2. Add User to Members List
    requester = User.query.get(req.user_id)
    if requester:
        existing_members = [m.strip() for m in journey.members.split(',')] if journey.members else []
        if requester.name not in existing_members:
            existing_members.append(requester.name)
            journey.members = ", ".join(existing_members)
            
    db.session.commit()
    
    # Notify Requester
    notif = Notification(
        recipient_id=req.user_id,
        message=f"Your request to join <b>{journey.project_name}</b> was accepted!",
        type='request_accepted',
        link=url_for('my_collab_detail', collab_id=journey.id)
    )
    db.session.add(notif)
    db.session.commit()
    return {'status': 'success', 'message': 'Request accepted'}

@app.route('/decline_request/<int:request_id>', methods=['POST'])
def decline_request(request_id):
    if 'user_id' not in session:
        return {'status': 'error', 'message': 'Unauthorized'}, 401
        
    req = MyJourneyRequest.query.get_or_404(request_id)
    journey = req.my_journey
    
    # Permission Check: Only Admin can decline
    if journey.admin_name and journey.admin_name != session.get('user_name'):
         return {'status': 'error', 'message': 'Only admin can decline requests'}, 403
         
    # Update Request Status
    req.status = 'rejected'
    db.session.commit()
    
    # Notify Requester
    notif = Notification(
        recipient_id=req.user_id,
        message=f"Your request to join <b>{journey.project_name}</b> was declined.",
        type='request_declined',
        link='#' 
    )
    db.session.add(notif)
    db.session.commit()
    
    return {'status': 'success', 'message': 'Request declined'}



@app.route('/my_journey_detail/<int:journey_id>')
def my_journey_detail(journey_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    journey = MyJourney.query.get_or_404(journey_id)
    
    # Fetch Real Journey Days - Ordered by Date then ID (insertion order)
    real_days = MyJourneyDay.query.filter_by(my_journey_id=journey.id).order_by(MyJourneyDay.journey_date, MyJourneyDay.id).all()
    journey_days = []
    
    # Determine Start Dates
    # 1. Dropdown Base: Strictly Project Creation Date (User Request)
    dropdown_start_date = journey.project_date_time.date()
    
    # 2. Calculation Base: Earliest of (Project Date, First Entry Date) 
    # to avoid negative days if entries exist before the project date.
    calc_start_date = dropdown_start_date
    if real_days:
        first_entry_date = real_days[0].journey_date
        if first_entry_date < calc_start_date:
            calc_start_date = first_entry_date

    for day in real_days:
        # Calculate Day Number (Calendar based)
        delta = (day.journey_date - calc_start_date).days
        day_num = delta + 1
        journey_days.append({
            'day_number': day_num,
            'member_name': day.member_name,
            'description': day.description,
            'date': day.journey_date
        })
    
    # Social Data (Mock/Real Mix - keeping existing logic for social as user didn't request social backend changes yet)
    # Existing code used mock list logic based on counts in DB. We'll keep that for now to avoid breaking view.
    
    # Social Data
    likes_list = MyJourneyLike.query.filter_by(my_journey_id=journey.id).all()
    comments_list = MyJourneyComment.query.filter_by(my_journey_id=journey.id).order_by(MyJourneyComment.created_at.desc()).all()
    
    current_user_name = session.get('user_name')
    is_liked = False
    if current_user_name:
        is_liked = MyJourneyLike.query.filter_by(my_journey_id=journey.id, user_name=current_user_name).first() is not None
            
    members_list = []
    
    if journey.members:
        members_list = [m.strip() for m in journey.members.split(',')]
    
    if current_user_name and current_user_name not in members_list:
        members_list.insert(0, current_user_name)

    return render_template('my_journey_detail.html', 
                           journey=journey,
                           user_name=current_user_name, 
                           admin_name=journey.admin_name,
                           likes_list=likes_list,
                           comments_list=comments_list,
                           members_list=members_list,
                           journey_days=journey_days,
                           start_date=dropdown_start_date,
                           is_liked=is_liked) # Pass start_date for JS dropdown logic

@app.route('/add_journey_day/<int:journey_id>', methods=['POST'])
def add_journey_day(journey_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    journey = MyJourney.query.get_or_404(journey_id)
    
    member_name = request.form.get('member_name')
    date_str = request.form.get('journey_date')
    description = request.form.get('description')
    
    if not member_name or not date_str or not description:
        flash('All fields are required.', 'danger')
        return redirect(url_for('my_journey_detail', journey_id=journey_id))
        
    from datetime import datetime
    try:
        j_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format.', 'danger')
        return redirect(url_for('my_journey_detail', journey_id=journey_id))
        
    # Check for existing entry
    existing_day = MyJourneyDay.query.filter_by(
        my_journey_id=journey.id,
        journey_date=j_date,
        member_name=member_name
    ).first()

    if existing_day:
        existing_day.description = description
        flash('Journey entry updated successfully!', 'success')
    else:    
        new_day = MyJourneyDay(
            my_journey_id=journey.id,
            journey_date=j_date,
            member_name=member_name,
            description=description
        )
        db.session.add(new_day)
        flash('Journey entry added successfully!', 'success')
    
    db.session.commit()
    return redirect(url_for('my_journey_detail', journey_id=journey_id))

    db.session.commit()
    return redirect(url_for('my_journey_detail', journey_id=journey_id))

# --- Social Routes ---

@app.route('/like_project/<int:project_id>')
def like_project(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    project = Project.query.get_or_404(project_id)
    user_name = session['user_name']
    
    existing_like = ProjectLike.query.filter_by(project_id=project.id, user_name=user_name).first()
    
    if existing_like:
        db.session.delete(existing_like)
        project.likes = max(0, project.likes - 1)
    else:
        new_like = ProjectLike(project_id=project.id, user_name=user_name)
        db.session.add(new_like)
        project.likes += 1
        
    db.session.commit()
    return redirect(url_for('journey_detail', project_id=project_id))

@app.route('/comment_project/<int:project_id>', methods=['POST'])
def comment_project(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    project = Project.query.get_or_404(project_id)
    user_name = session['user_name']
    comment_text = request.form.get('comment_text')
    
    if comment_text:
        new_comment = ProjectComment(project_id=project.id, user_name=user_name, comment_text=comment_text)
        db.session.add(new_comment)
        project.comments += 1
        db.session.commit()
        
    return redirect(url_for('journey_detail', project_id=project_id))

@app.route('/like_my_journey/<int:journey_id>')
def like_my_journey(journey_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    journey = MyJourney.query.get_or_404(journey_id)
    user_name = session['user_name']
    
    existing_like = MyJourneyLike.query.filter_by(my_journey_id=journey.id, user_name=user_name).first()
    
    if existing_like:
        db.session.delete(existing_like)
        journey.likes = max(0, journey.likes - 1)
    else:
        new_like = MyJourneyLike(my_journey_id=journey.id, user_name=user_name)
        db.session.add(new_like)
        journey.likes += 1
        
        # Notify Admin
        admin_user = User.query.filter_by(name=journey.admin_name).first()
        if admin_user and admin_user.name != user_name:
             notif = Notification(
                recipient_id=admin_user.id,
                message=f"<b>{user_name}</b> liked your project <b>{journey.project_name}</b>.",
                type='like',
                link=url_for('my_journey_detail', journey_id=journey.id)
            )
             db.session.add(notif)
        
    db.session.commit()
    return redirect(url_for('my_journey_detail', journey_id=journey_id))

@app.route('/comment_my_journey/<int:journey_id>', methods=['POST'])
def comment_my_journey(journey_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    journey = MyJourney.query.get_or_404(journey_id)
    user_name = session['user_name']
    comment_text = request.form.get('comment_text')
    
    if comment_text:
        new_comment = MyJourneyComment(my_journey_id=journey.id, user_name=user_name, comment_text=comment_text)
        db.session.add(new_comment)
        journey.comments += 1
        
        # Notify Admin
        admin_user = User.query.filter_by(name=journey.admin_name).first()
        if admin_user and admin_user.name != user_name:
             notif = Notification(
                recipient_id=admin_user.id,
                message=f"<b>{user_name}</b> commented on <b>{journey.project_name}</b>.",
                type='comment',
                link=url_for('my_journey_detail', journey_id=journey.id)
            )
             db.session.add(notif)
             
        db.session.commit()
        
    return redirect(url_for('my_journey_detail', journey_id=journey_id))

@app.route('/logout')

def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/my_collab_detail/<int:collab_id>')
def my_collab_detail(collab_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    # Collab is just a MyJourney that you are a member of
    journey = MyJourney.query.get_or_404(collab_id)
    
    # Fetch Journey Days
    real_days = MyJourneyDay.query.filter_by(my_journey_id=journey.id).order_by(MyJourneyDay.journey_date, MyJourneyDay.id).all()
    journey_days = []
    
    dropdown_start_date = journey.project_date_time.date()
    calc_start_date = dropdown_start_date
    if real_days:
        first_entry_date = real_days[0].journey_date
        if first_entry_date < calc_start_date:
            calc_start_date = first_entry_date
            
    for day in real_days:
        delta = (day.journey_date - calc_start_date).days
        day_num = delta + 1
        journey_days.append({
            'day_number': day_num,
            'member_name': day.member_name,
            'description': day.description,
            'date': day.journey_date
        })
    
    likes_list = MyJourneyLike.query.filter_by(my_journey_id=journey.id).all()
    comments_list = MyJourneyComment.query.filter_by(my_journey_id=journey.id).order_by(MyJourneyComment.created_at.desc()).all()
    
    current_user_name = session.get('user_name')
    is_liked = False
    if current_user_name:
        is_liked = MyJourneyLike.query.filter_by(my_journey_id=journey.id, user_name=current_user_name).first() is not None
        
    members_list = [m.strip() for m in journey.members.split(',')] if journey.members else []

    return render_template('my_collab_detail.html', 
                           journey=journey, 
                           user_name=current_user_name,
                           admin_name=journey.admin_name,
                           likes_list=likes_list,
                           comments_list=comments_list,
                           members_list=members_list,
                           journey_days=journey_days,
                           start_date=dropdown_start_date,
                           is_liked=is_liked)

@app.route('/add_collab_day/<int:collab_id>', methods=['POST'])
def add_collab_day(collab_id):
    # Same logic as add_journey_day, but redirects to my_collab_detail
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    journey = MyJourney.query.get_or_404(collab_id)
    
    member_name = request.form.get('member_name')
    date_str = request.form.get('journey_date')
    description = request.form.get('description')
    
    if not member_name or not date_str or not description:
        flash('All fields are required.', 'danger')
        return redirect(url_for('my_collab_detail', collab_id=collab_id))
        
    from datetime import datetime
    try:
        j_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format.', 'danger')
        return redirect(url_for('my_collab_detail', collab_id=collab_id))
        
    existing_day = MyJourneyDay.query.filter_by(
        my_journey_id=journey.id,
        journey_date=j_date,
        member_name=member_name
    ).first()

    if existing_day:
        existing_day.description = description
        flash('Entry updated successfully!', 'success')
    else:    
        new_day = MyJourneyDay(
            my_journey_id=journey.id,
            journey_date=j_date,
            member_name=member_name,
            description=description
        )
        db.session.add(new_day)
        flash('Entry added successfully!', 'success')
    
    db.session.commit()
    return redirect(url_for('my_collab_detail', collab_id=collab_id))

@app.route('/like_my_collab/<int:collab_id>')
def like_my_collab(collab_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    journey = MyJourney.query.get_or_404(collab_id)
    user_name = session['user_name']
    
    existing_like = MyJourneyLike.query.filter_by(my_journey_id=journey.id, user_name=user_name).first()
    
    if existing_like:
        db.session.delete(existing_like)
        journey.likes = max(0, journey.likes - 1)
    else:
        new_like = MyJourneyLike(my_journey_id=journey.id, user_name=user_name)
        db.session.add(new_like)
        journey.likes += 1
        
        # Notify Admin
        admin_user = User.query.filter_by(name=journey.admin_name).first()
        if admin_user and admin_user.name != user_name:
             notif = Notification(
                recipient_id=admin_user.id,
                message=f"<b>{user_name}</b> liked your project <b>{journey.project_name}</b>.",
                type='like',
                link=url_for('my_journey_detail', journey_id=journey.id)
            )
             db.session.add(notif)
        
    db.session.commit()
    return redirect(url_for('my_collab_detail', collab_id=collab_id))

@app.route('/comment_my_collab/<int:collab_id>', methods=['POST'])
def comment_my_collab(collab_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    journey = MyJourney.query.get_or_404(collab_id)
    user_name = session['user_name']
    comment_text = request.form.get('comment_text')
    
    if comment_text:
        new_comment = MyJourneyComment(my_journey_id=journey.id, user_name=user_name, comment_text=comment_text)
        db.session.add(new_comment)
        journey.comments += 1
        
        # Notify Admin
        admin_user = User.query.filter_by(name=journey.admin_name).first()
        if admin_user and admin_user.name != user_name:
             notif = Notification(
                recipient_id=admin_user.id,
                message=f"<b>{user_name}</b> commented on <b>{journey.project_name}</b>.",
                type='comment',
                link=url_for('my_journey_detail', journey_id=journey.id)
            )
             db.session.add(notif)
             
        db.session.commit()
        
    return redirect(url_for('my_collab_detail', collab_id=collab_id))


@app.route('/notifications')
def notifications():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    notifications = Notification.query.filter_by(recipient_id=user_id).order_by(Notification.created_at.desc()).all()
    
    # Mark all as read when viewed? Or user manually? 
    # Usually standard is mark simplified. Let's mark them as read.
    for n in notifications:
        n.is_read = True
    db.session.commit()
    
    return render_template('notifications.html', notifications=notifications, user_name=session.get('user_name'))

@app.route('/like_home_journey/<int:journey_id>')
def like_home_journey(journey_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    journey = MyJourney.query.get_or_404(journey_id)
    user_name = session['user_name']
    
    existing_like = MyJourneyLike.query.filter_by(my_journey_id=journey.id, user_name=user_name).first()
    
    if existing_like:
        db.session.delete(existing_like)
        journey.likes = max(0, journey.likes - 1)
    else:
        new_like = MyJourneyLike(my_journey_id=journey.id, user_name=user_name)
        db.session.add(new_like)
        journey.likes += 1
        
        # Notify Admin
        admin_user = User.query.filter_by(name=journey.admin_name).first()
        if admin_user and admin_user.name != user_name:
             notif = Notification(
                recipient_id=admin_user.id,
                message=f"<b>{user_name}</b> liked your project <b>{journey.project_name}</b>.",
                type='like',
                link=url_for('my_journey_detail', journey_id=journey.id)
            )
             db.session.add(notif)
        
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/comment_home_journey/<int:journey_id>', methods=['POST'])
def comment_home_journey(journey_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    journey = MyJourney.query.get_or_404(journey_id)
    user_name = session['user_name']
    comment_text = request.form.get('comment_text')
    
    if comment_text:
        new_comment = MyJourneyComment(my_journey_id=journey.id, user_name=user_name, comment_text=comment_text)
        db.session.add(new_comment)
        journey.comments += 1
        
        # Notify Admin
        admin_user = User.query.filter_by(name=journey.admin_name).first()
        if admin_user and admin_user.name != user_name:
             notif = Notification(
                recipient_id=admin_user.id,
                message=f"<b>{user_name}</b> commented on <b>{journey.project_name}</b>.",
                type='comment',
                link=url_for('my_journey_detail', journey_id=journey.id)
            )
             db.session.add(notif)
             
        db.session.commit()
        
    return redirect(url_for('dashboard'))

@app.route('/api/get_comments/<int:journey_id>')
def api_get_comments(journey_id):
    comments = MyJourneyComment.query.filter_by(my_journey_id=journey_id).order_by(MyJourneyComment.created_at.desc()).all()
    comments_data = []
    for c in comments:
        comments_data.append({
            'user_name': c.user_name,
            'comment_text': c.comment_text,
            'created_at': c.created_at.strftime('%Y-%m-%d')
        })
    return jsonify({'status': 'success', 'comments': comments_data})

@app.route('/like_public_journey/<int:journey_id>')
def like_public_journey(journey_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    journey = MyJourney.query.get_or_404(journey_id)
    user_name = session['user_name']
    
    existing_like = MyJourneyLike.query.filter_by(my_journey_id=journey.id, user_name=user_name).first()
    
    if existing_like:
        db.session.delete(existing_like)
        journey.likes = max(0, journey.likes - 1)
    else:
        new_like = MyJourneyLike(my_journey_id=journey.id, user_name=user_name)
        db.session.add(new_like)
        journey.likes += 1
        
        # Notify Admin
        admin_user = User.query.filter_by(name=journey.admin_name).first()
        if admin_user and admin_user.name != user_name:
             notif = Notification(
                recipient_id=admin_user.id,
                message=f"<b>{user_name}</b> liked your project <b>{journey.project_name}</b>.",
                type='like',
                link=url_for('my_journey_detail', journey_id=journey.id)
            )
             db.session.add(notif)
        
    db.session.commit()
    return redirect(url_for('journey_detail', project_id=journey.id))

@app.route('/comment_public_journey/<int:journey_id>', methods=['POST'])
def comment_public_journey(journey_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    journey = MyJourney.query.get_or_404(journey_id)
    user_name = session['user_name']
    comment_text = request.form.get('comment_text')
    
    if comment_text:
        new_comment = MyJourneyComment(my_journey_id=journey.id, user_name=user_name, comment_text=comment_text)
        db.session.add(new_comment)
        journey.comments += 1
        
        # Notify Admin
        admin_user = User.query.filter_by(name=journey.admin_name).first()
        if admin_user and admin_user.name != user_name:
             notif = Notification(
                recipient_id=admin_user.id,
                message=f"<b>{user_name}</b> commented on <b>{journey.project_name}</b>.",
                type='comment',
                link=url_for('my_journey_detail', journey_id=journey.id)
            )
             db.session.add(notif)
             
        db.session.commit()
        
    return redirect(url_for('journey_detail', project_id=journey.id))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
