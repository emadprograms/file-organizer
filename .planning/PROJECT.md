# Project: File Organizer Post-Processor

**Current State:** v1.1 Shipped (2026-07-06)
The system is now a streamlined, high-precision PDF organization post-processor. It has been fully pruned of all legacy extraction and YAML configuration logic, ensuring a clean, maintainable codebase focused exclusively on transforming JSON reports into physical directory structures.

## Core Capabilities
- **Automatic Organization:** House $ightarrow$ Tenant (Timeline) $ightarrow$ Topic hierarchy.
- **High Precision:** 0-indexed PDF splitting and strict output validation.
- **Resilience:** Global circuit breaker for LLM failures and atomic checkpointing.
- **Preview:** Rich-based dry-run visualization.
- **Streamlined Architecture:** Pure post-processing pipeline with no redundant extractor logic.

## Next Milestone Goals
**Goal: Generalization & External Configuration**
The next phase of the project is to transition from hardcoded routing rules to a general-purpose, configuration-driven tool. This will involve:
- Implementing a new, robust configuration schema (JSON/YAML) for AI instructions.
- Allowing users to define custom extraction and routing logic via config.
- Decoupling the pipeline from specific housing-related categories.

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? $ightarrow$ Move to Out of Scope with reason
2. Requirements validated? $ightarrow$ Move to Validated with phase reference
3. New requirements emerged? $ightarrow$ Add to Active
4. Decisions to log? $ightarrow$ Add to Key Decisions
5. "What This Is" still accurate? $ightarrow$ Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
<details>
<summary>Archive: Previous Project Context (v1.0 & v1.1)</summary>

**Core Value:** Automatically transform a flat, pre-categorized PDF into a perfectly organized folder structure per tenant, with zero manual sorting — driven entirely by the JSON report data, LLM intelligence, and configurable routing rules.

### Constraints
- **Model**: Gemma 4 26B A4B IT
- **Rate Limit**: 7 seconds between LLM requests
- **Failure Threshold**: Pipeline aborts after 5 consecutive global 500/Timeout errors
- **Language**: Arabic output filenames and summaries
</details>
