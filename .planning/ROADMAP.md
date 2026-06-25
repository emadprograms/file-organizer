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
2. The 13 category folders are generated dynamically (no empty folders) and prefixed with zero-padding (e.g., `01_`) so they sort correctly in Windows Explorer.
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

## Phase 7: Local Pass 1 Inference via Mac Mini M4

**Goal:** Drastically speed up the slowest bottleneck (Pass 1 Vision Extraction) and completely bypass Google API rate limits by moving the operation locally onto the Mac Mini M4 (16GB) using Qwen2-VL-7B-Instruct.

**Requirements Mapped:**

- `PERF-01`: Bypassing Cloud Rate Limits
- `PERF-02`: Zero-Cost Inference
- `ARCH-01`: Local MLX / llama.cpp Server Integration
- `ARCH-02`: Hardware-Accelerated Metal Processing

**Success Criteria:**

1. Setup a local server (via LM Studio, Ollama, or llama.cpp) running the quantized `Qwen2-VL-7B-Instruct` model on the Mac Mini.
2. Update the `src/llm.py` API router to point base Pass 1 extraction requests to the `http://localhost:.../v1` endpoint mimicking OpenAI's API.
3. Verify that the local model accurately reads Arabic from scanned PDFs without throwing out-of-memory (OOM) errors.
4. Measure and confirm that the local execution drastically reduces total processing time for the batch since there is no `global_cooldown` or `503 UNAVAILABLE` network throttling on Pass 1.

### Phase 07.3: Improve multi-page correspondence processing via Arabic footer pattern detection (INSERTED)

**Goal:** Drastically speed up processing by detecting multi-page correspondences and skipping page-by-page LLM extraction for the subsequent pages of the same document.
**Requirements**: 

- Detect Arabic pagination footers (e.g., "1 من 10 الصفحة" or "2 من 10 الصفحة") using pattern detection.
- Group the subsequent pages as part of the same section based on the total page count parsed from the footer.
- The main topic and category should be derived from the first page of the correspondence.
- Automatically skip LLM extraction for pages 2 to N of the same correspondence document, placing them in the same folder category as page 1.

**Depends on:** Phase 7
**Plans:** 0 plans

Plans:

- [ ] TBD (run /gsd-plan-phase 07.3 to break down)

### Phase 07.3.1: Provide LLM with OCR footer hints instead of skipping pages (INSERTED)

**Goal:** Modify Pass 1 to still call the LLM on every page, but pass any detected OCR pagination (e.g. "1 من 10") into the prompt so the LLM can make an informed decision on whether the page is a continuation, rather than blindly skipping pages.
**Requirements:**

- Do not skip the LLM execution for pages with footers.
- Use local Mac OCR to detect the footer.
- Pass the detected footer string to the LLM prompt.
- Allow the local LLM to output `is_continuation` based on this context.

**Depends on:** Phase 07.3
**Plans:** 1/1 plans complete

Plans:

- [x] 07.3.1-PLAN.md

- [x] TBD (run /gsd-plan-phase 07.3.1 to break down) (completed 2026-06-24)

### Phase 07.4: Harden Prompt for Document Detection (INSERTED)

**Goal:** Improve document detection by hardening the prompt with specific letter subject patterns, enabling the local LLM to accurately deduce the document type from the subject, and falling back to a larger model (e.g. Gemma 4 26b) when no subject is present.
**Requirements:**

- Always analyze the subject of the letter first.
- Allow the local LLM to guess the document type utilizing these specific patterns:
  - Subject is exactly "الموضوع : الوحدات السكنية" or mentions an "extension of stay" (e.g., تمديد الإقامة / السكن) -> `amar takhsees`. (STRICT DEFINITION: Must be an order from a higher authority to give the primary tenant a place to stay. Penalize false positives.)
  - If the word "الأشغال" (Ashgal) is present ANYWHERE, it MUST be maintenance. This includes temporary key handover forms for maintenance (do NOT put these in key_handover_form). Do NOT put inspection notices or reports here -> maintenance.
  - Notices of inspection, inspection reports, house visits, yellow papers with inspection details, and photographs -> inspection_pictures.
  - Subject contains "طلب" (request) and mentions modifying the house -> house modifications.
  - Contains "استمارة تسليم الوحدات السكنية التابعة لوزارة الداخلية" -> key handover form.
  - Looks like "الموضوع: الوحدة السكنية رقم ( 508 ) طريق 4411 مجمع 944 سافرة" or "حاب ( 13/19239) قم الحس" (e.g., has a meter number) -> EWA.
  - Subject is "الموضوع: وقف استقطاع بدل الانتفاع" -> allowance. (Does NOT contain "30 bd" or "60 bd").
  - Contains text for "rent deduction" (e.g., استقطاع الإيجار) or mentions deducting amounts like "30 bd" or "60 bd". If a tabular form mentions these amounts, it MUST be rent deduction and NEVER basic details -> rent deduction. (MUST contain the amount to disambiguate from allowance).
  - Contains "إشعار" or "اشعار" (notification) OR mentions the tenant vacating the house (إخلاء), refusing to vacate, extensions for vacating, or eviction -> notifications (do NOT put vacating/eviction notices in "other letters").
  - Basic vs Personal Details: `basic details` are strictly forms about a person. `personal details` refers to pictures of identity cards, passports, and other non-form documents related to the person and his family. If it is related to a person and his family but NOT a form, it is `personal details`. Allow the local LLM to handle this detection directly based on these definitions.
