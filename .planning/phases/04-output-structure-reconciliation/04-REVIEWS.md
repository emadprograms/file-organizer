---
phase: 04
reviewers: [gemini, antigravity]
reviewed_at: 2026-07-05T07:29:00+03:00
plans_reviewed: [04-01-file-organizer.md, 04-02-pipeline-integration.md]
---

# Cross-AI Plan Review — Phase 4

## Gemini Review

# Review: Phase 4 Output Structure & Reconciliation

## Summary
The plan outlines a solid architectural approach to bridging the logical groupings from Pass 2 into a physical directory hierarchy, alongside robust state recovery (checkpointing) and safety checks (reconciliation). Decoupling `run_reconciliation` from `FileOrganizer` is a sound design choice. However, the plan glosses over critical data availability gaps regarding how tenant timelines are derived at the filesystem stage, and there's a risk of path resolution errors if `FileOrganizer` stops accepting a fully resolved base directory.

## Strengths
- **Clear separation of concerns:** Extracting `run_reconciliation` into a separate module-level function keeps `FileOrganizer` focused solely on filesystem operations.
- **Accurate interface design:** The shift for `organize()` to return a `per_page` list of relative output paths perfectly aligns with the required manifest structure described in D-07.
- **Resilient Pipeline:** The implementation of atomic writes and checkpoint cleanup safely enables resume-ability (`grouped.json`) without risking partial states.
- **Accurate Baseline:** The plan correctly honors the user's explicit override (D-04) to create topic subdirectories on-demand rather than eagerly pre-creating all 13 folders.

## Concerns
- **HIGH: Missing Tenant Timeline Aggregation:** 
  Task 1 asserts `FileOrganizer` will implement `{canonical_arabic_name} {year_start}-{year_end}/`. However, `DocumentGroup` (`src/core/schemas.py:12`) only contains `primary_tenant: str` and `dates: list[str]`. The overall tenant timeline is NOT stored on the `DocumentGroup` schema. `FileOrganizer` cannot determine a tenant's overall `year_start` and `year_end` from a single document segment; it must perform an initial aggregation pass across *all* `documents` to compute the min/max dates per tenant before creating directories.
- **HIGH: "Unassigned" Tenant Fragmentation:** 
  D-03 requires inferring the "Unassigned" folder's period from all unassigned pages. In the current codebase (`src/cleaning.py:512`), unassigned pages are dynamically tagged as `page.canonical_tenant = f"Unassigned ({month_str})"`. If `FileOrganizer` strictly iterates over `doc.primary_tenant`, it will fragment these into multiple different tenants (e.g., "Unassigned (2020-05)" and "Unassigned (2020-06)"). The organizer must explicitly normalize/strip these suffixes to group them into a single `غير محدد` tenant before aggregating their timeline.
- **MEDIUM: Base Directory Context Loss:** 
  Task 1 plans to "Rewrite FileOrganizer to accept house_id and use it to construct the output directory". Currently, `src/organize.py:121` constructs the full path (`args.target_dir / "output" / house_id`) and passes it as `output_base_dir` to `organizer.organize()`. If `FileOrganizer` only accepts `house_id`, it loses the `args.target_dir` context (e.g., `./pdfs/1273`) and risks incorrectly writing to `./output/{house_id}` in the current working directory.
- **LOW: Unnecessary Dependency on FOLDER_ROUTING:**
  Task 1 mentions using `FOLDER_ROUTING` to create topic subdirectories. But `doc.folder_path` is already fully resolved during `route_document` (Pass 2) and `src/processing/organizer.py:45` currently creates paths using `doc.folder_path` directly. Importing `FOLDER_ROUTING` into `FileOrganizer` is unnecessary.

## Suggestions
- Update Task 1 of `04-01-file-organizer.md` to explicitly mention an initial aggregation pass: iterate over all `documents` first to compute `(min_year, max_year)` for every unique `primary_tenant`.
- Add logic to Task 1 to intercept `primary_tenant` strings starting with "Unassigned", strip the month suffix, and group them as the singular "Unassigned" tenant for date aggregation.
- Instead of rewriting `FileOrganizer` to accept `house_id` exclusively, keep the `output_dir` parameter (which `src/organize.py` already resolves correctly) and pass `house_id` merely for use inside the manifest/reconciliation step.
- Drop the requirement for `FileOrganizer` to read `FOLDER_ROUTING`. Rely entirely on `doc.folder_path`.

## Risk Assessment
**HIGH** — While the pipeline mechanics (checkpoints, JSON manifests, and function wiring) are solid, the folder naming rules (timeline suffixes and Unassigned grouping) cannot be implemented as described without addressing the data aggregation gaps. The fragmentation of the Unassigned tenant due to `src/cleaning.py`'s month suffix will actively break the expected D-03 output behavior unless explicitly mitigated in `organizer.py`.

---

## Antigravity Review

# Cross-AI Plan Review: Phase 4 (Output Structure & Reconciliation)

## Summary
The implementation plans for Phase 4 (04-01 and 04-02) are well-structured and accurately capture the stringent user constraints regarding folder naming, checkpoint behavior, and reconciliation. The separation of `FileOrganizer`'s file-writing responsibility from the actual pipeline logic is maintained cleanly. However, there are a few minor logic overlaps with existing codebase routing and a potential risk around how the "total input pages" metric is calculated for the reconciliation audit.

