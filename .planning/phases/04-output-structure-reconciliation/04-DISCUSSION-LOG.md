# Phase 4: Output Structure & Reconciliation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md -- this log preserves the alternatives considered.

**Date:** 2026-07-05
**Phase:** 4-Output Structure & Reconciliation
**Areas discussed:** Folder structure & naming, Checkpoint/resume design, Reconciliation manifest & report, FileOrganizer refactor scope

---

## Folder Structure & Naming

| Option | Description | Selected |
|--------|-------------|----------|
| Number prefix + English slug | e.g. `01_basic_details` -- matches existing routing.py pattern | ✓ |
| Plain slug, no number | e.g. `basic_details` | |
| Number + Arabic label | e.g. `01_المعلومات_الأساسية` | |

**User's choice:** Number prefix + English slug matching routing.py

---

| Option | Description | Selected |
|--------|-------------|----------|
| Canonical Arabic name + timeline | e.g. `علي محمد 2018-2023/` | ✓ |
| Sanitized transliteration + timeline | e.g. `Ali_Mohamed_2018-2023/` | |
| Arabic NFC only | Rely on sanitize_filename() | |

**User's choice:** Canonical Arabic name + timeline

---

| Option | Description | Selected |
|--------|-------------|----------|
| Infer from unassigned pages date range | min_date to max_date of pages going to Unassigned | ✓ |
| Overall document date range | Earliest to latest page of entire PDF | |
| Static label | `غير محدد/` with no period | |

**User's choice:** Infer period from date range of unassigned pages

---

## Checkpoint / Resume

| Option | Description | Selected |
|--------|-------------|----------|
| Pass 1 only | cleaned.json already implemented | |
| Pass 1 + Pass 2 grouped state | Save DocumentGroup list before PDF splitting | ✓ |
| Full state including written PDFs | Most complex | |

**User's choice:** Save Pass 2 grouped/routed DocumentGroup list as JSON before splitting

---

| Option | Description | Selected |
|--------|-------------|----------|
| Same output dir as Pass 1 | `output/{house_id}_grouped.json` | |
| Dedicated checkpoints dir | `output/checkpoints/grouped.json` | ✓ |
| Alongside source files | `{target_dir}/{house_id}_grouped.json` | |

**User's choice:** Dedicated checkpoints directory

---

| Option | Description | Selected |
|--------|-------------|----------|
| After all PDFs written | Clean completion | |
| Never | Keep as permanent audit trail | |
| After successful reconciliation | Page counts match | ✓ |

**User's choice:** Delete checkpoints after successful reconciliation pass

---

## Reconciliation Manifest & Report

| Option | Description | Selected |
|--------|-------------|----------|
| JSON | Machine-readable `{house_id}_manifest.json` | ✓ |
| CSV | Human-readable in Excel | |
| Both | JSON + summary TXT | |

**User's choice:** JSON

---

**Manifest structure:** Agent discretion -- chose Option C (summary + per-page array) as it best supports audit verification of no lost pages.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Halt with RuntimeError | Mismatches must not pass | ✓ |
| Log warning, write manifest anyway | Let operator decide | |
| Write manifest + non-zero exit code | No exception traceback | |

**User's choice:** Halt pipeline and raise RuntimeError on count mismatch

---

## FileOrganizer Refactor Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Extend in-place | Add pre-create step and reconciliation method to existing class | |
| Replace with new OutputBuilder | New class, old class unused | |
| Rewrite same file | Same filename and class name, rebuilt with full Phase 4 responsibilities | Agent decision |

**User's choice:** Agent discretion -- agent chose rewrite in-place (same class name, same import, clean implementation)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Pre-create all 13 dirs | Even if empty (OUT-03 requirement) | |
| On-demand only | Create only when a doc routes there | ✓ |

**User's choice (user override):** On-demand only -- empty topic folders NOT pre-created. This intentionally overrides OUT-03.

---

## Agent's Discretion

- Manifest structure: chose summary + per-page array (Option C) for best audit coverage
- FileOrganizer approach: rewrite in-place -- same class name for import compatibility, clean implementation
- Manifest file location: `output/{house_id}_manifest.json` (consistent with pipeline artifacts)
- `output/checkpoints/` dir pre-created before grouping step to avoid write failures

## Deferred Ideas

None -- discussion stayed within phase scope.
