import glob

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    if 'from typing import ' in content:
        if ' Any' not in content:
            content = content.replace('from typing import ', 'from typing import Any, ')
    else:
        content = "from typing import Any\n" + content
        
    with open(filepath, 'w') as f:
        f.write(content)

files = (glob.glob('tests/test_*.py') + ['tests/conftest.py'])
for f in files:
    fix_file(f)

