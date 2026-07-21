---
phase: 24
plan: 24-03
reviewer: internal-agent-pass-2
date: 2026-07-21
---

## Review Pass 2: 24-03-PLAN.md (Gap Closure)

### Findings

#### blocker 1: `area_id` and `house_id` Extraction in `finalize()`
**Section:** Task 4, Step 1 & 4
**Issue:** The plan says to rewrite `finalize()` from scratch, but fails to explicitly retain the existing logic that robustly extracts `area_id` and `house_id` from the filename. The current `finalize()` method matches the filename against directory names in `areas_root` (e.g., `clean_name.startswith(a.name + " ")`) to handle areas with spaces (like "Safra D"). If the executor rewrites this from scratch without knowing this trick, they might use naive `.split(" ")` or `parse_filename_syntax`, which will fail on spaces.
**Recommendation:** Explicitly instruct the executor in Task 4 to retain the existing prefix-matching loop logic from the old `finalize()` method to correctly extract `area_id` and `house_id` from the `clean_name` before determining the target directory.

#### blocker 2: Page Index Offset for Master JSONs
**Section:** Task 4, Step 7
**Issue:** `finalize()` appends the incoming PDF pages to the master `{house_id}_finalized.pdf`. However, the temporary JSONs (`_cleaned`, `_grouped`, `_routed`) have page indices (like `original_index`, `start_page`, and `end_page`) relative to the incoming PDF (e.g., starting at 0). If merged into the master `.source_files/` JSONs as-is, their page references will point to the beginning of the master document instead of the newly appended pages. Clicking a group in the UI would navigate to the wrong document.
**Recommendation:** Before appending the arrays to the master JSONs, `finalize()` must get the current page count of the master `{house_id}_finalized.pdf` (let's call it `N`). It must add `N` to the `original_index` in `_cleaned` pages, and add `N` to the `start_page` and `end_page` of all groups in `_grouped` and `_routed` so they correctly align with the master document.

#### blocker 3: Missing Document Metadata in Scenario 1
**Section:** Task 3, Step 5 (Scenario 1)
**Issue:** For "Scenario 1 (G or 1-13)", the plan suggests bypassing `_clean_documents` and `_group_documents` entirely to manually generate a single `DocumentGroup`. However, if `group == 'G'`, the plan says to "use LLM to route". The LLM routing function (`route_document`) strictly requires `category` and `brief_arabic_title`, which are populated by the cleaning and grouping passes. Creating a raw `DocumentGroup` without running these passes will cause the routing step to fail or fallback.
**Recommendation:** Do not bypass `_clean_documents` in Scenario 1. `propose()` should always run `_clean_documents` first. For Scenario 1, it should then manually create a single `DocumentGroup` by merging all the cleaned pages (ensuring it inherits `category` and `brief_arabic_title`), and then call the existing routing logic.

#### concern 4: Duplicate Tenant Timeline Resolution
**Section:** Task 3, Step 5 (Scenario 1)
**Issue:** The plan asks `propose()` to manually check `doc_date` against YAML timelines, handle overlaps (voting + LLM), and assign to matching timelines for Scenario 1. This duplicates the complex tenant resolution logic already present inside `Pipeline._route_documents`. Hand-rolling this logic in `propose()` is highly prone to bugs and divergence.
**Recommendation:** Refactor or reuse the existing tenant timeline resolution methods in `Pipeline` instead of instructing the executor to write it from scratch in `propose()`.

#### concern 5: File Rename and `process_inbox` Race Condition
**Section:** Task 2 & 3
**Issue:** While `process_inbox()` loops continuously, `propose()` is synchronous and can take minutes (due to LLM calls). The logic states that `process_inbox` cleans up `.tmp_{stem}` if the corresponding PDF is missing. The user might approve the file (`OK`) or delete it while `propose()` is running or just after it finishes. The current conditions seem to handle the known states, but the executor needs to be careful not to trigger `shutil.rmtree` on a `.tmp_` directory that is currently being populated by `propose()`.
**Recommendation:** Add a note in Task 2 to ensure that the cleanup logic checks if a directory is "stale" (e.g., unmodified for > 5 minutes) before deleting it, to prevent deleting active `.tmp_` folders.
