from rich.console import Console
import logging

# Initialize a global console object
console = Console()
_verbose = False

logger = logging.getLogger(f"file_organizer.{__name__}")

def set_verbosity(verbose: bool):
    """Sets the global UI verbosity flag."""
    global _verbose
    _verbose = verbose
    logger.debug(f"UI verbosity set to: {verbose}")

def vprint(*args, **kwargs):
    """
    Prints to the console only if verbosity is enabled.
    Used for detailed UI elements like trees, tables, and debug info.
    """
    if _verbose:
        console.print(*args, **kwargs)
