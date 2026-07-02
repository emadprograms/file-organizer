# File Categorizer Generalization

## What This Is

A high-precision document processing pipeline that currently ingests housing-related PDFs and categorizes them. We are transforming it into a general-purpose, configuration-driven tool where users can provide their own instructions for AI extraction, cleaning, grouping, and folder organization via a config file.

## Core Value

Empower users to seamlessly categorize and organize any type of PDF by simply providing clear AI instructions and destination folders, without changing the underlying pipeline engine.

## Current Milestone: v1.1 Code Hardening & Tech Debt Cleanup

**Goal:** Harden the codebase, remove redundant code, and clarify the structure to reduce technical debt introduced in the previous generalization milestone.

**Target features:**
- Clean up redundant code in `src/llm.py`, `src/organizer.py`, and other modules.
- Clarify code architecture and responsibilities to improve readability.
- Eliminate existing technical debt left from the refactor.

## Requirements

### Validated

- ✓ Multi-Pass Classification — Pass 1 (vision extraction), Pass 1.5 (audit/cleaning), Pass 2 (tenant/logical grouping), Pass 3 (organization/routing).
- ✓ LLM Integration — Providers for Gemini, OpenRouter, Groq.
- ✓ Automated PDF Segmentation — Splits large PDFs into categories.
- ✓ Implement a user-provided configuration file (YAML/JSON) parser.
- ✓ Migrate Pass 1 (Vision Extraction) to use config-defined metadata extraction instructions.
- ✓ Migrate Pass 1.5 (Audit & Cleaning) to use config-defined global cleaning instructions.
- ✓ Migrate Pass 2 (Grouping) to use config-defined grouping constraints.
- ✓ Migrate Pass 3 (Organization) to map generated document groups to config-defined "Destination Folders".

### Active

- [ ] Remove redundant/unused legacy code in `src/llm.py` and `src/organizer.py`.
- [ ] Refactor and clarify code architecture to ensure separation of concerns.
- [ ] Clear up existing technical debt left over from the generalization refactoring.

### Out of Scope

- [Changing the core pipeline implementation] — The engine (ingestion, 4 passes) must remain identical, only the instructions/rules are externalized.
- [New feature additions] — This milestone focuses purely on hardening, cleanup, and reducing tech debt.

## Context

The codebase was recently refactored to support general-purpose YAML/JSON configurations, but old logic was left in place, leading to a messy, hard-to-understand architecture. The goal is to clean this up before adding any new features.

## Constraints

- **Compatibility**: Must not alter the underlying Python architecture/pipeline logic.
- **Configuration**: Uses YAML/JSON for the config file.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| "Destination Folders" Terminology | Avoiding the term 'category' for user-defined buckets prevents conflict with the extracted 'category' metadata. | — Pending |

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
*Last updated: 2026-07-02 after new milestone v1.1 initialization*
