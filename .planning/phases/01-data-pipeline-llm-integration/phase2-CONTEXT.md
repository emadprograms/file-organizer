# Phase 2: Filesystem Generator - Context

**Gathered:** 2026-06-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Orchestrate the full pipeline output (`list[DocumentGroup]`) into a structured folder hierarchy on disk — house number → chronological residents → 13 category subfolders — and save sliced PDFs into the correct locations.

**Input:** `list[DocumentGroup]` from `Pipeline.process_pdf()` (each with `start_page`, `end_page`, `house_number`, `primary_tenant`, `category`, `dates`).
**Output:** A directory tree with correctly named and placed PDF files.

</domain>

<decisions>
## Implementation Decisions

### D-01: Output Location
- Configurable `--output` CLI argument, defaulting to `./output/{house_number}/`.
- If the argument is omitted, generate into `./output/` with the house number as the root subfolder.

### D-02: Resident Chronological Ordering
- Order residents by **first appearance in the PDF** (page order ≈ move-in order).
- The document is already roughly chronological, so this is the simplest and most reliable approach.
- Result: `1_FirstResident`, `2_SecondResident`, etc.

### D-03: Amar Takhsees Handling
- **Single shared `amar_takhsees/` folder** at the root level of the house directory.
- All Amar Takhsees documents go here regardless of the person named, since these people didn't actually live there.
- No 13-category subdivision — PDFs placed directly in this folder.

### D-04: House-Generic Letters
- **Flat `house_letters/` folder** at the root level of the house directory.
- No subcategory subdivision — PDFs placed directly in this folder.
- These are documents about the house itself, not tied to any specific person.

### D-05: PDF Naming Convention
- **Date-based naming** when dates are available: `{date}_{category}.pdf` (e.g., `2024-01-15_notification.pdf`).
- Fall back to a **counter** when no date is extracted: `{category}_1.pdf`, `{category}_2.pdf`.
- Arabic names in filenames use the canonical name from entity resolution.

### D-06: Empty Folder Pre-creation
- **Always create all 13 subfolders** inside each resident's directory, even if empty.
- Makes the structure predictable and consistent for downstream consumers.

### D-07: Re-run / Overwrite Behavior
- If the output directory already exists, **delete it entirely and regenerate cleanly**.
- No merge/skip logic — always a fresh generation.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Definitions
- `.planning/ROADMAP.md` — Phase 2 definition and success criteria (SYS-01 through SYS-06).
- `.planning/REQUIREMENTS.md` — System requirements for filesystem organization.
- `.planning/PROJECT.md` — Core constraints and 13-category definitions.

### Phase 1 Outputs (Inputs to Phase 2)
- `src/pipeline.py` — `Pipeline.process_pdf()` returns `list[DocumentGroup]`.
- `src/schemas.py` — `DocumentGroup` dataclass and `Category` enum (13 types).
- `src/split.py` — `extract_pdf_segment()` for PDF slicing.
- `src/main.py` — Current flat output logic to be replaced by the filesystem generator.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `extract_pdf_segment(source_pdf, start_page, end_page, output_path)` — ready to use, just needs correct output paths.
- `Category` enum values map directly to subfolder names (e.g., `Category.BASIC_DETAILS.value` = `"basic_details"`).
- `DocumentGroup.primary_tenant` provides the canonical resident name for folder creation.
- `DocumentGroup.dates` list provides dates for filename generation.

### What Needs to Change
- `main.py` — Replace flat file dumping with the new filesystem generator module.
- A new module (e.g., `src/organizer.py`) should handle directory creation and PDF placement.
- CLI argument parsing (e.g., `argparse`) needed for `--output` flag.

### Target Directory Structure
```
output/
└── 683/                              ← house_number (D-01)
    ├── 1_محمد_السيد/                  ← first resident by appearance (D-02)
    │   ├── 1_basic_details/          ← always created (D-06)
    │   ├── 2_personal_details/
    │   ├── 3_amar_takhsees/
    │   ├── 4_key_handover_form/
    │   ├── 5_contract/
    │   ├── 6_ewa_related_letters/
    │   ├── 7_rent_deduction/
    │   ├── 8_allowance_deduction/
    │   ├── 9_notifications/
    │   ├── 10_maintenance/
    │   ├── 11_pictures/
    │   ├── 12_modifications/
    │   └── 13_other_letters/
    ├── 2_أحمد_علي/
    │   └── (same 13 subfolders)
    ├── amar_takhsees/                ← shared flat folder (D-03)
    │   ├── 2024-01-15_amar_takhsees.pdf
    │   └── amar_takhsees_1.pdf
    └── house_letters/                ← flat folder (D-04)
        ├── 2023-05-20_notification.pdf
        └── other_letters_1.pdf
```

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 2-Filesystem Generator*
*Context gathered: 2026-06-22*
