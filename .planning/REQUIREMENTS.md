# Milestone v1.2 Requirements

This document tracks the active requirements and goals for Milestone v1.2: Core Stabilization & Logic Overhaul.

## Category 1: OS, File I/O, and GUI Stability (IO)

- [ ] **IO-01 (Atomic Cache Saving):** The system must save the `.cache.json` file atomically (write to a temporary file, then rename) to prevent the entire cache from being corrupted or truncated to 0 bytes if the application is forcibly closed, crashes, or loses power during the write operation.
- [ ] **IO-02 (PDF Compression & Preservation):** The system must still copy the full original PDF into the house directory as requested. However, before processing and copying, it must compress the PDF to significantly reduce the massive file sizes, saving disk space without losing the full context file.
- [ ] **IO-03 (File Lock Release):** The `PdfIngestor` must explicitly call `doc.close()` on the PyMuPDF document after iterating through it, preventing the OS from holding a permanent file lock on the PDF (which currently blocks users from moving or deleting the file in Windows).
- [ ] **IO-04 (OS Path Sanitization):** The `_sanitize_filename` function must strip control characters like `\n` and `\r` from resident names. Currently, if the AI hallucinates a line break in a name, `os.makedirs` will violently crash the application when attempting to create an illegal Windows path.
- [ ] **IO-05 (GUI Telemetry Optimization):** The `poll_telemetry` function must be optimized to only render the most recent state in the Treeview instead of redundantly deleting and re-inserting hundreds of queued intermediate states. This prevents the severe UI freezing and flickering currently happening under heavy processing loads.
- [ ] **IO-06 (Safe Directory Overwrites):** The system must safely merge new output into existing house directories rather than using `shutil.rmtree` to destructively wipe out the entire folder (and all its contents) every time a new processing run occurs on the same house number.
- [ ] **IO-07 (Cache Validation Safety):** The system must wrap the cache loading logic in proper exception handling (e.g., `try/except ValidationError`) to safely handle outdated or manually modified cache files, preventing the entire pipeline from instantly crashing upon startup.

## Category 2: Core Timeline and Document Grouping Logic (LOGIC)

- [ ] **LOGIC-01 (Family Size Resilience):** The pipeline must allow Anchor documents (like Housing Contracts or Basic Details forms) containing more than 3 names to establish a new timeline. Currently, the `len(valid_mapped) <= 3` limit causes large families to be ignored and their documents orphaned to the "UNKNOWN" folder.
- [ ] **LOGIC-02 (Array Order Independence):** When an Anchor document lists multiple names (e.g., Husband and Wife), the grouping logic must correctly match the family to the current timeline regardless of which name the AI happened to output first in the array. Currently, it only checks `valid_mapped[0]`, causing immediate timeline hijacking if the spouse is listed first.
- [ ] **LOGIC-03 (Accurate Name Matching):** The word intersection math (`< 2` threshold) must be adjusted to correctly handle valid single-word Arabic names (e.g., "محمد"). Currently, single-word names mathematically cannot share 2 words, forcing them into duplicate, fragmented resident folders.
- [ ] **LOGIC-04 (Precise Date Grouping):** The pipeline must stop merging documents together indiscriminately. It must enforce strict date-matching during the grouping phase so that consecutive pages with different dates are recognized as separate documents.
- [ ] **LOGIC-05 (Prefix Document Rescue):** ID Cards (`PERSONAL_DETAILS`) and other non-anchor documents that appear at the very beginning of a scanned dossier must be able to initialize the timeline or be safely held until a timeline is established. Currently, because they aren't Anchor documents, they are permanently orphaned to the fallback folder.
- [ ] **LOGIC-06 (Non-Anchor Recipient Routing):** Non-anchor documents (like specific notifications or EWA letters) must respect the recipient name extracted by the AI. Currently, they are blindly forced into the `current_primary_tenant`'s folder even if the AI explicitly stated the letter belongs to a different family member.

## Category 3: Arabic Data Integrity and Output Formatting (ARABIC)

- [ ] **ARABIC-01 (Arabic String Safety):** The system must remove the destructive `.replace("ال", "")` logic. This crude string manipulation carves letters out of the middle of legitimate Arabic names (e.g., destroying "خالد" into "خاد"), causing random timeline splits and corrupt folder names.
- [ ] **ARABIC-02 (Zero-Padded Folder Sorting):** The 13 Arabic output folders must be zero-padded (e.g., `01. `, `02. `) instead of starting with raw numbers. Because Windows File Explorer uses lexicographical sorting, the current folders visually display out of chronological order (e.g., `1, 10, 11, 2, 3`), ruining the narrative flow.
- [ ] **ARABIC-03 (Dynamic Folder Generation):** The system must only generate Arabic category subfolders dynamically when a file actually needs to be written to them. Currently, it hardcodes the creation of all 13 empty folders for every single resident, creating massive visual clutter.

## Category 4: LLM Error Handling and Entity Resolution (LLM)

- [ ] **LLM-01 (Identity Preservation):** The `resolve_entities` LLM prompt in Pass 1.5 must correctly map and retain non-primary family member identities (like wives and children). Currently, it aggressively maps everyone to the primary tenant, permanently erasing their distinct identities from the output.
- [ ] **LLM-02 (Reliable Retries):** The pipeline must stop silently swallowing LLM extraction errors with bare `except Exception: pass` blocks. All exceptions must be caught, logged, and trigger the robust 429/500 retry logic instead of falling back to default/missing data.
- [ ] **LLM-03 (Other Letters Catch-All Fix):** The `other_letters` category must be removed from `NONE_EXPECTED_CATEGORIES`. This forces the pipeline to actively retry when the AI lazily dumps documents into `other_letters` without extracting any names, rather than blindly accepting the incomplete extraction.

## Category 5: Performance and Architecture (PERF/ARCH)

- [ ] **PERF-01 (Speed up extraction):** Drastically speed up Pass 1 Vision Extraction by moving it locally.
- [ ] **PERF-02 (Bypass rate limits):** Bypass Google API rate limits (global cooldown and 503 errors).
- [ ] **ARCH-01 (Local inference via LM Studio):** Implement local inference using Qwen2.5-VL-7B-Instruct via LM Studio.
- [ ] **ARCH-02 (Hybrid fallback):** Implement robust fallback logic to default to cloud models (e.g., gemini-4-26b) when local inference fails or times out.

## Future Requirements
None yet defined.

## Out of Scope
- **Saving Text Only:** The user requires the original visual format of the PDFs to be retained (via extraction and compression), rather than simply outputting raw OCR text.
