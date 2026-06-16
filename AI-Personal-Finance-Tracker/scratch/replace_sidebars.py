import os
import re

templates_dir = r"c:\Users\Bhushan\OneDrive\Desktop\finance tracker\AI-Personal-Finance-Tracker\templates"

for filename in os.listdir(templates_dir):
    if filename.endswith(".html") and filename != "sidebar.html":
        filepath = os.path.join(templates_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check if sidebar wrapper custom exists in this template
        if 'class="sidebar-wrapper-custom"' in content:
            new_content = re.sub(
                r'(?s)<aside class="sidebar-wrapper-custom" id="sidebarWrapper">.*?</aside>',
                r"{% include 'sidebar.html' %}",
                content
            )
            if new_content != content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Successfully replaced sidebar in {filename}")
            else:
                print(f"Regex didn't modify {filename}")
        else:
            print(f"No sidebar wrapper custom found in {filename}")
