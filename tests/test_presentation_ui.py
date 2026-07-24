from typing import Any
import pytest
from unittest.mock import patch
from src.presentation.ui import console, set_verbosity, vprint

def test_set_verbosity() -> None:
    """Verify that set_verbosity updates the internal _verbose state."""
    # Test enabling verbosity
    set_verbosity(True)
    from src.presentation.ui import _verbose
    assert _verbose is True

    # Test disabling verbosity
    set_verbosity(False)
    from src.presentation.ui import _verbose
    assert _verbose is False

def test_vprint_verbose_true() -> None:
    """Verify that vprint calls console.print when verbosity is enabled."""
    set_verbosity(True)
    with patch.object(console, 'print') as mock_print:
        vprint("Test message")
        mock_print.assert_called_once_with("Test message")

def test_vprint_verbose_false() -> None:
    """Verify that vprint does NOT call console.print when verbosity is disabled."""
    set_verbosity(False)
    with patch.object(console, 'print') as mock_print:
        vprint("Test message")
        mock_print.assert_not_called()
