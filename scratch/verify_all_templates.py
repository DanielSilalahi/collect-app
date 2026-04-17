import jinja2
import os

template_dir = r"c:\Users\Daniel\Documents\Daniel\dev\random\col-app\backend\templates"
loader = jinja2.FileSystemLoader(template_dir)
env = jinja2.Environment(loader=loader)

for root, dirs, files in os.walk(template_dir):
    for file in files:
        if file.endswith(".html"):
            rel_path = os.path.relpath(os.path.join(root, file), template_dir).replace("\\", "/")
            try:
                env.get_template(rel_path)
            except jinja2.TemplateSyntaxError as e:
                print(f"Error in {rel_path}: {e}")
            except Exception as e:
                # Some might fail if they expect specific context, but syntax should be ok
                pass
