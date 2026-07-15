# Debug Session Resolution: Finalized PDF Missing

## Symptom
The user encountered an error during the finalization stage of the PDF organization pipeline:
```
Failed to create finalized PDF: no such file: 'pdfs\SAF F 2450_3 - خالد حمود ناصر حمود\SAF F 2450_3_categorized.pdf'
```
However, the script still successfully generated the split PDFs (40 of them) within that directory.

## Root Cause Analysis
During the `run_generation_pass` in `main.py`, the system attempts to create a unified TOC and finalize the document.
To do this, it first organizes the files by calling `organizer.organize(...)`.
Inside `organize(...)`, the system determines the `house_dir` (which includes the tenant's name). It then calls `ensure_target_directories` which tries to rename the original `target_dir` (e.g. `pdfs\SAF F 2450_3`) to `house_dir` (e.g. `pdfs\SAF F 2450_3 - خالد حمود ناصر حمود`).
If `house_dir` **already exists** (for example from a previous run), `ensure_target_directories` gracefully skips the rename step and does nothing. 

However, in `main.py`, the code blindly assumes that the original PDF file must now reside in `house_dir`:
```python
if not dry_run and target_dir != house_dir:
    pdf_path = house_dir / pdf_path.name
    target_dir = house_dir
```
If the directory wasn't renamed, the original `_categorized.pdf` file was still sitting at its original location! Because `main.py` updated `pdf_path` without actually moving the file on disk, the script crashed on `fitz.open(str(pdf_path))` later when it tried to add the Table of Contents.

## The Fix
I updated `main.py` to handle the file movement explicitly before updating the path pointers:
```python
    if not dry_run and target_dir != house_dir:
        import shutil
        new_pdf_path = house_dir / pdf_path.name
        # If the file hasn't been moved yet, move it now
        if pdf_path.exists() and not new_pdf_path.exists():
            shutil.move(str(pdf_path), str(new_pdf_path))
        elif not pdf_path.exists() and new_pdf_path.exists():
            # It was already moved/renamed by organizer
            pass
        pdf_path = new_pdf_path
        target_dir = house_dir
```
I also updated the cleanup logic to make sure `yaml` configuration files are properly moved into `.source_files` if the directory wasn't renamed by `ensure_target_directories`.
