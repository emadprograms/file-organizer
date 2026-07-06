# Phase 11: close-gaps-llm-01-to-llm-08-log-02-out-05-grp-10-wire-correc - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-06T08:24:00+03:00
**Phase:** 11-close-gaps-llm-01-to-llm-08-log-02-out-05-grp-10-wire-correc
**Areas discussed:** Audit Log Format, Unassigned Period Naming, Semantic Routing Response

---

## Audit Log Format (LOG-02)

| Option | Description | Selected |
|--------|-------------|----------|
| Save as structured JSON in logs/traces/ alongside LLM calls for easy parsing | | |
| Inline in app.log as text (simpler to read in one place) | | |
| Both: inline summary in app.log and detailed JSON in logs/traces/ | | ✓ |

**User's choice:** Both: inline summary in app.log and detailed JSON in logs/traces/
**Notes:** 

---

## Unassigned Period Naming (OUT-05)

| Option | Description | Selected |
|--------|-------------|----------|
| 'Unassigned (YYYY-MM-DD to YYYY-MM-DD)' using the exact inferred start/end dates | | |
| 'Unassigned (YYYY-MM to YYYY-MM)' using just the year and month | | ✓ |
| 'Unassigned (YYYY to YYYY)' using just the years | | |

**User's choice:** 'Unassigned (YYYY-MM to YYYY-MM)' using just the year and month
**Notes:** 

---

## Semantic Routing Response (GRP-10)

| Option | Description | Selected |
|--------|-------------|----------|
| JSON object with 'folder' and 'reason' (provides better audit trail and forces the LLM to think) | | ✓ |
| Just the folder name as a simple string (faster, saves tokens) | | |

**User's choice:** JSON object with 'folder' and 'reason' (provides better audit trail and forces the LLM to think)
**Notes:** 

---

## the agent's Discretion

None

## Deferred Ideas

None
