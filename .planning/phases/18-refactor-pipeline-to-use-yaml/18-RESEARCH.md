# Phase 18: Refactor Pipeline to use YAML - Research Notes

## Overview
The goal of this phase is to integrate YAML-driven configuration for tenant extraction and routing, replacing the hardcoded anchor logic when applicable. This enables a dual-mode strategy: an Initial Discovery mode that derives a YAML from existing anchor logic, and an Incremental Update mode where the pipeline strictly adheres to the YAML structure for document mapping.

## Code Adjustments

### `src/timeline/phase.py` (`process_cleaning_phase`)
- Needs to check for the presence of `tenants.yaml` in the root/target directory.
- **Initial Discovery (No YAML)**: 
  - Proceed with current `build_tenant_timelines` using anchor logic.
  - Automatically generate and save `tenants.yaml` based on the discovered timelines (with `start_date` and `end_date`).
- **Incremental Update (YAML exists)**:
  - Load `tenants.yaml`.
  - Pass the tenant names from YAML directly to `canonicalize_with_llm` to map raw OCR names.
  - Use the timelines from `tenants.yaml` to override missing tenant associations.
  - Apply the missing tenant fallback logic:
    - **Has Date, No Name**: Map to the tenant covering the date. If overlapping, resolve to the **latest** tenant.
    - **No Date, No Name**: Resolve to the tenant marked with `end_date: "present"`.

### `src/tenant_config/tenants.py`
- Modify `canonicalize_with_llm` to optionally take a predefined list of allowed tenant names (from YAML) and constrain the LLM's output to strictly map to these known identities.
- Enhance `build_tenant_timelines` to be bypassable when `tenants.yaml` provides the explicit timelines, skipping the `stats["anchor_count"] >= 1 and stats["total_count"] >= 5` rule.

### `src/main.py`
- Update file placement operations in `run_generation_pass`.
- **D-01 & D-02 & D-03**: Rename `source_files` to `.source_files`. Ensure the original `*_categorized.pdf` remains in the root output directory and is NOT moved into `.source_files`. Only move `*_report.json` and `.run_cache` checkpoints into `.source_files`.
- Provide the necessary path to `tenants.yaml` down to `process_cleaning_phase`.

## Validation Architecture

The test infrastructure will need robust coverage to verify the dual-mode execution and file placement updates. 

### 1. Conditional Anchor Logic Bypass Validation
- **Initial Discovery (No YAML)**: Provide mock documents simulating the anchor conditions (e.g. >= 1 anchor, >= 5 pages). Verify that only tenants meeting the threshold are extracted and that a correctly formatted `tenants.yaml` is written out.
- **Incremental Update (YAML present)**: Create a mock `tenants.yaml` and feed in documents that **fail** the strict anchor logic (< 5 pages or 0 anchors). Verify that these documents are correctly assigned to the tenants from the YAML, proving the anchor logic is skipped.

### 2. Timeline Fallback Logic Validation
- **Overlap Handling**: Configure `tenants.yaml` with overlapping dates for two tenants (e.g., Tenant A: Jan-June, Tenant B: May-December). Pass a mock document with a date in May and no name. Verify it is assigned to Tenant B (the latest tenant).
- **No Date, No Name**: Pass a mock document (like a picture) with no dates and no name. Verify it defaults to the tenant with `end_date: "present"`.

### 3. Directory and File Placement Validation
- **Hidden Directory**: Verify that `.source_files` is created instead of `source_files`.
- **PDF Placement**: After a full pipeline run, assert that the original `*_categorized.pdf` is still located in the root target directory (e.g., `output_dir / house_id`).
- **Data File Placement**: Assert that `*_report.json` and all `.run_cache` files are successfully moved inside `.source_files/`.
