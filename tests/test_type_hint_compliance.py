import ast
import os
import pytest

def test_no_legacy_type_hints():
    """
    Ensure that legacy typing.List and typing.Dict are not used in the codebase.
    Modern Python 3.9+ built-in generics (list, dict) should be used instead.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dirs_to_check = ['tests', 'src']
    
    violating_files = []
    
    for d in dirs_to_check:
        dir_path = os.path.join(project_root, d)
        if not os.path.exists(dir_path):
            continue
            
        for root, _, files in os.walk(dir_path):
            for file in files:
                if not file.endswith('.py'):
                    continue
                    
                file_path = os.path.join(root, file)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                try:
                    tree = ast.parse(content, filename=file_path)
                except SyntaxError:
                    continue
                    
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module == 'typing':
                            for alias in node.names:
                                if alias.name in ('List', 'Dict'):
                                    violating_files.append((file_path, node.lineno, f"Imported {alias.name} from typing"))
                    elif isinstance(node, ast.Attribute):
                        if isinstance(node.value, ast.Name) and node.value.id == 'typing':
                            if node.attr in ('List', 'Dict'):
                                violating_files.append((file_path, node.lineno, f"Used typing.{node.attr}"))

    if violating_files:
        msg = "Found legacy type hints (typing.List or typing.Dict):\n"
        for filepath, lineno, reason in violating_files:
            rel_path = os.path.relpath(filepath, project_root)
            msg += f"{rel_path}:{lineno} - {reason}\n"
        pytest.fail(msg)
