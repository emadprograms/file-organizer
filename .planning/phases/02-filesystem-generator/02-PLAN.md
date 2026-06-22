# Phase 2: Filesystem Generator — PLAN

**Phase:** 02-filesystem-generator
**Created:** 2026-06-22 (Rev 2 — addresses review cycle 1 findings)
**Requirements:** SYS-01, SYS-02, SYS-03, SYS-04, SYS-05, SYS-06
**Context:** 02-CONTEXT.md (decisions D-01 through D-07)
**Reviews:** 02-REVIEWS.md (F-01 through F-14 addressed below)

## Goal

Orchestrate the full pipeline output (`list[DocumentGroup]`) into a structured folder hierarchy on disk and save sliced PDFs into the correct locations.

## Target Structure

```
output/                               ← --output arg (D-01)
└── {house_number}/                   ← created BY organize() (F-02 fix)
    ├── 1_{resident_name}/
    │   ├── 1_basic_details/
    │   ├── 2_personal_details/
    │   ├── ... (all 13, even if empty — D-06)
    │   └── 13_other_letters/
    ├── 2_{resident_name}/
    │   └── (same 13 subfolders)
    ├── amar_takhsees/                ← flat (D-03)
    └── house_letters/                ← flat (D-04)
```

---

## Tasks

### Task 1: Create `src/organizer.py` — Core Filesystem Generator

**File:** `src/organizer.py` (new)
**Requirements:** SYS-01, SYS-02, SYS-03, SYS-04, SYS-05, SYS-06
**Addresses:** F-02, F-03, F-04, F-05, F-06, F-07, F-08, F-09, F-12

Create the `FileOrganizer` class that takes a list of `DocumentGroup` objects and the source PDF path, then generates the entire directory structure with sliced PDFs.

**Implementation details:**

1. **`CATEGORY_FOLDERS` constant** — Ordered dict mapping `Category` enum values to numbered folder names:
   ```python
   CATEGORY_FOLDERS = {
       Category.BASIC_DETAILS: "1_basic_details",
       Category.PERSONAL_DETAILS: "2_personal_details",
       Category.AMAR_TAKHSEES: "3_amar_takhsees",
       Category.KEY_HANDOVER: "4_key_handover_form",
       Category.CONTRACT: "5_contract",
       Category.EWA_LETTERS: "6_ewa_related_letters",
       Category.RENT_DEDUCTION: "7_rent_deduction",
       Category.ALLOWANCE_DEDUCTION: "8_allowance_deduction",
       Category.NOTIFICATIONS: "9_notifications",
       Category.MAINTENANCE: "10_maintenance",
       Category.PICTURES: "11_pictures",
       Category.MODIFICATIONS: "12_modifications",
       Category.OTHER_LETTERS: "13_other_letters",
   }
   ```

2. **`_resolve_house_number(documents) -> str`** — **(F-06 fix):**
   - Collect ALL `house_number` values from every `DocumentGroup`.
   - Use **majority vote** (most common non-empty value) as the canonical house number.
   - If different values found, print a warning: `"⚠ Inconsistent house numbers detected: {values}. Using majority: {winner}"`
   - Fallback to `"unknown_house"` if all empty.

3. **`_build_resident_order(documents) -> list[tuple[int, str]]`** — **(F-03 fix):**
   - Scan documents in page order. Track first appearance of each unique `primary_tenant`.
   - **Explicitly filter out:** `"UNKNOWN"`, `"NONE"`, `""`, and any whitespace-only strings.
   - **Skip tenants whose documents are ALL `Category.AMAR_TAKHSEES`** — these people didn't live there.
   - Return an ordered list of `(index, tenant_name)` tuples — e.g., `[(1, "محمد السيد"), (2, "أحمد علي")]`.
   - **(D-02):** Index = first appearance order = chronological order.

