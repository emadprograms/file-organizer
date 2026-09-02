---
status: investigating
trigger: "There are lot of issues in the current milestone. clicking on the categories inside the catgories doesn't open the pdfs. the categories are not numbered like how it is in the folders. I want you to hunt for more issues. what other issues can you find. and the biggest issue that the tests are not fully developed. they don't catch these issues. so first things first. I want you to hunt of issues (frontend related only.)"
created: 2026-09-02
---

# Symptoms
- Expected behavior: Clicking on categories inside categories opens the PDFs. Categories are numbered like in folders. Tests should catch these issues.
- Actual behavior: Clicking doesn't open PDFs. Categories are not numbered. Tests are not fully developed.
- Error messages: None provided.
- Timeline: Current milestone.
- Reproduction: Interact with frontend categories.

# Current Focus
- hypothesis: There might be a routing or event handling issue in nested categories, and missing mapping for category numbers. The test suite lacks coverage for these UI interactions.
- next_action: gather initial evidence

# Evidence
- The `CategoryResponse` model (`src/api/models.py`) and the `list_categories` endpoint (`src/api/routes.py`) only return `tenant`, `name`, and `document_count`. They do not return the actual documents or their `vault_id`s.
- The frontend `renderCategories` function (`src/api/static/index.html`) renders each category as a static card with no click handlers (`onclick`). There is no UI functionality to expand a category or click it to view the PDFs within.
- The `list_categories` endpoint groups by `folder_path` or `category` from the `state.json`. In the state data, this value is usually the raw category name (e.g., `صيانة`) without the prefix numbers used in physical folder creation (`10_صيانة`). The prefix logic from `FOLDER_PREFIXES` in `src/routing/config.py` is not applied when serving these category names.
- The frontend tests in `tests/frontend/test_tabs.py` only verify that the category text and document count are visible (`expect(page.locator("#document-list")).to_contain_text("Category A")`). They lack any assertions related to expanding a category or clicking on PDFs within it.

# Eliminated
- It is not an issue with the actual filesystem numbering, as `reconcile/core.py` and `timeline/core.py` successfully apply the prefixes for physical directory names. The issue is purely on the API response formatting and frontend display.

# Resolution
- root_cause: 
  1. The API endpoint (`list_categories`) returns unnumbered category names because it extracts the raw `folder_path` without applying `FOLDER_PREFIXES`.
  2. The `CategoryResponse` only includes a document count and lacks the actual document data. Consequently, the frontend renders categories as static cards without any click events to list or open the contained PDFs.
  3. Tests do not verify any interactions within the Categories tab.
- fix: (Pending fix - Diagnosis only per user instruction)
- verification: N/A
- files_changed: None