## Strengths
- **Reconciliation Strictness:** Correctly enforces D-08 by requiring `RuntimeError` on page count mismatches, properly blocking the checkpoint cleanup. 
- **Checkpoint Lifecycle:** Integrates D-05 and D-06 beautifully by resuming from `grouped.json` and only deleting checkpoints upon a fully verified successful run, preventing data loss on failed splits.
- **Dependency Re-use:** Appropriately re-uses `extract_pdf_segment` from `src.processing.split` instead of re-implementing `pymupdf` logic in the organizer.
- **Directory Formatting:** Accurately formats the folder structures (including timeline suffix) using `utils.sanitize_filename` avoiding invalid characters.

## Concerns
- **MEDIUM Risk: Reconciliation Baseline.** The plan in `04-02` Task 2 instructs `main()` to call `run_reconciliation` with `total_input_pages`. If the agent derives this by using `len(cleaned_pages)` (from the JSON report), it assumes the preceding categorizer JSON never dropped a page. To strictly satisfy OUT-06 ("total pages in input PDF"), `total_input_pages` MUST be derived directly from the source PDF using `fitz.open(pdf_path).page_count`.
- **MEDIUM Risk: Duplicate Routing Logic.** In `04-01` Task 1, the plan says: `Create topic subdirectories on-demand only (D-04, OUT-03) using FOLDER_ROUTING (OUT-04)`. `FileOrganizer` does not need to (and shouldn't) import or use `FOLDER_ROUTING`. In Pass 2 (`src/processing/pipeline.py`), `route_document()` already sets `doc.folder_path` to the correct 13_folder target. `FileOrganizer` should strictly rely on the existing `doc.folder_path` field (as it does in `src/processing/organizer.py:45`) and just create the target dir if it doesn't exist.
- **LOW Risk: Unassigned Fallback Naming.** D-03 explicitly states: `or just غير محدد/ if all dates are null`. The plan in `04-01` Task 1 instructs the agent to implement `غير محدد {year_start}-{year_end}/` but omits the instruction for the fallback state when dates cannot be inferred, which will lead to `None-None` literal strings in the folder name.
- **LOW Risk: Inconsistent Checkpoint Paths.** The plan for `04-02` Task 1 references the path `output/checkpoints/grouped.json`. In the actual `organize.py` codebase, the `output` directory is resolved dynamically against `args.target_dir` (`output_json_path = args.target_dir / "output" / ...`). The plan should explicitly instruct the use of `args.target_dir / "output" / "checkpoints" / "grouped.json"`.

## Suggestions
- **Calculate Source Pages via PyMuPDF:** In `04-02` Task 2, instruct the agent to compute `total_input_pages` in `main()` by importing `fitz` and calling `fitz.open(pdf_path).page_count`. This ensures the reconciliation is anchored to physical PDF truth.
- **Simplify Organizer Task:** Modify `04-01` Task 1 to drop the reference to `FOLDER_ROUTING` and instead specify: "Create directories dynamically based entirely on `doc.folder_path`. If it doesn't exist, create it (satisfies on-demand D-04)."
- **Clarify Unassigned Edge Case:** Add the explicit instruction in `04-01` Task 1 to check for valid inferred periods and fallback to `غير محدد/` natively if none exist.
- **Align Paths:** Explicitly inform the agent in `04-02` Task 1 that the checkpoint path must be constructed using `args.target_dir`.

## Risk Assessment
**MEDIUM** 
The overall architecture is highly sound and maps well to the requested Phase boundary, but the potential discrepancy in calculating the baseline PDF page count poses a direct risk to the OUT-06 success criteria. Correcting the total page count logic and preventing `FileOrganizer` from needlessly importing the routing dictionaries will lower the risk to LOW.

---

## Consensus Summary

Both reviewers noted that `FileOrganizer` does not need to reference `FOLDER_ROUTING` directly, as the document objects already contain the fully resolved `folder_path`. They also flagged significant issues with how inputs and states are passed around, requiring fixes to ensure correct directory resolution, tenant date aggregation, and accurate page count validation.

### Agreed Strengths
- **Reconciliation Strictness:** The decoupling of `run_reconciliation` from the `FileOrganizer` logic is well-regarded, as is the enforcement of page count equalities via `RuntimeError`.
- **Checkpoint Resilience:** The handling of `grouped.json` and the deferred deletion of checkpoints strictly upon a fully verified successful run are strong design choices.
- **Accurate Interface Design:** Returning a `per_page` map aligns perfectly with the required JSON manifest schema.

### Agreed Concerns
- **MEDIUM: Unnecessary Dependency on FOLDER_ROUTING:** Both reviewers pointed out that `doc.folder_path` is already fully resolved from Pass 2. Rewriting `FileOrganizer` to import `FOLDER_ROUTING` is redundant and unnecessary.

### Divergent Views
- **Gemini Reviewer** highlighted crucial omissions in how the `FileOrganizer` extracts tenant timelines, noting that `DocumentGroup` lacks a global timeline and `FileOrganizer` must perform an initial aggregation pass to compute the overall min/max dates per `primary_tenant`. It also noted a fragmentation risk for the "Unassigned" bucket due to `src/cleaning.py` appending month strings (e.g., `Unassigned (2020-05)`). Finally, it caught an issue where relying exclusively on `house_id` for path resolution causes the loss of the `args.target_dir` context.
- **Antigravity Reviewer** identified a major risk regarding the `total_input_pages` calculation for the reconciliation manifest. It correctly pointed out that relying on the JSON report length is unsafe, and that `fitz.open(pdf_path).page_count` MUST be used directly on the source PDF. It also requested explicit handling of the `غير محدد/` fallback state when all dates are null, and raised a minor concern about ensuring checkpoint paths are explicitly derived from `args.target_dir`.