4. **`_sanitize_filename(name, max_length=50) -> str`** — **(F-07 fix):**
   - Replace filesystem-illegal characters (`/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`) with `_`.
   - Strip leading/trailing whitespace. Collapse multiple underscores.
   - **Truncate to `max_length` characters** to mitigate Windows MAX_PATH (260 char limit).
   - Ensure truncation doesn't split a multi-byte UTF-8 character.

5. **`_generate_pdf_name(doc, category_counter, used_names) -> str`** — **(D-05, F-05 clarified):**
   - `category_value` = `doc.category.value` (e.g., `"basic_details"`, `"notifications"`).
   - If `doc.dates` is non-empty, use the first date: `"{date}_{category_value}.pdf"`
   - Otherwise, use a counter: `"{category_value}_{counter}.pdf"`
   - **Duplicate date handling (Task 3 edge case):** If the generated name is already in `used_names` set, append `_2`, `_3`, etc.
   - Sanitize the final filename via `_sanitize_filename()`.

6. **`organize(documents, source_pdf, output_base_dir) -> dict`** — Main method. **(F-02 fix: receives RAW output base dir, creates house_number subfolder internally):**

   **Phase A — Validation & Setup:**
   - **(F-08 fix):** If `documents` is empty, print `"⚠ No documents to organize. Exiting."` and return `{}`.
   - **(D-07):** Resolve `house_dir = output_base_dir / house_number`. If `house_dir` exists, delete with `shutil.rmtree()`, then recreate.
   - **(F-09):** All file operations use explicit `encoding='utf-8'` where applicable.

   **Phase B — Create ALL directories first (F-12 fix):**
   - **(SYS-01):** Create `house_dir`.
   - **(SYS-02, D-02):** For each resident in `_build_resident_order()`, create `house_dir / "{index}_{sanitized_name}/"`.
   - **(SYS-04, D-06):** Inside each resident folder, create ALL 13 subfolders (even if empty).
   - **(SYS-03, D-03):** Create `house_dir / "amar_takhsees/"`.
   - **(SYS-03, D-04):** Create `house_dir / "house_letters/"`.
   - Use `os.makedirs(path, exist_ok=True)` for all directory creation.

   **Phase C — Write PDFs (only after all dirs exist):**
   - Build a lookup: `resident_name -> folder_path` from the resident order.
   - Track `used_names` per target directory to handle duplicate filenames.
   - Track per-resident, per-category counters for counter-based naming.
   - For each `DocumentGroup`:
     - If `doc.category == Category.AMAR_TAKHSEES` → target = `house_dir / "amar_takhsees/"`
     - Elif `doc.primary_tenant` in (`"UNKNOWN"`, `"NONE"`, `""`) → target = `house_dir / "house_letters/"`
     - Else → look up resident folder → target = `resident_folder / CATEGORY_FOLDERS[doc.category]`
     - Generate filename via `_generate_pdf_name()`.
     - **(F-04 fix):** Call `extract_pdf_segment(str(source_pdf), doc.start_page, doc.end_page, str(target / filename))` — explicit `str()` conversion for both paths.
   - Print progress: `"  → {filename} (pages {start}-{end})"`

   **Phase D — Summary:**
   - Return a dict: `{str(output_path): (start_page, end_page)}` for verification.
   - Print: `"✓ Generated {N} PDFs across {R} residents in {house_dir}"`

---

### Task 2: Update `src/main.py` — CLI Arguments & Integration

**File:** `src/main.py` (modify)
**Requirements:** D-01
**Addresses:** F-02 (caller side), F-11

Replace the current hardcoded logic with proper CLI argument parsing and organizer integration.

**Implementation details:**

1. Add `argparse` with:
   - `pdf_path` (positional, required) — Path to the input PDF file.
   - `--output` / `-o` (optional, default=`"./output"`) — Base output directory. **(D-01)**

2. Remove the hardcoded `sample_pdf = "sample.pdf"` and the flat file dumping loop (lines 18-34).

