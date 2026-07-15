# Phase 18: Refactor Pipeline to use YAML - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-15
**Phase:** 18-Refactor Pipeline to use YAML
**Areas discussed:** Translation Execution, Anchor Logic Removal, Missing Tenant Handling, File Organization

---

## Translation Execution & Anchor Logic Bypassing

| Option | Description | Selected |
|--------|-------------|----------|
| Translate in Application Logic | Pre-translate names | |
| Translate via LLM Prompt | Feed YAML to LLM for strictly mapping names | ✓ |

**User's choice:** Feed YAML to LLM. The user provided an exact dual-mode specification: If YAML doesn't exist, use old Anchor Logic and auto-generate YAML. If YAML exists, feed YAML to LLM and bypass Anchor Logic.
**Notes:** YAML will include timelines (`start_date` and `end_date`), allowing manual overrides for new tenants.

## Missing Tenant Handling & Historical Timeline

| Option | Description | Selected |
|--------|-------------|----------|
| Fail fast | Error out on missing tenant | |
| Read from JSON | Build timeline from past JSON to infer tenant | |
| Use YAML timelines | Use timelines exclusively from the YAML | ✓ |

**User's choice:** The user clarified we don't need historical JSON files since `tenants.yaml` will contain `start_date` and `end_date`. If no name is extracted, use document date vs YAML timelines. Overlaps are assigned to the newest tenant. Pictures (no date, no name) are assigned to the "present" tenant.

## File Organization & Safety

| Option | Description | Selected |
|--------|-------------|----------|
| Move all to `source_files` | (Current Behavior) | |
| Keep PDF in root, hide source_files | Rename to `.source_files`, leave PDF alone | ✓ |

**User's choice:** Make `.source_files` hidden, keep the original categorized PDF in the root directory, move only the JSON caches.

---

## Claude's Discretion

None

## Deferred Ideas

None
