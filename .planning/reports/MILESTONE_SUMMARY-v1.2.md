# Milestone v1.2 — Project Summary

**Generated:** 2026-07-17
**Purpose:** Team onboarding and project review

---

## 1. Project Overview

**What This Is:** A technical debt cleanup and refactoring effort for the file organizer project. The goal is to remove unused legacy code, break down bloated functions, and implement logic-based modular refactoring.
**Target Users / Value:** Keep the codebase lean and maintainable without altering the existing correct functionality.
**Milestone v1.2 Scope:** Pipeline Resilience & Grouping Overhaul. Phases 7, 8, 9, and 10 have been executed to add strict Pydantic validation, "True Until Proven Guilty" grouping, and robust rate-limiting safety nets to the LLM orchestration layer.

## 2. Architecture & Technical Decisions

- **Decision:** Dynamic Literal Schema Enforcement for Routing
  - **Why:** Instead of generic string types, generating a dynamic `Literal` from configuration ensures that the LLM's responses are structurally enforced against allowed folders. It rejects hallucinations at the Pydantic parsing layer.
  - **Phase:** 07
- **Decision:** 3-Attempt Retry Loop with Feedback
  - **Why:** To automatically correct LLM hallucinations. If the LLM returns an invalid folder, it receives explicit feedback indicating the rejected value and the allowed choices, failing hard if unresolved.
  - **Phase:** 07
- **Decision:** "True Until Proven Guilty" Correspondence Grouping
  - **Why:** To prevent correspondence (letters) from being inappropriately split by tables or page breaks. Continuity is assumed as long as the `subject` central theme remains unchanged.
  - **Phase:** 08
- **Decision:** Hybrid Routing Matrix
  - **Why:** Deterministic bypass paths (Contracts, IDs, Bills) save LLM latency and cost since their grouping logic is fixed. The LLM is reserved for complex detection (Letters, Forms, Others).
  - **Phase:** 08
- **Decision:** Global LLM Resilience Loop with Strict Wait Times
  - **Why:** To replace `tenacity` exponential backoff with deterministic 65s waits for rate limits (429) and 15s waits with provider rotation for server errors (500s).
  - **Phase:** 09
- **Decision:** "Correctness First" Hard Halts
  - **Why:** Elimination of all fallback logic (e.g., misrouting to `'13_others'`). Unrecoverable errors or persistent validation failures now intentionally raise a `PipelineHaltError` to stop execution and prevent data corruption.
  - **Phase:** 09
- **Decision:** Dynamic Chunking with Provider Rotation Definition
  - **Why:** Grouping chunks step down in size (5 -> 3 -> 2) if a full rotation across LLM providers fails, ensuring resilience against repeated edge cases.
  - **Phase:** 10
- **Decision:** LLM-Validated Anchor Merge
  - **Why:** Rather than blindly merging chunks mathematically, the system uses a 1-page overlap sliding window to confirm logical boundaries.
  - **Phase:** 10

## 3. Phases Delivered

| Phase | Name | Status | One-Liner |
|-------|------|--------|-----------|
| 07 | Anti-Hallucination Schema Enforcement | Complete | Enforce structural validation of LLM routing responses to prevent folder hallucinations and implement a resilient retry loop. |
| 08 | "True Until Proven Guilty" Grouping Logic | Complete | Transition grouping logic from a generic approach to a category-aware hybrid routing system with deterministic bypasses. |
| 09 | Rate Limiting & Router Safety Net | Complete | Enforce a "Correctness First" failure model, replacing graceful fallbacks with explicit pipeline halts and strict LLM retries. |
| 10 | Chunk State Management | Complete | Implement resilient grouping with dynamic chunk sizing (5->3->2), persistent state recovery, and LLM-validated anchor merging. |

## 4. Requirements Coverage

