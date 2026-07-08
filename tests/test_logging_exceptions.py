import os
import logging
import pytest
from src.logger import setup_logging

def test_exception_logging_traceback(tmp_path):
    """
    Verify that logger.exception() captures the full stack trace in debug.log.
    """
    # Setup logging to a temporary directory
    run_id = "exception_test_run"
    # Since setup_logging modifies global logging state, we need to ensure a clean slate
    # if running in a pytest session.
    
    # Clear existing handlers to prevent duplicate logging
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    run_dir = setup_logging(run_id=run_id, verbose=True)
    
    # Use a logger from the file_organizer hierarchy
    logger = logging.getLogger("file_organizer.test_exceptions")
    
    # Trigger an exception and log it with logger.exception()
    try:
        1 / 0
        # This line should not be reached
    except ZeroDivisionError:
        logger.exception("A simulated division by zero error occurred")
    
    # Path to debug.log
    debug_log_path = os.path.join(run_dir, "debug.log")
    
    assert os.path.exists(debug_log_path), "debug.log was not created"
    
    with open(debug_log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Find the line containing the error message
    found_error_msg = False
    found_traceback = False
    
    for line in lines:
        # Since debug.log is JSONL, we need to check if the traceback is 
        # inside the 'message' or a separate field (depending on the JSONLFormatter)
        # The JSONLFormatter puts the exception info in the 'message' if it's 
        # stringified by logging, or could be separate.
        # Standard logging.exception() appends the traceback to the msg.
        
        if "A simulated division by zero error occurred" in line:
            found_error_msg = True
            # The traceback typically follows or is part of the same JSON record
            # if the formatter handles exc_info.
            
    # In the current JSONLFormatter, the traceback is included in the record.
    # The JSONLFormatter implementation might just be taking the formatted message.
    # Let's check for the standard Python traceback markers.
    
    # We'll search the whole file for the traceback string
    content = "".join(lines)
    if "Traceback (most recent call last):" in content:
        found_traceback = True
        
    assert found_error_msg, "Error message was not found in debug.log"
    assert found_traceback, "Stack trace was not found in debug.log"

if __name__ == "__main__":
    # This allows running the script directly
    # Mock setup for tmp_path if not run via pytest
    import shutil
    from pathlib import Path
    
    # Create a dummy tmp_path for example
    dummy_path = Path("logs/test_exceptions")
    dummy_path.mkdir(parents=True, exist_ok=True)
    
    # This would require patching src.logger.LOGS_DIR
    # But we'll run it via pytest for the proper tmp_path integration.
    print("Please run this test via 'pytest tests/test_logging_exceptions.py'")
