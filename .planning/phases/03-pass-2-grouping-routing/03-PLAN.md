---
objective: "Implement Routing Logic and Update Organizer"
wave: 3
depends_on: [2]
files_modified:
  - src/processing/routing.py
  - src/llm/llm.py
  - src/processing/organizer.py
  - tests/test_routing.py
autonomous: true
requirements:
  - GRP-08
  - GRP-09
  - GRP-10
  - GRP-11
  - GRP-12
  - GRP-13
---

# Plan 3: Routing Logic and Organizer Update

## Objective
Implement the 13-folder routing logic, handle LLM fallback for multi-match categories, and update the file organizer to synthesize the final file names (`YYYY-MM-DD - عنوان.pdf`) and split the documents physically using `split.py`.

## Tasks

```xml
<task>
  <action>
    Create `src/processing/routing.py`.
    Define `FOLDER_ROUTING: dict[str, list[str]]` mapping the 13 hardcoded folders to categories as specified in `03-RESEARCH.md` (e.g. `"5_contract": ["contract"]`).
    Derive `CATEGORY_TO_FOLDERS`, `SINGLE_MATCH`, and `MULTI_MATCH` constants.
  </action>
  <read_first>
    - .planning/phases/03-pass-2-grouping-routing/03-RESEARCH.md
  </read_first>
  <acceptance_criteria>
    - `src/processing/routing.py` exists with the 13 folder names and mappings.
    - `SINGLE_MATCH` contains categories like "contract", "pictures", "id_cards", "utility_bills".
    - `MULTI_MATCH` contains "forms", "letters", "others".
  </acceptance_criteria>
</task>

<task>
  <action>
    Add `route_document(self, category: str, content_explanation: str, allowed_folders: list[str]) -> str` to `LLMClient` in `src/llm/llm.py`.
    It should ask the LLM to choose ONE folder from `allowed_folders` based on the document's content.
    Return the chosen folder name.
  </action>
  <read_first>
    - src/llm/llm.py
  </read_first>
  <acceptance_criteria>
    - `route_document` is implemented.
    - Uses `_route_llm_call`.
  </acceptance_criteria>
</task>

<task>
  <action>
    Implement `determine_folder(category: str, content_explanation: str, llm_client: LLMClient) -> str` in `src/processing/routing.py`.
    If `category` is in `SINGLE_MATCH`, return the mapped folder directly.
    If `category` is in `MULTI_MATCH`, call `llm_client.route_document` passing the allowed folders.
    If the LLM call fails or returns an invalid folder, retry once.
    If it fails again, return the `"13_others"` fallback folder.
  </action>
  <read_first>
    - src/processing/routing.py
    - src/llm/llm.py
  </read_first>
  <acceptance_criteria>
    - `determine_folder` handles single-match directly.
    - Handles multi-match via `LLMClient.route_document`.
    - Correctly falls back to `"13_others"` on repeated failure.
  </acceptance_criteria>
</task>

<task>
  <action>
    Update `src/processing/organizer.py` `FileOrganizer.organize` method.
    Remove reliance on the declarative `config.routing` logic.
    For each `DocumentGroup` passed in, the folder path should already be provided via `DocumentGroup.folder_path` (set by pipeline).
    Format the filename:
    - If `category` is in `SINGLE_MATCH` and it's a 1-page document (like a single ID or picture), use `YYYY-MM-DD.pdf`.
    - Otherwise, use `YYYY-MM-DD - {brief_arabic_title}.pdf`.
    - If dates are missing, ensure we don't break; fallback to `"nodate"`. Use the first date in `doc.dates`.
    Sanitize the filename via `utils.sanitize_filename`.
    Keep the collision handling (`_2.pdf` suffix loop).
    Call `extract_pdf_segment` from `src/processing/split.py` to physically extract and compress the segment.
  </action>
  <read_first>
    - src/processing/organizer.py
    - src/core/utils.py
    - src/processing/split.py
  </read_first>
  <acceptance_criteria>
    - `organize` method correctly constructs the `YYYY-MM-DD - عنوان.pdf` name format.
    - Handles dateless documents.
    - Calls `extract_pdf_segment`.
  </acceptance_criteria>
</task>

<task>
  <action>
    Write tests in `tests/test_routing.py` covering `FOLDER_ROUTING` correctness, `determine_folder`, and the filename generation logic.
  </action>
  <read_first>
    - tests/conftest.py
  </read_first>
  <acceptance_criteria>
    - `pytest tests/test_routing.py -x -q` exits 0.
  </acceptance_criteria>
</task>
```

## Verification
- Run `pytest tests/test_routing.py -x` and ensure all pass.

## Must Haves
- **Truths**:
  - `FOLDER_ROUTING` dictionary contains exactly the 13 specified destination folders.
  - Multi-match categories use the LLM to choose an allowed folder.
  - `organizer.py` correctly constructs the filename schema `YYYY-MM-DD - brief_arabic_title.pdf`.

## Artifacts this phase produces
- `src.processing.routing.FOLDER_ROUTING` (constant dict)
- `src.processing.routing.CATEGORY_TO_FOLDERS` (constant dict)
- `src.processing.routing.SINGLE_MATCH` (constant set)
- `src.processing.routing.MULTI_MATCH` (constant set)
- `src.processing.routing.determine_folder` (function)
- `src.llm.llm.LLMClient.route_document` (method)
- `tests/test_routing.py` (test file)
