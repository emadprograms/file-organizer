---
objective: "Implement Routing Rules and LLM Route Call"
wave: 4
depends_on: [3]
files_modified:
  - tests/test_routing.py
  - src/processing/routing.py
  - src/llm/llm.py
autonomous: true
requirements:
  - GRP-08
  - GRP-09
  - GRP-10
must_haves:
  truths:
    - All 13 final folders are fully represented in the routing logic
    - Ambiguous documents are accurately resolved to a target folder via AI
  artifacts:
    - src.processing.routing.FOLDER_ROUTING
    - src.processing.routing.CATEGORY_TO_FOLDERS
    - src.processing.routing.SINGLE_MATCH
    - src.processing.routing.MULTI_MATCH
    - src.processing.routing.determine_folder
    - src.llm.llm.LLMClient.route_document
    - tests/test_routing.py
  key_links: []
---

# Plan 4: Routing Rules and LLM Route Call

## Objective
Implement the 13-folder routing logic and handle LLM fallback for multi-match categories.

## Tasks

```xml
<task>
  <files>
    - tests/test_routing.py
  </files>
  <action>
    Create `tests/test_routing.py`.
    Write tests covering `FOLDER_ROUTING` correctness (that it has exactly 13 folders) and `determine_folder` (both single and multi match with fallback to "13_others").
  </action>
  <verify>
    <automated>python -m pytest tests/test_routing.py -x</automated>
  </verify>
  <done>
    - Tests for routing utilities are defined and fail.
  </done>
</task>

<task>
  <files>
    - src/processing/routing.py
  </files>
  <action>
    Create `src/processing/routing.py`.
    Define `FOLDER_ROUTING: dict[str, list[str]]` mapping the 13 hardcoded folders to categories as specified in `03-RESEARCH.md` (e.g. `"5_contract": ["contract"]`).
    Derive `CATEGORY_TO_FOLDERS`, `SINGLE_MATCH`, and `MULTI_MATCH` constants.
  </action>
  <verify>
    <automated>python -c "from src.processing.routing import FOLDER_ROUTING; assert len(FOLDER_ROUTING) == 13"</automated>
  </verify>
  <done>
    - `src/processing/routing.py` exists with the 13 folder names and mappings.
    - `SINGLE_MATCH` contains categories like "contract", "pictures", "id_cards", "utility_bills".
    - `MULTI_MATCH` contains "forms", "letters", "others".
  </done>
</task>

<task>
  <files>
    - src/llm/llm.py
  </files>
  <action>
    Add `route_document(self, category: str, content_explanation: str, allowed_folders: list[str]) -> str` to `LLMClient` in `src/llm/llm.py`.
    It should ask the LLM to choose ONE folder from `allowed_folders` based on the document's content.
    Return the chosen folder name.
  </action>
  <verify>
    <automated>python -c "from src.llm.llm import LLMClient; assert hasattr(LLMClient, 'route_document')"</automated>
  </verify>
  <done>
    - `route_document` is implemented.
    - Uses `_route_llm_call`.
  </done>
</task>

<task>
  <files>
    - src/processing/routing.py
  </files>
  <action>
    Implement `determine_folder(category: str, content_explanation: str, llm_client: 'LLMClient') -> str` in `src/processing/routing.py`.
    If `category` is in `SINGLE_MATCH`, return the mapped folder directly.
    If `category` is in `MULTI_MATCH`, call `llm_client.route_document` passing the allowed folders.
    If the LLM call fails or returns an invalid folder, retry once.
    If it fails again, return the `"13_others"` fallback folder.
  </action>
  <verify>
    <automated>python -m pytest tests/test_routing.py::test_determine_folder -x</automated>
  </verify>
  <done>
    - `determine_folder` handles single-match directly.
    - Handles multi-match via `LLMClient.route_document`.
    - Correctly falls back to `"13_others"` on repeated failure.
  </done>
</task>
```