- If there is NO subject and it doesn't fit the strong patterns above, do NOT use the local LLM to guess blindly. Instead, fall back to a larger model (e.g., Gemma 4 26b) to detect the document, as it performs significantly better on nuanced text.
- Conduct stress testing to harden the prompts and validate detection logic.

**Depends on:** Phase 07.3
**Plans:** 1/1 plans complete

Plans:

- [x] 07.4-01-PLAN.md

### Phase 07.1: Compress output PDFs to ~35MB (80% quality) post-AI processing (INSERTED)

**Goal:** Compress the output PDFs after AI detection and file placement are done. We avoid compressing the PDF initially to retain 100% quality for AI extraction, but compress the final outputs down to ~35MB (retaining 80% quality) since human users don't need raw 400MB sizes.
**Requirements:**

- Wait until AI detection and file placement in folders is complete
- Compress large files (e.g., 400MB) to ~35MB (~80% quality retention)
- Leave initial extraction inputs uncompressed (100% quality) for the AI

**Depends on:** Phase 7
**Plans:** 1/1 plans complete

Plans:

- [x] 1-PLAN.md

- [ ] 07-01-PLAN.md

- [x] TBD (run /gsd-plan-phase 07.1 to break down) (completed 2026-06-24)

### Phase 07.2: Improve name grouping logic using local LLM (INSERTED)

**Goal:** Refactor name grouping logic to utilize the local LLM for semantic matching instead of relying strictly on exact string matching. This should be done carefully to ensure we don't break any existing program logic, maintaining exact matches as a fast-path fallback.
**Requirements**: 

- Implement semantic name matching via local Qwen2-VL / LLM
- Retain existing exact string matching as a fast path to ensure zero breakage
- Ensure family members group together correctly even with typos or slight name variations

**Depends on:** Phase 07.1
**Plans:** 1/1 plans complete

Plans:

- [x] 07-02-PLAN.md (completed 2026-06-24)

### Phase 07.5: Two-Pass Local Pipeline (INSERTED)

**Goal:** Completely eliminate local vision model reasoning failures by decoupling OCR and categorization. Use `qwen2.5vl:7b` strictly to extract raw Arabic text from the PDF pages, and use a reasoning text model (e.g. `llama3.1:8b` or DeepSeek) to process the raw text and return the strict JSON categorization.
**Requirements:**

- Implement a two-pass architecture in `src/llm.py` `classify_page()`.
- Pass 1 (Vision): Prompt `qwen2.5vl:7b` to simply transcribe all Arabic text from the image verbatim without attempting to classify it.
- Pass 2 (Reasoning): Prompt a text-only reasoning model (`llama3.1:8b`) with the transcribed text + the strict classification prompt, and return the 13-category JSON schema.
- Update tests to verify the two-pass architecture.

**Depends on:** Phase 07.4
**Plans:** 1/1 plans complete

Plans:

- [x] 07.5-01-PLAN.md

- [x] TBD (run /gsd-plan-phase 07.5 to break down) (completed 2026-06-24)

### Phase 07.5.1: Hybrid Cloud-First Vision Extraction with Local Overflow (INSERTED)

**Goal:** [Urgent work - to be planned]
**Requirements**: TBD
**Depends on:** Phase 7.5
**Plans:** 1/1 plans complete

Plans:

- [x] 01-PLAN.md

- [x] TBD (run /gsd-plan-phase 07.5.1 to break down) (completed 2026-06-25)

### Phase 07.5.2: Pass 1a Cloud-First Vision Extraction with Local Fallback (INSERTED)

**Goal:** Modify Pass 1a vision extraction to run cloud-first via Gemma with robust key rotation, falling back to local `qwen2.5vl:7b` only on Pass 1a rate limits without blocking other pipeline operations.
**Requirements**:

- Implement key-cycling retry loop in `extract_page` to handle transient failures/429s across multiple keys.
- Prevent page-by-page snapping oscillation between cloud and local modes during active cooldowns.
- Avoid class-wide/global rate-limiting cooldown blocks that freeze non-OCR tasks like name matching or entity resolution.
- Verify pipeline speed and accuracy on `508.pdf` (first 30 pages).

**Depends on:** Phase 07.5.1
**Plans:** 1/1 plans complete

Plans:

- [x] TBD (run /gsd-plan-phase 07.5.2 to break down) (completed 2026-06-25)

## Phase 8: Output Quality Review & Refinement

**Goal:** Analyze the output of the newly localized/optimized pipeline to identify classification mistakes, extraction anomalies, and grouping errors, and systematically implement fixes to improve overall accuracy.

**Requirements Mapped:**

- `QUAL-01`: Manual Output Audit & Error Logging
- `QUAL-02`: Edge-Case Discussion & Triage
- `QUAL-03`: Iterative Logic Refinement
- `QUAL-04`: Regression Testing

**Success Criteria:**

1. Review generated folders and identify specific instances where the LLM or Timeline grouping made a mistake.
2. Discuss the root cause of these mistakes with the User to determine the optimal fix (e.g., Prompt engineering, Python logic tweak, or OCR preprocessing).
3. Implement the fixes without breaking previously working edge cases.
4. Achieve a visually flawless output structure on the test batch.

## Phase 9: OS, File I/O, and UI Stabilization

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