3. New flow — **(F-02 fix: pass raw `args.output`, NOT `args.output / house_number`):**
   ```python
   documents = pipeline.process_pdf(args.pdf_path)
   organizer = FileOrganizer()
   summary = organizer.organize(documents, args.pdf_path, Path(args.output))
   ```

4. **(F-11 fix):** Use the returned `summary` dict for the final report:
   ```python
   print(f"\n{'='*50}")
   print(f"  House: {house_number}")
   print(f"  Residents: {num_residents}")
   print(f"  PDFs generated: {len(summary)}")
   print(f"  Output: {output_dir}")
   print(f"{'='*50}")
   ```

5. Keep the existing `sys.stdout.reconfigure(encoding='utf-8')` for Arabic console output. **(F-09)**

---

### Task 3: Handle Edge Cases in Resident Resolution

**File:** `src/organizer.py` (extend Task 1)
**Requirements:** SYS-02, SYS-03
**Addresses:** F-03, F-06, F-07, F-08

Harden the edge cases (these are integrated into Task 1 above but listed separately for verification):

1. **`NONE`/`UNKNOWN`/empty tenants filtered** from `_build_resident_order()` — never create resident folders for these. Their documents route to `house_letters/`. **(F-03)**

2. **Multiple documents in same category for same resident:**
   - Per-resident, per-category counter tracked in the PDF writing loop.
   - Counter used in `_generate_pdf_name()` when dates are absent.

3. **Duplicate dates in same category:**
   - `used_names` set per directory. If collision: append `_2`, `_3`, etc.

4. **Resident in both regular docs AND Amar Takhsees:**
   - `_build_resident_order()` excludes ONLY-amar-takhsees tenants.
   - If a tenant has mixed docs: they get a resident folder for non-amar docs. Their amar docs still route to `amar_takhsees/`.

5. **House number inconsistency:** Majority-vote logic with warning. **(F-06)**

6. **Long filenames on Windows:** Truncation to 50 chars in `_sanitize_filename()`. **(F-07)**

7. **Empty documents list:** Early-exit with warning message. **(F-08)**

---

### Task 4: Write Automated Tests

**File:** `tests/test_organizer.py` (new)
**Requirements:** Verification of SYS-01 through SYS-06
**Addresses:** F-10

Write automated tests using `pytest` with mock `DocumentGroup` objects:

1. **`test_basic_structure()`** — Given 3 DocumentGroups for 2 residents:
   - Assert house_number root folder created. **(SYS-01)**
   - Assert 2 numbered resident folders. **(SYS-02)**
   - Assert all 13 subfolders in each. **(SYS-04)**
   - Assert `amar_takhsees/` and `house_letters/` at root. **(SYS-03)**

2. **`test_resident_ordering()`** — Given documents where resident B appears on page 5 and resident A on page 10:
   - Assert B is `1_B` and A is `2_A`. **(D-02)**

3. **`test_amar_takhsees_routing()`** — Given AMAR_TAKHSEES category docs:
   - Assert PDFs land in `amar_takhsees/`, not in a resident folder. **(D-03, SYS-03)**

4. **`test_house_letters_routing()`** — Given docs with `primary_tenant="UNKNOWN"`:
   - Assert PDFs land in `house_letters/`. **(D-04)**

5. **`test_continuation_pages_merged()`** — Given a DocumentGroup spanning pages 5-8:
   - Assert a single PDF is created (not 4 separate ones). **(SYS-06)**

6. **`test_date_based_naming()`** — Given a doc with dates:
   - Assert filename contains the date. **(D-05)**

7. **`test_counter_fallback_naming()`** — Given a doc without dates:
   - Assert filename uses a counter. **(D-05)**

8. **`test_overwrite_behavior()`** — Run organize twice:
   - Assert second run produces clean output, not merged. **(D-07)**

