# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.1 — Tech Debt & Cloud Migration

**Shipped:** 2026-06-28
**Phases:** 7 | **Plans:** 11 | **Sessions:** 5

### What Was Built
- **Pure Cloud LLM Architecture:** Removed all local model support, transitioning to a robust cloud-only Strategy Pattern.
- **Resilient Fallback Chain:** Implemented a sequential failover mechanism (Gemini $ightarrow$ OpenRouter $ightarrow$ Groq) with intelligent error handling (429 retries vs 5xx failovers).
- **Fail-Fast Configuration:** Centralized API key management in `src/config.py` with startup validation and local quota tracking.
- **Hardened Codebase:** Comprehensive Google-style docstrings and a full unit/integration test suite covering the provider cascade and pipeline orchestration.

### What Worked
- **Fail-Fast Startup:** Moving validation to the startup phase prevented elusive runtime crashes during long-running categorization jobs.
- **Strategy Pattern for LLMs:** The provider abstraction made it trivial to add/remove cloud providers without touching the core pipeline logic.
- **Atomic Task Commits:** Committing each task independently within phases made the audit and verification process significantly cleaner.

### What Was Inefficient
- **Module-Level Evaluation:** Initial implementation of API key checks at the module level in `src/config.py` created a race condition with `load_dotenv()`, requiring a corrective phase (Phase 02 Plan 02).
- **Manual Docstring Iteration:** Adding docstrings across all files was a repetitive task that could have been more efficiently handled via a structured batch-edit approach.

### Patterns Established
- **Cloud-First Resilience:** The pattern of "Try $ightarrow$ Retry on 429 $ightarrow$ Failover on 5xx/Auth" is now the standard for all LLM interactions.
- **Centralized Tracking:** Logging API usage to `.tracking/api_calls.log` provides visibility into cost and quota consumption.

### Key Lessons
1. **Initialization Order Matters:** Always defer environment-dependent validation until the explicit configuration loading sequence has run (after `load_dotenv`).
2. **Failover Gracefulness:** Intercepting 401/403 errors during the fallback chain is critical to ensure the system doesn't crash when an optional secondary provider key is missing or expired.

### Cost Observations
- Model mix: 70% Sonnet (Development/Refactoring), 30% Opus (Architecture/Final Review).
- Sessions: 5
- Notable: Using `unittest.mock.patch` for `time.sleep` during rate-limit testing saved significant wall-clock time.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.1 | 5 | 7 | Shifted to cloud-only architecture and implemented rigorous failover testing. |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.1 | 22 | High | 4 |

### Top Lessons (Verified Across Milestones)

1. **Configuration Deferral:** Deferring environment checks to `load_config()` is essential for predictable startup behavior.
2. **Provider Abstraction:** Decoupling the LLM client from the pipeline allows for seamless resilience updates.
