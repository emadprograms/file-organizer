# Phase 23 - Inbox Parsing and Syntax: Research

**Date:** 2026-07-20
**Phase:** 23 - inbox-parsing-and-syntax
**Goal:** Build parser for space-separated FS-UI commands

## 1. Codebase Structure & Integration Points

- **`src/main.py`**: Contains `run_append_mode(config: Any)` which handles the `append` CLI subcommand with an `.inbox.lock`. This mode loops over files in `inbox_path` and will be the primary caller of the new parser.
- **`src/core/config.py`**: Defines `AppConfig` which loads `inbox_path`, `areas_root_path`, and `area_mappings`.
- **`src/categorization/categorization.py`**: Houses `process_unclassified_pdf()` which runs LLM extraction and generates `_report.json`. This is critical for inferring missing `U` fields.
- **`src/timeline/phase.py` & `src/grouping/name_matcher.py`**: Contains the logic for Pass 1 canonicalization (e.g., `canonicalize_with_llm()` and `cluster_names_fuzzily()`) which can be adapted or reused to map `TENANT_HINT` to a canonical tenant name.

## 2. config.yaml Schema (`area_mappings`)

- `config.yaml` maps human-friendly area names to their ID counterparts (e.g., `"Safra C": "SAF C"`).
- To resolve an area when `[AREA]` is `U`, the parser will need to scan the physical subdirectories inside `areas_root_path` (e.g., `/Volumes/arshad-pc/Areas/SAF C/1234`). If a house ID is found in multiple area folders, the parser must raise a conflict error and trigger the rename (`_please choose area.pdf`).

## 3. Pass 1 Canonicalization for TENANT_HINT

- `src/grouping/name_matcher.py` exposes `canonicalize_with_llm(unresolved_names, llm_client, allowed_tenants)`.
- To map `TENANT_HINT` to an exact directory:
  1. Load existing tenants for the house using `src/tenant_config/yaml_loader.py::load_tenant_config()` (reads `.source_files/[house]_tenants.yaml`).
  2. Pass the `TENANT_HINT` and the list of allowed tenants to `canonicalize_with_llm` to get the exact match. If `U`, it falls back to chronological assignment logic.

## 4. Grouping & Routing Pipeline Skips (`[GROUP]`)

- **`1-13`**: Document is pre-grouped and pre-routed. The pipeline completely skips both `src/pipeline/pipeline.py::_group_documents` and `_route_documents`. The parser will set `doc.folder_path` to the exact matched folder string from `FOLDER_PREFIXES`.
- **`G`**: Document is a pre-grouped monolith but needs routing. Skips `_group_documents` but invokes `_route_documents`.
- **`U`**: Raw monolith. Runs the standard pipeline (`_group_documents` -> `_route_documents`).

## 5. 13 Folder Structure

Defined as `FOLDER_PREFIXES` in `src/routing/config.py`. The numbers 1-13 map exactly to these 13 standardized Arabic folders:

1. `01_بيانات أساسية`
2. `02_بيانات شخصية`
3. `03_أمر تخصيص`
4. `04_محضر تسليم مفتاح`
5. `05_عقود`
6. `06_كهرباء وماء`
7. `07_استقطاع إيجار`
8. `08_وقف استقطاع بدل`
9. `09_إشعارات`
10. `10_صيانة`
11. `11_صور ومعاينات`
12. `12_تعديلات`
13. `13_رسائل متنوعة`

## 6. `_report.json` Structure for Inference

- The generated `_report.json` is a JSON array (or dictionary by page keys) of classification dicts.
- Relevant fields available for majority-vote inference:
  - `expected_house_number`: Extracted house ID.
  - `date`: Document issue date.
- To resolve `U` for House or Date, the parser will parse `_report.json`, collect valid values across all pages, and compute the mode (majority vote).

## 7. Pydantic Models for Parser Output

- Currently, `src/core/schemas.py` defines `DocumentGroup`, `GroupEntry`, etc.
- A new model (e.g., `ParsedCommand`) should be added to `src/core/schemas.py` to strongly type the 5 space-separated positional args:
  - `area` (str | Literal['U'])
  - `house` (str | Literal['U'])
  - `tenant_hint` (str | Literal['U'])
  - `group` (int | Literal['G', 'U'])
  - `date` (str | Literal['U'])
  - `title` (str - from trailing text)

## 8. Integration within `append`

- The parser should be exposed as a standalone function (e.g., `parse_inbox_filename(filename: str) -> ParsedCommand`).
- Within `src/main.py`'s `run_append_mode`, the listener loop will iterate over PDFs, call this parser, catch invalid syntax exceptions (to immediately rename to `_Error_Invalid_Format`), and invoke `process_unclassified_pdf` when it needs to infer `U` fields.

## Validation Architecture

### Critical Integration Points
- Parser must be pure (no side effects) — validation and resolution happen in separate layers
- Area resolution requires filesystem access to `areas_root_path` subdirectories
- Tenant resolution requires YAML config loading + LLM client initialization
- `_report.json` inference requires running the full categorization pipeline

### Risk Areas
- **Area ambiguity**: House exists in multiple areas — handled by error rename (D-11)
- **Tenant hint mismatch**: LLM canonicalization returns no match — needs graceful fallback
- **Empty _report.json**: Categorization produces no usable data — needs error handling
- **Partial U fields**: Some fields resolved, others not — needs partial resolution tracking
