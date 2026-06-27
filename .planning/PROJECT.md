# File Categorizer

## Core Value
Categorizes files using LLMs.

## Requirements

### Validated

- ✓ Clean up, audit, and fix existing code — v1.1
- ✓ Delete redundant code no longer using core logic — v1.1
- ✓ Remove local model support — v1.1
- ✓ Simplify API key loading and switching process — v1.1
- ✓ Implement cloud-only fallback chain: Gemini -> OpenRouter -> Groq — v1.1
- ✓ Add comprehensive tests and harden code — v1.1
- ✓ Add Google style docstrings — v1.1

### Active

*(None yet — Planning next milestone)*

### Out of Scope

- Local model execution.

## Context

Shipped v1.1 with completely overhauled LLM architecture, transitioning exclusively to cloud APIs with a robust failover chain (Gemini -> OpenRouter -> Groq) via the Strategy Pattern. Extractor pipelines and configuration parsing have been hardened and modularized.

- Test suite passes 100% (22 integration/unit tests).
- E2E cascade for LLM fallback validated.
- Nyquist validation passing.

## Key Decisions
- **01-01-local-removal:** Removed all local LLM extraction and fallback logic. ✓ Good (Migrating purely to cloud APIs for stability and avoiding local model management overhead.)
- **02-01-api-keys:** Centralized API key configuration with fail-fast validation and local quota tracking. ✓ Good (Prevent runtime crashes and monitor quota.)
- **02-02-gap-closure:** Deferred environment variable checks to load_config(). ✓ Good (Ensures load_dotenv() runs before environment checks.)
- **03-cloud-fallback:** Implemented provider cascade via Strategy Pattern. ✓ Good (Seamless failover from primary to fallback providers).

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-28 after v1.1 milestone*
