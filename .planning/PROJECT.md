# File Categorizer

## Core Value
Categorizes files using LLMs.

## Current Milestone: v1.1 Tech Debt & Cloud Migration

**Goal:** Clear technical debt, remove local model support, simplify API key management, establish a robust cloud-only fallback structure (Gemini -> OpenRouter -> Groq), and harden code with tests.

**Target features:**
- ✓ Clean up, audit, and fix existing code — Phase 01
- ✓ Delete redundant code no longer using core logic — Phase 01
- ✓ Remove local model support — Phase 01
- ✓ Simplify API key loading and switching process — Phase 02
- Implement cloud-only fallback chain: Gemini -> OpenRouter -> Groq
- Add comprehensive tests and harden code

### Key Decisions
- **01-01-local-removal:** Removed all local LLM extraction and fallback logic. Rationale: Migrating purely to cloud APIs for stability and avoiding local model management overhead.
- **02-01-api-keys:** Centralized API key configuration with fail-fast validation and local quota tracking. Rationale: Prevent runtime crashes and monitor quota.
- **02-02-gap-closure:** Deferred environment variable checks to load_config(). Rationale: Ensures load_dotenv() runs before environment checks.

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

*Last updated: 2026-06-27 after Phase 02*
