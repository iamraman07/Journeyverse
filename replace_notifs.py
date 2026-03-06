import re

with open("app.py", "r", encoding='utf-8') as f:
    content = f.read()

# Fix the escaped quotes issue
content = content.replace('message=f\\"{user_name}', 'message=f"{user_name}')
content = content.replace('{project.project_name}\\"', '{project.project_name}"')
content = content.replace('{journey.project_name}\\"', '{journey.project_name}"')

with open("app.py", "w", encoding='utf-8') as f:
    f.write(content)

print("Fix complete.")
