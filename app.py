from flask import Flask, render_template, redirect, url_for, flash, session, request, jsonify, make_response
from flask_bcrypt import Bcrypt
from config import Config
from models import db, User, Project, JourneyDay, ProjectRequest, ProjectLike, ProjectComment, MyJourney, MyJourneyDay, MyJourneyLike, MyJourneyComment, MyCollab, MyCollabDay, MyCollabLike, MyCollabComment, MyJourneyRequest, Notification, GeneratedStory
import os
import io
from google import genai
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER


if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key.strip()] = value.strip('"\'')
print("API KEY:", os.getenv("GOOGLE_API_KEY"))

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
        gender = request.form.get('gender')
        
        # Validation checks
        if not name or not email or not password or not gender:
            flash('All fields are required.', 'danger')
            return redirect(url_for('signup'))
            
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists.', 'warning')
            return redirect(url_for('signup'))
            
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(name=name, email=email, password=hashed_password, gender=gender)
        
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
        if existing_request.status == 'pending':
            return {'status': 'success', 'request_state': existing_request.status, 'message': 'Request already exists'}
        else:
            existing_request.status = 'pending'
            data = request.get_json() or {}
            existing_request.request_message = data.get('message', '').strip()
            project = MyJourney.query.get(project_id)
            admin_users = User.query.filter_by(name=project.admin_name).all()
            for admin_u in admin_users:
                if admin_u.id != session['user_id']:
                    notif = Notification(
                        recipient_id=admin_u.id,
                        message=f"{session['user_name']} requested to join {project.project_name}.",
                        type='request_received',
                        link=url_for('pending_requests')
                    )
                    db.session.add(notif)
            db.session.commit()
            return {'status': 'success', 'request_state': 'pending', 'message': 'Request sent successfully'}
        
    data = request.get_json() or {}
    req_msg = data.get('message', '').strip()
        
    new_request = MyJourneyRequest(my_journey_id=project_id, user_id=user_id, request_message=req_msg)
    db.session.add(new_request)
    
    # Notify Admin
    project = MyJourney.query.get(project_id)
    admin_users = User.query.filter_by(name=project.admin_name).all()
    for admin_user in admin_users:
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
            removed_users = User.query.filter_by(name=member_to_remove).all()
            for removed_user in removed_users:
                # 1. Clear existing pending/accepted request so "Request to Join" works again
                existing_request = MyJourneyRequest.query.filter_by(my_journey_id=journey_id, user_id=removed_user.id).first()
                if existing_request:
                    db.session.delete(existing_request)
                
                # 2. Add Notification
                notif = Notification(
                    recipient_id=removed_user.id,
                    message=f"You have been removed from the project <b>{journey.project_name}</b> by the admin.",
                    type='member_removed',
                    link=url_for('home')
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

@app.route('/generate_story/<int:project_id>', methods=['GET', 'POST'])
def generate_story(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    journey = MyJourney.query.get_or_404(project_id)
    
    # Permission Check: Only Admin can access this
    if journey.admin_name and journey.admin_name != session.get('user_name'):
         flash('Only the admin can generate a story.', 'danger')
         return redirect(url_for('my_journey_detail', journey_id=project_id))

    if request.method == 'POST':
        genre = request.form.get('genre')
        narration_style = request.form.get('narration_style')
        language = request.form.get('language')
        story_length = request.form.get('story_length')
        
        # --- Step 4: Fetch and format journey entries ---
        real_days = MyJourneyDay.query.filter_by(my_journey_id=journey.id).order_by(MyJourneyDay.journey_date, MyJourneyDay.id).all()
        
        # Calculate Day Number (Calendar based, matching the detail page logic)
        dropdown_start_date = journey.project_date_time.date()
        calc_start_date = dropdown_start_date
        if real_days:
            first_entry_date = real_days[0].journey_date
            if first_entry_date < calc_start_date:
                calc_start_date = first_entry_date

        formatted_journey_entries = ""
        for day in real_days:
            delta = (day.journey_date - calc_start_date).days
            day_num = delta + 1
            formatted_journey_entries += f"Day {day_num}: {day.description}\n"
            
            
        # --- Collect Team Member Genders ---
        admin_user = User.query.filter_by(name=journey.admin_name).first()
        admin_gender = admin_user.gender if admin_user and admin_user.gender else "Unknown"
        
        team_members_info = ""
        if journey.members:
            member_names = [m.strip() for m in journey.members.split(',')]
            for mem_name in member_names:
                mem_user = User.query.filter_by(name=mem_name).first()
                mem_gender = mem_user.gender if mem_user and mem_user.gender else "Unknown"
                team_members_info += f"- {mem_name} ({mem_gender})\n"
        
        print(f"--- Fetched Journey Entries for Project {journey.id} ---\n{formatted_journey_entries}--------------------------------------------------")
        
        # --- Step 5: Story Length Handling ---
        length_instruction = ""
        if story_length == "Short":
            length_instruction = "150-200"
        elif story_length == "Medium":
            length_instruction = "400-600"
        elif story_length == "Detailed":
            length_instruction = "900-1200"
            
        # --- Step 6: Build AI Prompt ---
        ai_prompt = f"""Project Name: {journey.project_name}

Narration Style: {narration_style}

Admin: {journey.admin_name} ({admin_gender})

Team Members:
{team_members_info}
Language: {language}
Genre: {genre}
Story Length: {length_instruction} words

Journey Entries:
{formatted_journey_entries}

Instruction for AI:

1. Use ONLY the names listed in the Team Members section.

2. Use correct pronouns based on gender.

Example:
Raman → she/her
Bob → he/him

3. Do NOT assume gender from the name.

4. FIRST PERSON RULE

If narration style is FIRST PERSON:
The narrator is the admin.

Whenever the narrator speaks using "I", prefix the sentence with the admin name in brackets.

Example:

(Bob) I started working on the project structure.

5. THIRD PERSON RULE

If narration style is THIRD PERSON:
Do not use brackets.

Example:

Bob started designing the system.
Raman tested the feature.

6. Never invent new names.
7. DO NOT INVENT DIALOGUES

The AI must not create fictional conversations between team members.
Incorrect example:
"Bob said excitedly..."
Correct example:
Bob started working on the project structure.
Only describe actions that logically follow from the journey entries.

8. GENRE SHOULD ONLY AFFECT TONE

Genre should influence the tone of the storytelling but must not change the events.
Do not turn the story into a movie script.
Avoid lines such as: "Ek naya Bollywood chapter shuru hua..."
Instead focus on the development journey.

9. REDUCE FILLER STORYTELLING

Avoid long poetic descriptions that do not describe real actions.
Incorrect example: "Coding ki duniya mein kahaniyan likhi ja rahi thin..."
Correct example: Bob started setting up the backend and frontend structure for the project.
Every paragraph should mainly describe real work done in the project.

10. KEEP THE STORY GROUNDED IN THE PROJECT

The story should feel like a real project-building journey.
Focus on: planning, coding, testing, design decisions, feature implementation, collaboration.
Avoid turning the story into a fictional narrative.

11. IMPROVE COLLABORATION FLOW

Avoid repetitive patterns like: "Bob built a feature. Ramandeep tested it."
Instead describe collaboration naturally.
Example: Bob implemented the login system while Ramandeep tested different scenarios to ensure the authentication flow worked properly.

12. NO DAY NUMBERS OR DOCUMENTATION STYLE

Do NOT divide the story into "Day 1", "Day 2", etc.
Hide the day numbers completely and transition the timeline naturally.
Do not format the output like a changelog, list, or documentation. Write a continuous, flowing narrative.

13. KEEP LANGUAGE NATURAL AND PROFESSIONAL

If the language is Hinglish and genre is Bollywood:
- Maintain a highly professional developer tone.
- Do NOT use typical or dramatic Bollywood movie dialogues.
- Do NOT write overly dramatic or cheesy lines.
- Write naturally, integrating Hindi and English smoothly, as a real engineer would narrate their work.

14. KEEP THE STORY FOCUSED ON THE BUILDING PROCESS

The main focus should always remain on:
how the project idea started
how features were built
how the team collaborated
how the system evolved
"""
        print("\n--- FINAL PROMPT SENT TO GEMINI ---\n")
        print(ai_prompt)
        print("\n-----------------------------------\n")
        
        # --- Step 8: Check for existing story ---
        existing_story = GeneratedStory.query.filter_by(
            project_id=journey.id,
            genre=genre,
            narration_style=narration_style,
            language=language,
            story_length=story_length
        ).first()
        
        if existing_story:
            db.session.delete(existing_story)
            db.session.commit()
            
        try:
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                flash("AI Error: GOOGLE_API_KEY environment variable is not set.", "danger")
                return redirect(url_for('my_journey_detail', journey_id=project_id))
                
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=ai_prompt
            )
            generated_text = response.text
            
            # Save the generated story to the database
            new_story = GeneratedStory(
                project_id=journey.id,
                genre=genre,
                narration_style=narration_style,
                language=language,
                story_length=story_length,
                story_text=generated_text
            )
            db.session.add(new_story)
            db.session.commit()
            
            flash(f'Story successfully generated by AI!', 'success')
            return redirect(url_for('view_story', project_id=project_id, story_id=new_story.id))
            
        except Exception as e:
            print(f"AI Generation Error: {e}")
            error_message = str(e)
            
            # Check for common API errors to show better feedback
            if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message or "quota" in error_message.lower():
                flash('AI API Daily Quota Exceeded. Please try again tomorrow or update your API billing plan.', 'danger')
            else:
                flash(f'Error generating AI story: {error_message}', 'danger')
                
            return redirect(url_for('generate_story', project_id=project_id))
            
    # Render the generate story page for GET request
    return render_template('generate_story.html', journey=journey)


@app.route('/story/<int:project_id>')
def view_story(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    journey = MyJourney.query.get_or_404(project_id)
    
    # Get the specific story requested via query parameter, or get the latest one
    story_id = request.args.get('story_id')
    if story_id:
        story = GeneratedStory.query.get_or_404(story_id)
    else:
        # Default to the most recent generated story for this project
        story = GeneratedStory.query.filter_by(project_id=project_id).order_by(GeneratedStory.id.desc()).first_or_404()
        
    return render_template('story.html', journey=journey, story=story)

@app.route('/download_story_pdf/<int:story_id>')
def download_story_pdf(story_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    story = GeneratedStory.query.get_or_404(story_id)
    journey = MyJourney.query.get(story.project_id)
    
    # Permission Check (Matching view_story access if strict, though view_story doesn't strictly check admin here. Assuming if they can view it they can download it)
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
    styles.add(ParagraphStyle(name='CenterTitle', alignment=TA_CENTER, fontSize=18, spaceAfter=20, fontName='Helvetica-Bold'))
    
    StoryElements = []
    
    # Title
    StoryElements.append(Paragraph(f"Project Title: {journey.project_name}", styles['CenterTitle']))
    
    # Metadata
    meta_style = styles['Normal']
    StoryElements.append(Paragraph(f"<b>Language:</b> {story.language}", meta_style))
    StoryElements.append(Paragraph(f"<b>Genre:</b> {story.genre}", meta_style))
    StoryElements.append(Paragraph(f"<b>Narration Style:</b> {story.narration_style}", meta_style))
    StoryElements.append(Paragraph(f"<b>Story Length:</b> {story.story_length}", meta_style))
    StoryElements.append(Spacer(1, 20))
    
    # Story Content
    # We replace newlines with HTML breaks so ReportLab renders them as new lines
    story_text_html = story.story_text.replace('\n', '<br />')
    StoryElements.append(Paragraph(story_text_html, styles['Justify']))
    
    doc.build(StoryElements)
    
    buffer.seek(0)
    pdf_out = buffer.getvalue()
    buffer.close()
    
    response = make_response(pdf_out)
    response.headers['Content-Type'] = 'application/pdf'
    # Use project name in filename, sanitize a bit just in case
    safe_filename = "".join([c for c in journey.project_name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
    response.headers['Content-Disposition'] = f'attachment; filename="Story_{safe_filename}.pdf"'
    return response

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
        
        # Notify Admin
        admin_users = User.query.filter_by(name=project.username).all()
        for admin_u in admin_users:
             if admin_u.name != user_name:
                  notif = Notification(
                     recipient_id=admin_u.id,
                     message=f"{user_name} liked your project {project.project_description[:20]}...",
                     type='like',
                     link=url_for('journey_detail', project_id=project.id)
                 )
                  db.session.add(notif)
        
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
        
        # Notify Admin
        admin_users = User.query.filter_by(name=project.username).all()
        for admin_u in admin_users:
             if admin_u.name != user_name:
                  notif = Notification(
                     recipient_id=admin_u.id,
                     message=f"{user_name} commented on {project.project_description[:20]}...",
                     type='comment',
                     link=url_for('journey_detail', project_id=project.id) + '#commentsBtn'
                 )
                  db.session.add(notif)
                  
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
        admin_users = User.query.filter_by(name=journey.admin_name).all()
        for admin_user in admin_users:
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
        admin_users = User.query.filter_by(name=journey.admin_name).all()
        for admin_user in admin_users:
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
        admin_users = User.query.filter_by(name=journey.admin_name).all()
        for admin_user in admin_users:
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
        admin_users = User.query.filter_by(name=journey.admin_name).all()
        for admin_user in admin_users:
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
        admin_users = User.query.filter_by(name=journey.admin_name).all()
        for admin_user in admin_users:
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
        admin_users = User.query.filter_by(name=journey.admin_name).all()
        for admin_user in admin_users:
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
        admin_users = User.query.filter_by(name=journey.admin_name).all()
        for admin_user in admin_users:
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
        admin_users = User.query.filter_by(name=journey.admin_name).all()
        for admin_user in admin_users:
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
