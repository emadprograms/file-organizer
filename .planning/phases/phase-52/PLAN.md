# Phase 52 Plan: Corrupted Vault File Safeguards

## 1. Context and Objective
This phase aims to fulfill REQ-04 by ensuring that the reconciler, pipeline, timeline generator, and verification processes survive corrupted or 0-byte PDFs in the vault. 

## 2. Requirements Addressed (REQ-04)
- The system MUST survive encountering a corrupted, empty, or 0-byte PDF inside the vault.
- Verification and Timeline View generation MUST NOT crash when attempting to parse or link to a corrupted vault document.
- The reconciler MUST flag corrupted vault files during its health-check routines.

## 3. Detailed Implementation Plan

### Step 1: Update Verification Engine (`src/core/verification.py`)
- Locate the collection of physical Vault PDFs in `run_verification()`.
- Add logic to check for corrupted files:
  - Check if `stat().st_size == 0`. If so, add an error: `add_error(f"Corrupt (0-byte) Vault PDF detected: {f.name}")`.
  - Use `pypdf.PdfReader` wrapped in a `try...except Exception` block to open the PDF. If an exception occurs, add an error flagging it as corrupt: `add_error(f"Corrupt Vault PDF detected: {f.name} ({e})")`.

### Step 2: Ensure Reconciler Safe Ingestion and Flagging (`src/reconcile/core.py`)
- The reconciler already handles `PdfReader` exceptions via `try...except` (defaulting to `1` page).
- Update these `try...except` blocks (around lines 200 and 343) to increment a new metric in the report dictionary: `report.setdefault("corrupt_vault_files", 0); report["corrupt_vault_files"] += 1`.
- Update the Reconciler Summary log output at the end of the script to display the number of "Corrupt Vault Files Detected" if `report.get("corrupt_vault_files", 0) > 0`.

### Step 3: Ensure Watcher Orchestrator handles Vault / Shortcut Safely (`src/watcher/orchestrator.py`)
- In `watcher/orchestrator.py`, `fitz.open(str(filepath))` is called during processing (e.g., line 214 and line 422). If a corrupt PDF or a shortcut to a corrupt PDF is passed, this call will crash `fitz`.
- Wrap `fitz.open(str(filepath))` calls inside a `try...except Exception` block. If it fails, log an error, and safely abort processing for that file or use a default (like in line 422 where it does have a try-except, but line 214 does not). For line 214, if it fails, fallback gracefully or abort.

### Step 4: Ensure Pipeline Safe Processing (`src/pipeline/runner.py`)
- The `runner.py` uses `fitz.open(str(pdf_path))` to read total pages (around line 160).
- If a corrupt PDF is dropped into the pipeline, it crashes here.
- Wrap this `fitz.open` call with a `try...except Exception` block. If it fails, set `total_input_pages = 1` and log a warning, allowing the pipeline to continue.

## 4. Verification & Testing
- Create/update unit tests to verify corrupted vault handling:
  - Generate a 0-byte `.pdf` file inside the vault.
  - Run the reconciler and verify it completes without crashing and increments the `corrupt_vault_files` report metric.
  - Run the verification script and assert that it correctly flags the 0-byte vault file.
- Perform manual UAT by dropping a 0-byte PDF into the watcher inbox and ensuring the orchestrator safely skips or defaults it without crashing the service.