9. **`test_unknown_tenant_filtered()`** — Given docs with `primary_tenant="UNKNOWN"`:
   - Assert no resident folder created for UNKNOWN. **(F-03)**

Use `tmp_path` pytest fixture for temporary output directories. Mock `extract_pdf_segment` to avoid needing real PDFs — verify it's called with correct args.

---

### Task 5: Integration Test with Real Data

**File:** No new files — run against `sample.pdf`
**Requirements:** All SYS-*

1. Run automated tests: `python -m pytest tests/test_organizer.py -v`
2. Run full pipeline: `python -m src.main sample.pdf --output ./test_output`
3. Verify the output structure:
   - House number folder exists at root.
   - Residents are numbered by first appearance.
   - All 13 subfolders exist in each resident folder.
   - `amar_takhsees/` and `house_letters/` exist at root level.
   - PDF files are correctly sliced and placed.
   - Filenames follow date / counter convention. **(D-05)**
4. Compare page ranges against existing flat `out_*.pdf` files.
5. Fix any issues found during testing.

---

### Task 6: Cleanup & Final Polish

**Files:** Root directory, `.gitignore`
**Requirements:** None (housekeeping)
**Addresses:** F-13, F-14

1. Remove the old `out_*.pdf` files from the root directory (Phase 1 test artifacts).
2. **(F-14 fix):** Update `.gitignore` to add:
   ```
   output/
   test_output/
   out_*.pdf
   *.cache.json
   ```
3. **(F-13):** Verify `src/organizer.py` works with the existing `python -m src.main` import pattern — no `__init__.py` changes needed since `src/` already works as a package.
4. Update `requirements.txt` if needed (unlikely — only stdlib `argparse`, `shutil`, `pathlib`).
5. Final end-to-end run to confirm clean output.

---

## Success Criteria (from ROADMAP.md)

- [ ] **SC-1:** Creates the correct double-sorted folder hierarchy (House → Person → 13 Categories).
- [ ] **SC-2:** "Amar Takhsees" and house-generic letters are successfully routed to root-level subfolders.
- [ ] **SC-3:** Combines continuous pages and saves them as a single sliced PDF in the correct category folder.

## Review Findings Resolution Matrix

| Finding | Severity | Resolution | Task |
|---------|----------|------------|------|
| F-02 | HIGH | `organize()` receives raw output dir, creates house_number internally | Task 1, Task 2 |
| F-01 | MEDIUM | Resolved by F-02 fix | Task 1, Task 2 |
| F-03 | MEDIUM | Explicit UNKNOWN/NONE/empty filter in `_build_resident_order()` | Task 1, Task 3 |
| F-04 | MEDIUM | Explicit `str()` conversion before `extract_pdf_segment()` | Task 1 |
| F-05 | LOW | Clarified: `category_value` = `doc.category.value` | Task 1 |
| F-06 | MEDIUM | Majority-vote house_number with warning | Task 1, Task 3 |
| F-07 | MEDIUM | `_sanitize_filename()` truncates to 50 chars | Task 1, Task 3 |
| F-08 | LOW | Early-exit with warning for empty documents | Task 1, Task 3 |
| F-09 | LOW | UTF-8 encoding noted, existing stdout fix preserved | Task 1, Task 2 |
| F-10 | MEDIUM | New Task 4: automated tests with pytest | Task 4 |
| F-11 | LOW | Summary dict wired to final report in main.py | Task 2 |
| F-12 | MEDIUM | Phase B (all dirs) before Phase C (all PDFs) | Task 1 |
| F-13 | LOW | Package compatibility verified | Task 6 |
| F-14 | LOW | Expanded .gitignore entries | Task 6 |

## Dependencies

- Phase 1 complete ✓ — `Pipeline.process_pdf()` returns `list[DocumentGroup]`
- `src/split.py` — `extract_pdf_segment()` available ✓
- `src/schemas.py` — `Category` enum and `DocumentGroup` dataclass available ✓
