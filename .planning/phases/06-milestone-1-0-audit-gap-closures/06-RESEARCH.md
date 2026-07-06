# Phase 6: Milestone 1.0 Audit Gap Closures - Research

**Date:** 2026-07-05
**Goal:** Resolve integration gaps found in the v1.0 Milestone Audit to ensure full pipeline correctness across phase boundaries.

## 1. Anchor Category Mismatch (`src/processing/pipeline.py`)
- **Current State:** `pipeline.py` (around line 298) defines `ANCHOR_CATEGORIES = {"Basic Details Form", "Housing Contract", "Rent Deduction Notice"}`.
- **Problem:** This does not match the JSON report categories, which are `"contract", "forms", "id_cards"`.
- **Implementation:** Update the `ANCHOR_CATEGORIES` set in `pipeline.py` to match the JSON report format:
  ```python
  ANCHOR_CATEGORIES = {"contract", "forms", "id_cards"}
  ```

## 2. Proactive Creation of the 13 Topic Subdirectories
- **Current State:** In `src/processing/organizer.py`, topic subdirectories are created dynamically on-demand right before writing a document PDF (`os.makedirs(target_dir, exist_ok=True)`).
- **Problem:** Empty subdirectories are not created, violating the requirement to always generate all 13 folders per tenant.
- **Implementation:** In `FileOrganizer.organize()`, immediately after `tenant_folder_names` is populated, loop through each generated tenant folder name and the keys of `FOLDER_ROUTING` (imported from `src.processing.routing`). For each combination, generate the target path and proactively create the directory using `os.makedirs(..., exist_ok=True)`.

## 3. Unassigned Folder Naming Update
- **Current State:** In `organizer.py` (lines 66 & 72), the Unassigned folder is mapped to `"غير محدد {min_year}-{max_year}"` or `"غير محدد"`.
- **Problem:** Needs to map to `"غير مخصص (فترة مستنتجة)"` or `"غير مخصص"` to match the Arabic output structure accurately.
- **Implementation:**
  - If dates are available, set it to: `f"غير مخصص (فترة مستنتجة) {min_year}-{max_year}"`
  - If no dates are available, set it to: `"غير مخصص"`

## 4. Atomic File Writes for Checkpoints and Fallbacks
- **Current State:** `organize.py` and `organizer.py` use standard file open methods and manual `.tmp` file renaming for writing checkpoints (`output_json_path`, `grouped_checkpoint_path`) and manifests.
- **Implementation:** 
  - Import the existing `atomic_write` context manager from `src.fs_utils`.
  - Update `organize.py` (lines ~121 and ~150) and `organizer.py` (line ~171) to use this pattern:
    ```python
    from src.fs_utils import atomic_write
    ...
    with atomic_write(str(file_path)) as tmp_path:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(..., f)
    ```

## 5. Reconciliation Report Detailed Breakdown
- **Current State:** `organizer.py`'s `run_reconciliation` computes unaccounted pages and throws a `RuntimeError` if numbers don't match, but does not log a breakdown to the console.
- **Implementation:** At the end of `run_reconciliation()`, before the `RuntimeError` check, use `rich.table.Table` and `rich.console.Console` to print a cleanly formatted table displaying:
  - House ID
  - Total Input Pages
  - Total Output Pages
  - Output File Count
  - Unaccounted Pages
  - This ensures the details are visible whether reconciliation passes or fails.

## 6. Grouping LLM Prompt Reasoning Explicit Instruction
- **Current State:** `GROUPING_PROMPT` in `src/processing/grouping.py` implicitly relies on the JSON schema requesting a "reason", but the system prompt lacks explicit instruction.
- **Implementation:** Append a rule to the `CRITICAL RULES` section in `GROUPING_PROMPT`:
  `5. You MUST provide a "reason" string for every group explaining why you grouped these pages together, based on what you saw and didn't see.`

## 7. Direct-Routed Documents Single-Page Check
- **Current State:** `organizer.py` (line ~107) applies a date-only filename (`YYYY-MM-DD.pdf`) to all direct-routed documents.
- **Problem:** Multi-page direct-routed documents lose context when named date-only.
- **Implementation:** Update the condition to check if the document is only a single page long:
  ```python
  if doc.is_direct_routed and doc.start_page == doc.end_page:
      base_name = utils.sanitize_filename(f"{date_str}.pdf")
  else:
      # use title logic
  ```

## 8. 5-Consecutive Failure Tracking for Multi-Match LLM Routing
- **Current State:** `route_document` in `routing.py` has a local 2-attempt retry loop but lacks global tracking across multiple document evaluations.
- **Problem:** Requirement LLM-08 dictates skipping LLM calls after 5 consecutive failures.
- **Implementation:** 
  - Add a module-level variable `consecutive_routing_failures = 0` in `routing.py`.
  - Inside `route_document()`, immediately check if `consecutive_routing_failures >= 5`. If so, log a warning and return `"13_others", False` without calling the LLM.
  - On a successful LLM routing call, reset `consecutive_routing_failures = 0`.
  - If the LLM call fails all local attempts, increment `consecutive_routing_failures += 1`.