- ✅ **SCHM-01**: Replace generic string typing in RoutingResponse with a strict Pydantic Literal binding exactly to the allowed folders.
- ✅ **PRMPT-01**: Update the grouping prompt to explicitly enforce "True Until Proven Guilty" for document boundaries.
- ✅ **PRMPT-02**: Instruct the LLM that letters are assumed to be continuations unless the topics are vastly different.
- ✅ **PRMPT-03**: Add explicit rules and examples for handling implicit continuations like un-headered tables and appendices.
- ✅ **RES-01**: The tenacity retry predicate must accept the Exception object so rate limiting waits out the 60s cooldown instead of crashing instantly.
- ✅ **RES-02**: The router must allow critical rate limit and runtime errors to bubble up to halt the pipeline.
- ✅ **RES-03**: Remove the global consecutive routing failures permanent lockout in the router.
- ✅ **GRP-01**: Decrease grouping chunk sizes to [4, 3, 2] (Implemented as 5->3->2) and dynamic failure thresholds.
- ✅ **GRP-02**: Ensure the chunk size index and failure counter are properly reset to 0 upon processing a successful chunk.
- ✅ **GRP-03**: Restructure the failure counter so that exhausting the chunk limit gracefully halts the pipeline instead of crashing blindly, enabling the checkpoint system.
- ✅ **GRP-04**: Prevent the overlap merging logic from blindly merging chunks mathematically; ensure it respects LLM boundaries.

**Audit Verdict:**
The milestone audit reveals the milestone is **NOT** fully ready to be closed due to test suite breakages (17 failed tests out of 163) related to missing exports/imports and routing safety issues. Additionally, the `GroupingStateManager` (Phase 10) was not instantiated or used in the `pipeline.py` run loop.

## 5. Key Decisions Log

- **Phase 07**: Implemented `pydantic.create_model` to generate dynamic Literal schemas for routing.
- **Phase 07**: Set a strict 3-attempt limit for routing retries with context-aware feedback on rejected values.
- **Phase 08**: Split prompt templates by category (`LETTER_PROMPT`, `FORM_PROMPT`, `OTHER_PROMPT`).
- **Phase 08**: Created deterministic bypass for grouping: `contract`, `id_cards` always group; `utility_bills` always split.
- **Phase 09**: Replaced `tenacity` with a manual loop to deterministically handle 429s (65s wait), 500s (15s wait + provider rotate: Gemini -> Groq -> Gemini -> OpenRouter), and 401/403s (immediate halt).
- **Phase 09**: Dropped all fallback logic to '13_others', ensuring any unresolved ambiguity raises `RoutingValidationError`.
- **Phase 10**: Checkpoint mechanism implemented to save state (`grouping_state.json`) after every LLM response to allow resume from exact failure points.

## 6. Tech Debt & Deferred Items

- **Tech Debt**: The test suite currently has 17 failing tests related to integration gaps (`src/processing/organizer/__init__.py` missing exports and `RoutingValidationError` capturing unexpected JSON serialization errors).
- **Tech Debt**: The `GroupingStateManager` built in Phase 10 is currently unused by the main application (`src/processing/pipeline.py`), effectively bypassing state persistence in production.
- **Deferred Item**: Phase 11 (Conditional LLM Folder Routing and Folder Renaming) was moved out of Milestone 1.2 to Milestone 1.3 Future.

## 7. Getting Started

- **Run the project**: Run the main application file or pipeline scripts.
- **Key directories**: `src/processing/routing/` for routing logic and config, `src/processing/grouping/` for dynamic chunking and merging, `src/llm/` for resilient LLM client logic.
- **Tests**: The primary test suite commands are `pytest tests/test_routing.py`, `pytest tests/test_routing_schema.py`, and `pytest tests/test_grouping.py`.
- **Where to look first**: Review `src/llm/llm.py` for the central LLM loop and provider rotation logic, and `src/processing/routing/router.py` for the dynamic Pydantic schema validation.

---

## Stats

- **Timeline:** Shipped 2026-07-10
- **Phases:** 4 / 4
- Git statistics unavailable — no tag or date range could be determined.
