# Phase 07: cross-phase-integration-fixes-tenant-date-mapping-relative-i - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-05
**Phase:** 07-cross-phase-integration-fixes-tenant-date-mapping-relative-i
**Areas discussed:** Relative vs Absolute Indexing, Dry-Run output format, Tenant/Date Mapping fallbacks, CLI flag design

---

## Relative vs Absolute Indexing

| Option | Description | Selected |
|--------|-------------|----------|
| Normalize to 0-indexed | Normalize everything to 0-indexed internally immediately after parsing, only convert to 1-indexed for logging/UI | ✓ |
| Keep 1-indexed | Keep everything 1-indexed internally to match the report, subtract 1 only exactly at the PyMuPDF API boundary | |
| Dedicated PageReference | Create a dedicated PageReference object that explicitly holds both and prevents mixing them up | |

**User's choice:** Normalize everything to 0-indexed internally immediately after parsing, only convert to 1-indexed for logging/UI
**Notes:** None

---

## Dry-Run output format

| Option | Description | Selected |
|--------|-------------|----------|
| Concise tree | Show a concise tree of planned folders and files, omitting LLM reasoning to keep it clean | ✓ |
| Tree with reasoning | Show the tree view, but include the LLM reasoning/confidence as inline annotations next to each file | |
| Full detailed log | Output the full detailed log as if it ran, but prefixed with [DRY-RUN] | |

**User's choice:** Show a concise tree of planned folders and files, omitting LLM reasoning to keep it clean
**Notes:** None

---

## Tenant/Date Mapping fallbacks

| Option | Description | Selected |
|--------|-------------|----------|
| Route to 'Unassigned' | Route to 'Unassigned' folder to guarantee pipeline completion, flagging it in the logs | ✓ |
| Fail pipeline immediately | Fail the pipeline immediately — strict enforcement is better than misfiled documents | |

**User's choice:** Route to 'Unassigned' folder to guarantee pipeline completion, flagging it in the logs
**Notes:** None

---

## CLI flag design

| Option | Description | Selected |
|--------|-------------|----------|
| Add `--verbose` | Add `--verbose` to output full LLM prompt/responses and verbose logs | ✓ |
| Add `--skip-llm` | Add `--skip-llm` to mock LLM responses for faster layout/routing testing | ✓ |
| Only `--dry-run` | Stick to only `--dry-run` for now to avoid complexity | |

**User's choice:** both verbose and skip llm
**Notes:** User manually typed to include both.

---

## the agent's Discretion

None

## Deferred Ideas

None
