# Phase 3 Summary

## Tasks Completed
1. Created `src/gui.py` implementing a `Tkinter` application to wrap the CLI.
2. Added "Browse" functionality for selecting input PDF and output directory.
3. Added a separate thread to run the categorization pipeline so the GUI doesn't freeze.
4. Hooked `sys.stdout` into a scrolled text widget to show real-time progress.
5. Modified `src/main.py` to automatically launch the GUI if no command line arguments are passed, preserving CLI behavior if arguments are given.
