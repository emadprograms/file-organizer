---
wave: 1
depends_on: []
files_modified:
  - "src/split.py"
  - "src/organizer.py"
autonomous: true
---

# Phase 07.1 Plan: Compress Output PDFs Post-AI Processing

## Goal
Compress the output PDFs after AI detection and file placement are done. We avoid compressing the PDF initially to retain 100% quality for AI extraction, but compress the final outputs down to ~35MB (retaining 80% quality) since human users don't need raw 400MB sizes.

## Tasks

```xml
<task>
  <id>add-compression-utility</id>
  <read_first>
    <file>src/split.py</file>
  </read_first>
  <action>
    Add a new `compress_pdf` function in `src/split.py`. This function will take an input PDF path and an output PDF path. It should use `ghostscript` (via `subprocess` calling `gs`) with arguments like `-dPDFSETTINGS=/ebook` or `-dPDFSETTINGS=/printer` to significantly compress the PDF file size (targeting ~80% visual quality, scaling ~400MB down to ~35MB) after it has been created. Include fallback logic to simply copy the file if `gs` is not installed or fails.
  </action>
  <acceptance_criteria>
    - `compress_pdf` function exists in `src/split.py` and can successfully reduce the size of a sample PDF without corrupting it.
    - Errors from the compression process (e.g. `gs` command not found) are caught safely and the original file is copied intact if compression fails.
  </acceptance_criteria>
</task>

<task>
  <id>compress-full-pdf-copy</id>
  <read_first>
    <file>src/organizer.py</file>
    <file>src/split.py</file>
  </read_first>
  <action>
    Modify the `organize` method in `src/organizer.py` where the full original PDF is copied to the house directory (`shutil.copy2(source_pdf, full_file_dest)`). Instead of blindly copying, call the new `compress_pdf` utility (imported from `src.split`) to save the compressed version directly to `full_file_dest`. If compression fails, fall back to `shutil.copy2`. This ensures that the massive ~400MB input PDF is compressed *only* after the AI has already finished its uncompressed inference.
  </action>
  <acceptance_criteria>
    - The copied full-context PDF inside the house directory is significantly smaller than the input `source_pdf` (assuming it has high-res images).
    - If `compress_pdf` fails or is unavailable, the fallback `shutil.copy2` runs successfully.
  </acceptance_criteria>
</task>

<task>
  <id>compress-extracted-segments</id>
  <read_first>
    <file>src/organizer.py</file>
    <file>src/split.py</file>
  </read_first>
  <action>
    Modify `extract_pdf_segment` in `src/split.py` to compress the segment before finalizing, or update the calling loop in `src/organizer.py` to compress the `target_path` after `extract_pdf_segment` finishes. Ensure the split PDF segments (e.g., individual category PDFs) are compressed using the `compress_pdf` utility. 
  </action>
  <acceptance_criteria>
    - The generated segment PDFs within the resident category folders are compressed compared to a raw `fitz` split extraction.
    - The total footprint of the output folder is minimized.
  </acceptance_criteria>
</task>
```

## Verification
- Run the pipeline on a large test PDF (e.g., 400MB). Verify that AI extraction proceeds successfully (100% quality) without OOM.
- After processing, inspect the destination house folder. The copied full-context PDF should be compressed (roughly ~35MB).
- The extracted segment PDFs should be visually legible (approx 80% quality) and smaller in file size than uncompressed equivalents.

## must_haves
- All AI extraction processes MUST use the original uncompressed PDF.
- The final copied PDF in the house folder MUST be compressed.
- Ghostscript or equivalent compression utility must be executed reliably with fallback mechanisms.

## Artifacts this phase produces
- Compressed full-context PDF outputs in the destination house directory.
- Compressed segment PDF outputs in the destination category subdirectories.
