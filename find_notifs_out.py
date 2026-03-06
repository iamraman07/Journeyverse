import re
with open("app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

with open("notifs_out.txt", "w", encoding="utf-8") as out:
    for i, line in enumerate(lines):
        if "Notification(" in line:
            out.write(f"--- Line {i+1} ---\n")
            start = max(0, i - 5)
            end = min(len(lines), i + 5)
            for j in range(start, end):
                prefix = ">> " if j == i else "   "
                out.write(f"{prefix}{j+1}: {lines[j].rstrip()}\n")
