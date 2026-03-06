import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    text = f.read()

# 1. request_join_project
old_req1 = """    if existing_request:
        return {'status': 'success', 'request_state': existing_request.status, 'message': 'Request already exists'}"""

new_req1 = """    if existing_request:
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
            return {'status': 'success', 'request_state': 'pending', 'message': 'Request sent successfully'}"""

text = text.replace(old_req1, new_req1)

old_req2 = """    # Notify Admin
    project = MyJourney.query.get(project_id)
    admin_user = User.query.filter_by(name=project.admin_name).first()
    if admin_user and admin_user.id != session['user_id']:
        notif = Notification(
            recipient_id=admin_user.id,
            message=f"{session['user_name']} requested to join {project.project_name}.",
            type='request_received',
            link=url_for('pending_requests')
        )
        db.session.add(notif)"""

new_req2 = """    # Notify Admin
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
            db.session.add(notif)"""

text = text.replace(old_req2, new_req2)

# 3. like_project
old_like = """        # Notify Admin
        admin_user = User.query.filter_by(name=project.username).first()
        if admin_user and admin_user.name != user_name:
             notif = Notification(
                recipient_id=admin_user.id,
                message=f"{user_name} liked your project {project.project_description[:20]}...",
                type='like',
                link=url_for('journey_detail', project_id=project.id)
            )
             db.session.add(notif)"""

new_like = """        # Notify Admin
        admin_users = User.query.filter_by(name=project.username).all()
        for admin_u in admin_users:
             if admin_u.name != user_name:
                  notif = Notification(
                     recipient_id=admin_u.id,
                     message=f"{user_name} liked your project {project.project_description[:20]}...",
                     type='like',
                     link=url_for('journey_detail', project_id=project.id)
                 )
                  db.session.add(notif)"""

text = text.replace(old_like, new_like)

# 4. comment_project
old_comment = """        # Notify Admin
        admin_user = User.query.filter_by(name=project.username).first()
        if admin_user and admin_user.name != user_name:
             notif = Notification(
                recipient_id=admin_user.id,
                message=f"{user_name} commented on {project.project_description[:20]}...",
                type='comment',
                link=url_for('journey_detail', project_id=project.id) + '#commentsBtn'
            )
             db.session.add(notif)"""

new_comment = """        # Notify Admin
        admin_users = User.query.filter_by(name=project.username).all()
        for admin_u in admin_users:
             if admin_u.name != user_name:
                  notif = Notification(
                     recipient_id=admin_u.id,
                     message=f"{user_name} commented on {project.project_description[:20]}...",
                     type='comment',
                     link=url_for('journey_detail', project_id=project.id) + '#commentsBtn'
                 )
                  db.session.add(notif)"""

text = text.replace(old_comment, new_comment)

# 5. like_my_journey & like_my_collab & like_home_journey & like_public_journey
old_like_journey = """        # Notify Admin
        admin_user = User.query.filter_by(name=journey.admin_name).first()
        if admin_user and admin_user.name != user_name:
             notif = Notification(
                recipient_id=admin_user.id,
                message=f"{user_name} liked your project {journey.project_name}.",
                type='like',
                link=url_for('my_journey_detail', journey_id=journey.id)
            )
             db.session.add(notif)"""

new_like_journey = """        # Notify Admin
        admin_users = User.query.filter_by(name=journey.admin_name).all()
        for admin_u in admin_users:
             if admin_u.name != user_name:
                  notif = Notification(
                     recipient_id=admin_u.id,
                     message=f"{user_name} liked your project {journey.project_name}.",
                     type='like',
                     link=url_for('my_journey_detail', journey_id=journey.id)
                 )
                  db.session.add(notif)"""

text = text.replace(old_like_journey, new_like_journey)

# 6. comment_my_journey & comment_my_collab & comment_home_journey & comment_public_journey
old_comment_journey = """        # Notify Admin
        admin_user = User.query.filter_by(name=journey.admin_name).first()
        if admin_user and admin_user.name != user_name:
             notif = Notification(
                recipient_id=admin_user.id,
                message=f"{user_name} commented on {journey.project_name}.",
                type='comment',
                link=url_for('my_journey_detail', journey_id=journey.id) + '#commentsBtn'
            )
             db.session.add(notif)"""

new_comment_journey = """        # Notify Admin
        admin_users = User.query.filter_by(name=journey.admin_name).all()
        for admin_u in admin_users:
             if admin_u.name != user_name:
                  notif = Notification(
                     recipient_id=admin_u.id,
                     message=f"{user_name} commented on {journey.project_name}.",
                     type='comment',
                     link=url_for('my_journey_detail', journey_id=journey.id) + '#commentsBtn'
                 )
                  db.session.add(notif)"""

text = text.replace(old_comment_journey, new_comment_journey)

with codecs.open('app.py', 'w', 'utf-8') as f:
    f.write(text)

print("Replacement Complete")
