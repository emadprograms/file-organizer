# Phase 23: inbox-parsing-and-syntax - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-20T17:45:00+03:00
**Phase:** 23-inbox-parsing-and-syntax
**Areas discussed:** Syntax Strictness, Missing Field Inference ('U'), Group parameter behavior, Area Conflict Resolution, Tenant Override, Invalid Filenames

---

## Syntax strictness

| Option | Description | Selected |
|--------|-------------|----------|
| Relaxed | Take the first 4 tokens, ignore trailing text | ✓ |
| Strict | Expect exactly 4 tokens | |
| Delimited | Require a specific delimiter | |

**User's choice:** Take the trailing text and use it as the document title, bypassing LLM title generation.
**Notes:** The parser is updated to expect 5 positional arguments `[AREA] [HOUSE] [TENANT_HINT] [GROUP] [DATE]`. Anything after that is the title.

---

## Inferring 'U' fields

| Option | Description | Selected |
|--------|-------------|----------|
| Categorization pipeline | Run the standard pipeline to get `_report.json` | ✓ |
| Targeted call | Lightweight LLM call specifically for missing fields | |

**User's choice:** Categorization pipeline.
**Notes:** The user also clarified `[GROUP]` logic where numbers 1-13 skip grouping and routing, `G` skips grouping, and `U` runs both. Area will be scanned from `config.yaml`, and Date/House inferred via majority vote from `_report.json`.

---

## Area conflict resolution

| Option | Description | Selected |
|--------|-------------|----------|
| Fail safe | Refuse to parse and rename file indicating the conflict | ✓ |
| LLM tie-breaker | Ask the LLM to guess the area | |

**User's choice:** Fail safe.
**Notes:** Propose a rename like `saf/uh 1273 U U 2026 - please choose area.pdf` to force the user to resolve it.

---

## Tenant Override

| Option | Description | Selected |
|--------|-------------|----------|
| 5th positional argument | Add `[TENANT_HINT]` to syntax | ✓ |
| Prefix/suffix flag | Use special tag in trailing notes | |

**User's choice:** 5th positional argument.
**Notes:** The hint will be passed to the LLM canonicalization logic to match against existing tenants.

---

## Invalid filenames

| Option | Description | Selected |
|--------|-------------|----------|
| Rename with error | Append `_Error_Invalid_Format` suffix | ✓ |
| Ignore silently | Leave the file as is | |

**User's choice:** Rename with error.
**Notes:** Immediate feedback to the user on parse failure.

---

## the agent's Discretion
None

## Deferred Ideas
- Implementation of the FS-UI orchestration loop (Phase 24).
