# Phase 5: Testing - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-28
**Phase:** 5-Testing
**Areas discussed:** Testing strategy, Fallback integration, Coverage & CI

---

## Testing strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Use standard pytest fixtures for mocking API calls. | Use standard pytest fixtures for mocking API calls. | |
| Leverage the existing `.cache.json` for a record/replay approach. | Leverage the existing `.cache.json` for a record/replay approach. | ✓ |

**User's choice:** Leverage the existing `.cache.json` for a record/replay approach.
**Notes:** Decided to reuse the existing pipeline cache rather than building pure pytest mocks for APIs.

---

## Fallback integration

| Option | Description | Selected |
|--------|-------------|----------|
| Completely mock the client instances to raise specific exceptions. | Completely mock the client instances to raise specific exceptions. | |
| Hit the real APIs with dummy/invalid API keys to trigger actual errors. | Hit the real APIs with dummy/invalid API keys to trigger actual errors. | ✓ |

**User's choice:** Hit the real APIs with dummy/invalid API keys to trigger actual errors.
**Notes:** Preferred over mocking clients to ensure that we handle genuine provider exceptions correctly.

---

## Coverage & CI

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, set up GitHub Actions and enforce a minimum coverage threshold (e.g. 80%). | Yes, set up GitHub Actions and enforce a minimum coverage threshold (e.g. 80%). | |
| Set up GitHub Actions, but don't enforce a hard coverage threshold yet. | Set up GitHub Actions, but don't enforce a hard coverage threshold yet. | |
| No CI for now; just run tests locally. | No CI for now; just run tests locally. | ✓ |

**User's choice:** No CI for now; just run tests locally.
**Notes:** Testing remains purely local; CI is deferred.

---

## the agent's Discretion

None

## Deferred Ideas

None
