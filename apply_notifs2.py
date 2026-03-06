import re

with open("app.py", "r", encoding='utf-8') as f:
    content = f.read()

# 1. request_join_project
content = content.replace(
    'message=f"<b>{session[\'user_name\']}</b> requested to join <b>{project.project_name}</b>.",',
    'message=f"{session[\'user_name\']} requested to join {project.project_name}.",'
)
# Routing is already pending_requests

# 2. accept_request
content = content.replace(
    'message=f"Your request to join <b>{journey.project_name}</b> was accepted!",',
    'message=f"Your request to join {journey.project_name} was accepted.",'
)

# 3. decline_request
content = content.replace(
    'message=f"Your request to join <b>{journey.project_name}</b> was declined.",',
    'message=f"Your request to join {journey.project_name} was declined.",'
)
content = content.replace(
    "type='request_declined',\n        link='#'",
    "type='request_declined',\n        link=url_for('my_journey_detail', journey_id=journey.id)"
)

# 4. remove_member
content = content.replace(
    'message=f"You have been removed from the project <b>{journey.project_name}</b> by the admin.",',
    'message=f"You have been removed from the project {journey.project_name} by the admin.",'
)
content = content.replace(
    "type='member_removed',\n                    link=url_for('notifications')",
    "type='member_removed',\n                    link=url_for('home')"
)

# 5. like_project
content = content.replace(
    'message=f"<b>{user_name}</b> liked your project <b>{project.project_description[:20]}...</b>.",',
    'message=f"{user_name} liked your project {project.project_description[:20]}...",'
)

# 6. comment_project
content = content.replace(
    "message=f\"<b>{user_name}</b> commented on your project <b>{project.project_description[:20]}...</b>.\",\n                type='comment',\n                link=url_for('journey_detail', project_id=project.id)",
    "message=f\"{user_name} commented on {project.project_description[:20]}...\",\n                type='comment',\n                link=url_for('journey_detail', project_id=project.id) + '#commentsBtn'"
)


# 7. like_my_journey, like_my_collab, like_home_journey, like_public_journey
content = content.replace(
    'message=f"<b>{user_name}</b> liked your project <b>{journey.project_name}</b>.",',
    'message=f"{user_name} liked your project {journey.project_name}.",'
)

# 8. comment_my_journey, comment_my_collab, comment_home_journey, comment_public_journey
# The target here: "Bob commented on air piano." (with period)
content = content.replace(
    "message=f\"<b>{user_name}</b> commented on <b>{journey.project_name}</b>.\",\n                type='comment',\n                link=url_for('my_journey_detail', journey_id=journey.id)",
    "message=f\"{user_name} commented on {journey.project_name}.\",\n                type='comment',\n                link=url_for('my_journey_detail', journey_id=journey.id) + '#commentsBtn'"
)
# And for collab
content = content.replace(
    "message=f\"<b>{user_name}</b> commented on <b>{journey.project_name}</b>.\",\n                type='comment',\n                link=url_for('my_collab_detail', collab_id=collab_id)",
    "message=f\"{user_name} commented on {journey.project_name}.\",\n                type='comment',\n                link=url_for('my_collab_detail', collab_id=collab_id) + '#commentsBtn'"
)

with open("app.py", "w", encoding='utf-8') as f:
    f.write(content)

print("Applied python fixes.")
