---
objective: "Implement Organizer Filename and Splitting Integration"
wave: 5
depends_on: [4]
files_modified:
  - src/processing/organizer.py
  - tests/test_routing.py
autonomous: true
requirements:
  - GRP-11
  - GRP-12
  - GRP-13
must_haves:
  truths:
    - Final documents are correctly assembled and physically split via PyMuPDF
    - Output filenames conform strictly to the required Arabic conventions
  artifacts:
    - src.processing.organizer.FileOrganizer
  key_links: []
---

# Plan 5: Organizer Filename and Splitting Integration

## Objective
Update the file organizer to synthesize the final file names (`YYYY-MM-DD - عنوان.pdf`) and split the documents physically using `split.py`.

## Tasks

```xml
<task>
  <files>
    - tests/test_routing.py
  </files>
  <action>
    Add test to `tests/test_routing.py` for the filename generation logic we will add to `FileOrganizer`.
  </action>
  <verify>
    <automated>python -m pytest tests/test_routing.py -x</automated>
  </verify>
  <done>
    - Test for filename formatting is defined and fails.
  </done>
</task>

<task>
  <files>
    - src/processing/organizer.py
  </files>
  <action>
    Update `src/processing/organizer.py` `FileOrganizer.organize` method.
    Remove reliance on the declarative `config.routing` logic.
    For each `DocumentGroup` passed in, the folder path should already be provided via `DocumentGroup.folder_path` (set by pipeline).
    Format the filename:
    - If `category` is in `SINGLE_MATCH` and it's a 1-page document (like a single ID or picture), use `YYYY-MM-DD.pdf`.
    - Otherwise, use `YYYY-MM-DD - {brief_arabic_title}.pdf`.
    - If dates are missing, fallback to `"nodate"`. Use the first date in `doc.dates`.
    Sanitize the filename via `utils.sanitize_filename`.
    Keep the collision handling (`_2.pdf` suffix loop).
    Call `extract_pdf_segment` from `src/processing/split.py` to physically extract and compress the segment.
  </action>
  <verify>
    <automated>python -m pytest tests/test_routing.py::test_filename_generation -x</automated>
  </verify>
  <done>
    - `organize` method correctly constructs the `YYYY-MM-DD - عنوان.pdf` name format.
    - Handles dateless documents.
    - Calls `extract_pdf_segment`.
  </done>
</task>
```
