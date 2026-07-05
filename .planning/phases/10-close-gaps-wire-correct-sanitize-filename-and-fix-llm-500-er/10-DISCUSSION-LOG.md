# Phase 10: close-gaps-wire-correct-sanitize-filename-and-fix-llm-500-er - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-05T23:50:00+03:00
**Phase:** 10-close-gaps-wire-correct-sanitize-filename-and-fix-llm-500-er
**Areas discussed:** Sanitize filename location, Fallback routing for 500 errors, 500 error state tracking

---

## Sanitize filename location

| Option | Description | Selected |
|--------|-------------|----------|
| Standardize on src/core/utils.py | Delete/deprecate src/fs_utils.py | |
| Standardize on src/fs_utils.py | Delete/deprecate the one in core/utils.py | |
| Something else | I'll type it | |

**User's choice:** You decide.
**Notes:** Decided to standardize on `src/core/utils.py` to keep common utilities centralized.

---

## Fallback routing for 500 errors

| Option | Description | Selected |
|--------|-------------|----------|
| Route to `13_others` | As implemented in Phase 6 | |
| Route to `Unassigned` | As suggested in Phase 7 | ✓ |
| Something else | I'll type it | |

**User's choice:** Route to `Unassigned`
**Notes:** User initially selected `Unassigned`, but revised this significantly in the next question.

---

## 500 error state tracking

| Option | Description | Selected |
|--------|-------------|----------|
| Reset per document/operation | | |
| Track globally across the entire run | | |
| Something else | I'll type it | ✓ |

**User's choice:** no no don't give up on that chunk. fail that file. so that when I try that file again, I can continue from where I left...
**Notes:** This overrides the previous question's answer. Instead of routing to `Unassigned`, any exhaustion of the 500 error limits (which remains global for the run) should fail the entire process for that file so it can be cleanly resumed later.

---

## the agent's Discretion

Sanitize filename location (standardized on `src/core/utils.py`)

## Deferred Ideas

None
