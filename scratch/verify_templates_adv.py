import os
import re

template_dir = r"c:\Users\Daniel\Documents\Daniel\dev\random\col-app\backend\templates"

for root, dirs, files in os.walk(template_dir):
    for file in files:
        if file.endswith(".html"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                
                # Stack to track open blocks
                stack = []
                tokens = re.finditer(r"\{%\s*(block|endblock)\s*(\w+)?\s*%\}", content)
                
                for match in tokens:
                    tag = match.group(1)
                    name = match.group(2)
                    
                    if tag == "block":
                        stack.append((name, match.start()))
                    else:
                        if not stack:
                            print(f"Error in {file}: Extra endblock at position {match.start()}")
                        else:
                            start_name, _ = stack.pop()
                            if name and start_name and name != start_name:
                                print(f"Warning in {file}: Endblock name mismatch: {start_name} != {name}")
                
                if stack:
                    for name, pos in stack:
                        print(f"Error in {file}: Unclosed block '{name}' at position {pos}")
