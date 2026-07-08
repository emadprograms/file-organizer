---
wave: 2
depends_on:
  - 01-exceptions-and-sys-exit-PLAN.md
files_modified:
  - src/processing/split.py
autonomous: true
---

# Plan: PyMuPDF Compression

## Requirements
- REF-03

## Context
Refactor `compress_pdf` in `src/processing/split.py` to eliminate the `Pillow` dependency and the dynamic `pip install`. Use a PyMuPDF-only compression method. Ensure `fitz.open()` uses context managers to avoid resource leaks.

## Tasks

<task>
<read_first>
- src/processing/split.py
</read_first>
<action>
Modify `compress_pdf` to remove `PIL` / `Pillow` imports and the `subprocess.check_call` that dynamically installs `Pillow`.
Rewrite the image compression to use PyMuPDF exclusively. You can use `fitz.Pixmap` to shrink images:
`pix = fitz.Pixmap(doc, xref)`
`if pix.width > max_dim or pix.height > max_dim:`
`    pix.shrink(1) # shrinks by factor of 2`
`image_bytes = pix.tobytes("jpeg")`
Ensure `fitz.open()` is used as a context manager `with fitz.open(...) as doc:` throughout the file, including in `extract_pdf_segment`. CRITICAL: Ensure that the `with` block is completely exited (or `doc.close()` is called explicitly) BEFORE attempting any fallback file copies (e.g., `shutil.copy2`) or moving the physical file, to prevent Windows permission errors due to locked file handles.
</action>
<acceptance_criteria>
- `subprocess.check_call` for `pip install Pillow` is removed.
- `import PIL` or `from PIL` is removed.
- Image downscaling is performed using `fitz.Pixmap` or another built-in PyMuPDF mechanism.
- `with fitz.open` is used for document handles, and handles are closed before performing any fallback `shutil.copy` operations on the same file.
</acceptance_criteria>
</task>

## Artifacts this phase produces
- No new symbols created. Existing functions modified.

## Must Haves
### truths
- D-04: Refactor `src/processing/split.py` to use PyMuPDF-only compression and eliminate Pillow.
- The PyMuPDF document handles are safely managed using context managers.
- PDF extraction and compression executes successfully without external image libraries.

### prohibitions
- The codebase contains no references to Pillow or PIL.
- The codebase contains no subprocess.check_call for pip install Pillow.
