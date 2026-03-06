import re
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_block = False
indent_amount = ""
for line in lines:
    m_admin = re.match(r'^( +)admin_user = User\.query\.filter_by\(name=(.*)\)\.first\(\)\s*$', line)
    if m_admin:
        indent_amount = m_admin.group(1)
        name_var = m_admin.group(2)
        new_lines.append(f"{indent_amount}admin_users = User.query.filter_by(name={name_var}).all()\n")
        new_lines.append(f"{indent_amount}for admin_user in admin_users:\n")
        in_block = True
        continue
    
    if in_block:
        if line.strip() == "":
             new_lines.append(line)
             continue
        
        curr_indent = len(line) - len(line.lstrip())
        if curr_indent <= len(indent_amount):
             in_block = False
             new_lines.append(line)
             continue
             
        if line.strip().startswith("if admin_user") and curr_indent > len(indent_amount):
             new_lines.append(f"{indent_amount}    {line.lstrip()}")
             continue
             
        new_lines.append("    " + line)
    else:
        new_lines.append(line)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("done")
