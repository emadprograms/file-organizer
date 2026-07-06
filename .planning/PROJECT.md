# Project: File Organizer Post-Processor

**Current State:** v1.0 Shipped (2026-07-06)
The system is a fully functional, high-precision PDF organization pipeline. It successfully ingests categorized JSON reports and transforms them into a structured directory hierarchy with 100% page reconciliation and robust LLM-driven grouping.

## Core Capabilities
- **Automatic Organization:** House $ightarrow$ Tenant (Timeline) $ightarrow$ Topic hierarchy.
- **High Precision:** 0-indexed PDF splitting and strict output validation.
- **Resilience:** Global circuit breaker for LLM failures and atomic checkpointing.
- **Preview:** Rich-based dry-run visualization.

## Next Milestone Goals (v1.1 / v2.0)
- [ ] **Performance Optimization:** Explore asynchronous LLM calls (if API supports) or batching.
- [ ] **Configuration Flexibility:** Move hardcoded topic lists and routing rules to the YAML config.
- [ ] **Enhanced UX:** Add a summary report PDF/HTML after every run.
- [ ] **Expanded Support:** Support for multiple house directories in a single invocation.

---
<details>
<summary>Archive: Previous Project Context</summary>

**Core Value:** Automatically transform a flat, pre-categorized PDF into a perfectly organized folder structure per tenant, with zero manual sorting — driven entirely by the JSON report data, LLM intelligence, and configurable YAML routing rules.

### Constraints
- **Model**: Gemma 4 26B A4B IT
- **Rate Limit**: 7 seconds between LLM requests
- **Failure Threshold**: Pipeline aborts after 5 consecutive global 500/Timeout errors
- **Language**: Arabic output filenames and summaries
</details>
