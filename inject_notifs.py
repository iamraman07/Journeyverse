import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    text = f.read()

text = text.replace('\r\n', '\n')


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

# request_join_project init
old_req2 = """    new_request = MyJourneyRequest(my_journey_id=project_id, user_id=user_id, request_message=req_msg)
    db.session.add(new_request)
    db.session.commit()
    
    return {'status': 'success', 'request_state': 'pending', 'message': 'Request sent successfully'}"""

new_req2 = """    new_request = MyJourneyRequest(my_journey_id=project_id, user_id=user_id, request_message=req_msg)
    db.session.add(new_request)

    # Notify Admin
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

text = text.replace(old_req2, new_req2)


# 2. like_project
old_like = """        new_like = ProjectLike(project_id=project.id, user_name=user_name)
        db.session.add(new_like)
        project.likes += 1
        
    db.session.commit()"""

new_like = """        new_like = ProjectLike(project_id=project.id, user_name=user_name)
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
        
    db.session.commit()"""

text = text.replace(old_like, new_like)


# 3. comment_project
old_comment = """        new_comment = ProjectComment(project_id=project.id, user_name=user_name, comment_text=comment_text)
        db.session.add(new_comment)
        project.comments += 1
        db.session.commit()"""

new_comment = """        new_comment = ProjectComment(project_id=project.id, user_name=user_name, comment_text=comment_text)
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
                  
        db.session.commit()"""

text = text.replace(old_comment, new_comment)


# 4. like_my_journey (and others that share the model MyJourneyLike)
old_like_journey = """        new_like = MyJourneyLike(my_journey_id=journey.id, user_name=user_name)
        db.session.add(new_like)
        journey.likes += 1
        
    db.session.commit()"""

new_like_journey = """        new_like = MyJourneyLike(my_journey_id=journey.id, user_name=user_name)
        db.session.add(new_like)
        journey.likes += 1
        
        # Notify Admin
        admin_users = User.query.filter_by(name=journey.admin_name).all()
        for admin_u in admin_users:
             if admin_u.name != user_name:
                  notif = Notification(
                     recipient_id=admin_u.id,
                     message=f"{user_name} liked your project {journey.project_name}.",
                     type='like',
                     link=url_for('my_journey_detail', journey_id=journey.id)
                 )
                  db.session.add(notif)
                  
    db.session.commit()"""

text = text.replace(old_like_journey, new_like_journey)


# 5. comment_my_journey (and others that share the model MyJourneyComment)
old_comment_journey = """        new_comment = MyJourneyComment(my_journey_id=journey.id, user_name=user_name, comment_text=comment_text)
        db.session.add(new_comment)
        journey.comments += 1
        db.session.commit()"""

new_comment_journey = """        new_comment = MyJourneyComment(my_journey_id=journey.id, user_name=user_name, comment_text=comment_text)
        db.session.add(new_comment)
        journey.comments += 1
        
        # Notify Admin
        admin_users = User.query.filter_by(name=journey.admin_name).all()
        for admin_u in admin_users:
             if admin_u.name != user_name:
                  notif = Notification(
                     recipient_id=admin_u.id,
                     message=f"{user_name} commented on {journey.project_name}.",
                     type='comment',
                     link=url_for('my_journey_detail', journey_id=journey.id) + '#commentsBtn'
                 )
                  db.session.add(notif)
                  
        db.session.commit()"""

text = text.replace(old_comment_journey, new_comment_journey)


with codecs.open('app.py', 'w', 'utf-8') as f:
    f.write(text)

print(f"Inj completed. Checking replacements:")
print(f"admin_users: {text.count('admin_users')}")
