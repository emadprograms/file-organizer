import os
import re

replacements = {
    "organize.py": "main.py",
    "src.organize": "src.main"
}

for root, _, files in os.walk('.'):
    if '.git' in root or '.venv' in root or 'node_modules' in root or '.agents' in root or 'build' in root or '__pycache__' in root:
        continue
    for file in files:
        if file.endswith('.py') or file.endswith('.md'):
            filepath = os.path.join(root, file)
            if "rename_script.py" in file:
                continue
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = content
                for old, new in replacements.items():
                    new_content = new_content.replace(old, new)
                    
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Updated {filepath}")
            except UnicodeDecodeError:
                pass
