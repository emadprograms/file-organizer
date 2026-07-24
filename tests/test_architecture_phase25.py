import pytest
from pathlib import Path

def test_core_ui_does_not_exist():
    """
    Phase 25 Architectural validation: ensure src/core/ui.py is removed.
    This fulfills the acceptance criteria that core/ no longer contains ui logic.
    """
    core_ui_path = Path(__file__).parent.parent / "src" / "core" / "ui.py"
    assert not core_ui_path.exists(), "src/core/ui.py should not exist. It moved to src/presentation/ui.py"

def test_core_ui_cannot_be_imported():
    """
    Phase 25 Architectural validation: ensure src.core.ui raises ImportError.
    """
    with pytest.raises(ImportError):
        import src.core.ui
