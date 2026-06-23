# Phase 6: Core Grouping & Timeline Logic - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-23
**Phase:** 06-core-grouping-timeline-logic
**Areas discussed:** Large families on Anchor docs, Date mismatch grouping, Prefix ID cards & Non-Anchor routing

---

## Large families on Anchor docs (LOGIC-01)

| Option | Description | Selected |
|--------|-------------|----------|
| Remove the limit | Remove the limit completely (any number of names on an anchor doc is valid) | |
| 10 names | Keep a safety threshold of 10 names | ✓ |
| 15 names | Keep a safety threshold of 15 names | |

**User's choice:** Keep a safety threshold of 10 names
**Notes:** 

---

## Date mismatch grouping (LOGIC-04)

| Option | Description | Selected |
|--------|-------------|----------|
| Add is_continuation | Add an `is_continuation` flag to the LLM schema so the AI decides | ✓ |
| Conflicting Date | Implement the 'Conflicting Date' rule (pure logic fix) | |
| Option A | Treat `NONE` as a wildcard | |

**User's choice:** No, I'd rather add an `is_continuation` flag to the LLM schema so the AI decides.
**Notes:** User emphasized that retrying for `is_continuation` must respect API rate limits and backoff logic, not hammer the API.

---

## Prefix ID cards (LOGIC-05) & Non-Anchor routing (LOGIC-06)

| Option | Description | Selected |
|--------|-------------|----------|
| Verified Residents | Pre-scan for Verified Residents, use Temporary Routing and Retrospective Assignment | ✓ |
| Temporary Routing only | Implement non-anchor routing only | |
| ID cards as unknown anchor | Only initialize timeline if current is UNKNOWN | |

**User's choice:** Yes, this logic is perfect. Let's lock this in.
**Notes:** User asked clarifying questions about overlapping timelines and meaningless names. The "Verified Resident" concept was introduced to solve both problems simultaneously.

---

## the agent's Discretion

None

## Deferred Ideas

None
