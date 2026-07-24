import ast
from pathlib import Path

def test_main_py_has_no_dead_imports():
    """
    Verify that src/main.py does not contain dead imports for 'fitz' and 'json'.
    This satisfies the validation requirement for Phase 28.
    """
    main_py_path = Path(__file__).parent.parent / "src" / "main.py"
    
    with open(main_py_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(main_py_path))
        
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name not in ["fitz", "json"], f"Dead import found: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            assert node.module not in ["fitz", "json"], f"Dead import found: {node.module}"
