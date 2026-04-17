import re

files = [
    r"c:\Users\Daniel\Documents\Daniel\dev\random\col-app\backend\templates\base.html",
    r"c:\Users\Daniel\Documents\Daniel\dev\random\col-app\backend\templates\customers\batches.html",
    r"c:\Users\Daniel\Documents\Daniel\dev\random\col-app\backend\templates\customers\upload_mapping.html"
]

for path in files:
    print(f"--- {path} ---")
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if "block" in line:
                print(f"{i}: {line.strip()}")
