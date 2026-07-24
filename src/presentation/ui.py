from typing import Any
from rich.console import Console
import logging

# Initialize a global console object
console = Console()
_verbose = False

logger = logging.getLogger(f"file_organizer.{__name__}")

def set_verbosity(verbose: bool) -> None:
    """Sets the global UI verbosity flag.
    
    Args:
        verbose (bool): Whether to enable verbose output.
        
    Returns:
        None
    """
    global _verbose
    _verbose = verbose
    logger.debug(f"UI verbosity set to: {verbose}")

def vprint(*args: Any, **kwargs: Any) -> None:
    """Prints to the console only if verbosity is enabled.
    
    Used for detailed UI elements like trees, tables, and debug info.
    
    Args:
        *args: Positional arguments to pass to console.print.
        **kwargs: Keyword arguments to pass to console.print.
        
    Returns:
        None
    """
    if _verbose:
        console.print(*args, **kwargs)
