# Milestone v1.2 Roadmap

This roadmap breaks down the stabilization and refactoring goals into safe, testable phases, continuing the phase numbering from the previous milestone.

## Phase 5: Arabic Formatting & LLM Accuracy

**Goal:** Stop the pipeline from actively mutilating Arabic names, ensure output folders sort correctly, and force the LLM to preserve family identities instead of swallowing errors.

**Requirements Mapped:**
- `ARABIC-01`: Arabic String Safety
- `ARABIC-02`: Zero-Padded Folder Sorting
- `ARABIC-03`: Dynamic Folder Generation
- `LLM-01`: Identity Preservation
- `LLM-02`: Reliable Retries
- `LLM-03`: Other Letters Catch-All Fix

**Success Criteria:**
1. Names like "خالد" are preserved perfectly and not mutilated by the `.replace("ال", "")` logic.
2. The 13 category folders are generated dynamically (no empty folders) and prefixed with zero-padding (e.g., `01. `) so they sort correctly in Windows Explorer.
3. Wives and children retain their distinct identities during Entity Resolution instead of being mapped to the primary tenant.
4. Any Python exception thrown during LLM parsing triggers the formal retry loop instead of being silently swallowed.
5. `other_letters` classifications missing a resident name trigger a retry instead of being accepted blindly.

## Phase 6: Core Grouping & Timeline Logic

**Goal:** Overhaul the logic that groups pages into documents and assigns them to resident timelines, ensuring families stay together and documents aren't orphaned or hijacked.

**Requirements Mapped:**
- `LOGIC-01`: Family Size Resilience
- `LOGIC-02`: Array Order Independence
- `LOGIC-03`: Accurate Name Matching
- `LOGIC-04`: Precise Date Grouping
- `LOGIC-05`: Prefix Document Rescue
- `LOGIC-06`: Non-Anchor Recipient Routing

**Success Criteria:**
1. Anchor documents listing more than 3 names successfully establish a timeline instead of being dropped.
2. Anchor documents listing multiple names do not hijack the timeline just because a spouse was listed first in the array.
3. Single-word Arabic names match correctly without failing the 2-word intersection threshold.
4. Consecutive pages of the same category but different dates are safely split into separate PDFs.
5. ID cards (`PERSONAL_DETAILS`) at the front of a file properly initialize a timeline instead of being permanently orphaned to the fallback folder.
6. Non-anchor documents (e.g., Notifications) are placed in the specific recipient's folder rather than being forced into the primary tenant's folder.

## Phase 7: OS, File I/O, and UI Stabilization

**Goal:** Prevent data corruption, crashes, and OS locks by fixing how the system handles files, directories, and background telemetry.

**Requirements Mapped:**
- `IO-01`: Atomic Cache Saving
- `IO-02`: PDF Compression & Preservation
- `IO-03`: File Lock Release
- `IO-04`: OS Path Sanitization
- `IO-05`: GUI Telemetry Optimization
- `IO-06`: Safe Directory Overwrites
- `IO-07`: Cache Validation Safety

**Success Criteria:**
1. Aborting the process midway does not corrupt or zero out the `.cache.json` file.
2. The UI treeview updates smoothly without freezing during heavy PDF processing.
3. The original PDF is compressed and copied to the house folder instead of duplicating the massive original.
4. Users can successfully delete or move the input PDF immediately after processing (no PyMuPDF file locks).
5. Running the pipeline multiple times on the same house safely merges files instead of `rmtree` wiping the folder.
6. Hallucinated line breaks in resident names are stripped and do not crash the OS `makedirs` call.
