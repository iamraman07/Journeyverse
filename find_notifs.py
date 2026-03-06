import re
with open("app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "Notification(" in line:
        print(f"--- Line {i+1} ---")
        # print 5 lines before and 10 lines after
        start = max(0, i - 10)
        end = min(len(lines), i + 15)
        for j in range(start, end):
            prefix = ">> " if j == i else "   "
            print(f"{prefix}{j+1}: {lines[j].rstrip()}")
