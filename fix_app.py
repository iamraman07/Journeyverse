import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Fix request_join_project
old_req = """    if existing_request:
        return {'status': 'success', 'request_state': existing_request.status, 'message': 'Request already exists'}"""

new_req = """    if existing_request:
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

text = text.replace(old_req, new_req)

# 2. Fix the initial request creation at the end of request_join_project
old_init_req = """    # Notify Admin
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

new_init_req = """    # Notify Admin
    project = MyJourney.query.get(project_id)
    admin_users = User.query.filter_by(name=project.admin_name).all()
    for admin_user in admin_users:
        if admin_user.id != session['user_id']:
            notif = Notification(
                recipient_id=admin_user.id,
                message=f"{session['user_name']} requested to join {project.project_name}.",
                type='request_received',
                link=url_for('pending_requests')
            )
            db.session.add(notif)"""

text = text.replace(old_init_req, new_init_req)


# General Notifications replacement logic
def replace_notif_block(text, prop_name):
    # Pattern to match
    pattern = re.compile(
        r'( +)admin_user = User\.query\.filter_by\(name=' + prop_name + r'\)\.first\(\)\n'
        r'\1if admin_user and admin_user\.name != user_name:\n'
        r'\1     notif = Notification\(\n'
        r'\1        recipient_id=admin_user\.id,\n'
        r'(.*?)\n'
        r'\1    \)\n'  # matches `        )` assuming indent is 4 less than Notification or equal to if
        r'\1     db\.session\.add\(notif\)',
        re.DOTALL
    )
    
    # We must be careful that `(.*?)` is non greedy but DOTALL can leap if not careful.
    # So we'll limit it to not include `admin_user = User`
    
    def replacer(match):
        indent = match.group(1)
        inner = match.group(2)
        if "admin_user = User.query.filter_by" in inner:
            return match.group(0) # fail safe
            
        res = (f"{indent}admin_users = User.query.filter_by(name={prop_name}).all()\n"
               f"{indent}for admin_user in admin_users:\n"
               f"{indent}    if admin_user.name != user_name:\n"
               f"{indent}         notif = Notification(\n"
               f"{indent}            recipient_id=admin_user.id,\n"
               f"{inner}\n"
               f"{indent}        )\n"
               f"{indent}         db.session.add(notif)")
        return res
    
    return pattern.sub(replacer, text)

text = replace_notif_block(text, "project.username")
text = replace_notif_block(text, "journey.admin_name")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("done script")
