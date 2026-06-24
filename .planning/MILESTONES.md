# Milestones

## v1.1 API Rate Limits & Stability (Shipped: 2026-06-23)

**Phases completed:** 1 phase, 1 plan, 5 tasks

**Key accomplishments:**
- Enforced a strict global 15 requests/minute IP-level cap across all keys.
- Implemented exponential backoff with jitter up to 300 seconds and permanently retired exhausted keys.
- Handled invalid 245-token LLM responses gracefully by falling back to OTHER_LETTERS after 2 failures.
- Switched to a sequential process to eliminate lock contention on API limits.

---

## v1.0 MVP (Shipped: 2026-06-23)

**Phases completed:** 2 phases, 9 plans, 4 tasks

**Key accomplishments:**

- Implemented Pass 1.5 Entity Resolution logic using an LLM call to map raw names and family members to a Canonical Primary Tenant before deterministic grouping.

---
