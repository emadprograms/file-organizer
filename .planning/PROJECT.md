# File Categorizer

## Core Value
Categorizes files using LLMs.

## Current Milestone: v1.1 Tech Debt & Cloud Migration

**Goal:** Clear technical debt, remove local model support, simplify API key management, establish a robust cloud-only fallback structure (Gemini -> OpenRouter -> Groq), and harden code with tests.

**Target features:**
- Clean up, audit, and fix existing code
- Delete redundant code no longer using core logic
- Remove local model support
- Simplify API key loading and switching process
- Implement cloud-only fallback chain: Gemini -> OpenRouter -> Groq
- Add comprehensive tests and harden code

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
