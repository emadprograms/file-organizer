import os

replacements = {
    "from src.utils.fs": "from src.utils.fs",
    "import src.utils.fs as fs_utils": "import src.utils.fs as fs_utils",  # This might be tricky, better to just rely on regex or simple string replacement
    "src.utils.fs": "src.utils.fs",
    
    "from src.utils.logger": "from src.utils.logger",
    "import src.utils.logger as logger": "import src.utils.logger as logger",
    "src.utils.logger": "src.utils.logger",
    
    "src.tenant_config.tenants": "src.tenant_config.tenants",
    
    "src.grouping": "src.grouping",
    
    "src.timeline.dates": "src.timeline.dates",
    "src.timeline.phase": "src.timeline.phase",
    "src.core.models": "src.core.models",
    
    "src.timeline": "src.timeline",
    
    "src.routing": "src.routing",
    
    "src.pipeline.pipeline": "src.pipeline.pipeline",
    "src.pipeline.visualizer": "src.pipeline.visualizer",
    
    "src.pdf": "src.pdf",
}

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    for old, new in replacements.items():
        new_content = new_content.replace(old, new)
        
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

for root, _, files in os.walk('.'):
    if '.git' in root or '.venv' in root or '__pycache__' in root or '.agents' in root or '.planning' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            process_file(os.path.join(root, file))
