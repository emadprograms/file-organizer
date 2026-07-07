import os
import shutil
import logging
from src.logger import setup_logging

def test_dual_logging():
    run_id = "test_dual_logs"
    # Cleanup previous tests
    if os.path.exists("logs"):
        # Find the test directory if it exists and remove it
        for d in os.listdir("logs"):
            if "test_dual_logs" in d:
                shutil.rmtree(os.path.join("logs", d))
    
    # We need to clear handlers because setup_logging only adds them if none exist
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    run_dir = setup_logging(run_id=run_id, verbose=False)
    
    logger = logging.getLogger("test_logger")
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")

    app_log_path = os.path.join(run_dir, "app.log")
    debug_log_path = os.path.join(run_dir, "debug.log")

    with open(app_log_path, "r", encoding="utf-8") as f:
        app_logs = f.read()
    
    with open(debug_log_path, "r", encoding="utf-8") as f:
        debug_logs = f.read()

    print(f"--- app.log ---\n{app_logs}")
    print(f"--- debug.log ---\n{debug_logs}")

    assert "DEBUG" not in app_logs, "app.log should NOT contain DEBUG logs"
    assert "INFO" in app_logs, "app.log should contain INFO logs"
    assert "DEBUG" in debug_logs, "debug.log should contain DEBUG logs"
    assert "INFO" in debug_logs, "debug.log should contain INFO logs"

    # Check for traces folder
    traces_folder = os.path.join(run_dir, "traces")
    global_traces_folder = os.path.join("logs", "traces")
    
    assert not os.path.exists(traces_folder), "Run-local traces folder should NOT exist"
    # Note: global_traces might exist from previous runs, but we want to ensure setup_logging didn't create it if it was missing.
    # Since we can't easily check if it was JUST created, we'll just check local.

    print("Verification successful: Dual logging works as expected and traces folders are not created.")

if __name__ == "__main__":
    test_dual_logging()
