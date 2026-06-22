---
id: "03"
wave: 1
depends_on: []
autonomous: true
objective: "Build a Tkinter GUI to wrap the CLI"
files_modified:
  - "src/gui.py"
---

# Phase 3: Graphical User Interface

## 1. Create `src/gui.py`
Create a `Tkinter` application that provides a graphical interface for the File Categorizer.
- Add a text entry and "Browse" button for selecting the input PDF file.
- Add a text entry and "Browse" button for selecting the output directory.
- Add a scrolled text area to display processing logs.
- Add a "Run" button to execute the pipeline.
- Ensure the pipeline execution happens in a separate thread (using `threading.Thread`) so the GUI does not freeze during processing.
- Redirect standard output (`sys.stdout`) to the scrolled text area while the pipeline runs.

## 2. Update `src/main.py`
Modify `main.py` so that it launches the GUI by default if no CLI arguments are provided.
- If arguments (like `pdf_path`) are passed, run in CLI mode.
- If no arguments are passed, import and launch the `Tkinter` app from `src/gui.py`.

## 3. Automated Tests
Add `tests/test_gui.py` to ensure the GUI can be imported and initialized without errors (mocking the `mainloop` call to avoid hanging the test runner).
