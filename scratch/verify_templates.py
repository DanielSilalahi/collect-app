import os
import re

template_dir = r"c:\Users\Daniel\Documents\Daniel\dev\random\col-app\backend\templates"

for root, dirs, files in os.walk(template_dir):
    for file in files:
        if file.endswith(".html"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                blocks = len(re.findall(r"\{%\s*block\s+", content))
                endblocks = len(re.findall(r"\{%\s*endblock\s*%\}", content))
                if blocks != endblocks:
                    print(f"File: {file} - Blocks: {blocks}, Endblocks: {endblocks}")
