import jinja2
import os

template_dir = r"c:\Users\Daniel\Documents\Daniel\dev\random\col-app\backend\templates"
loader = jinja2.FileSystemLoader(template_dir)
env = jinja2.Environment(loader=loader)

files = [
    "base.html",
    "dashboard.html",
    "customers/batches.html",
    "customers/upload_mapping.html",
    "customers/list.html"
]

for file in files:
    try:
        print(f"Checking {file}...")
        env.get_template(file)
        print("OK")
    except jinja2.TemplateSyntaxError as e:
        print(f"Error in {file}: {e}")
        print(f"Line: {e.lineno}")
        print(f"Message: {e.message}")
    except Exception as e:
        print(f"Error in {file}: {e}")
