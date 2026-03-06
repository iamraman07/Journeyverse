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
        
        # If we reached a line that is dedented back to the original indent amount, we left the block
        # For example, `    db.session.commit()` is often dedented
        if curr_indent <= len(indent_amount):
             if line.strip().startswith("if admin_user"):
                 # Wait, `if admin_user` might have the EXACT SAME indent as `admin_user = `
                 # So we indent it by 4 spaces to put it inside the `for` loop
                 new_lines.append(f"{indent_amount}    {line.lstrip()}")
                 continue
             else:
                 # It's something else, so we left the block
                 in_block = False
                 new_lines.append(line)
                 continue
             
        # If we are inside the block, just add 4 spaces
        new_lines.append("    " + line)
    else:
        new_lines.append(line)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
    
print("done line by line")
