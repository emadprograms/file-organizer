# File Categorizer Generalization

## What This Is

A high-precision document processing pipeline that currently ingests housing-related PDFs and categorizes them. We are transforming it into a general-purpose, configuration-driven tool where users can provide their own instructions for AI extraction, cleaning, grouping, and folder organization via a config file.

## Core Value

Empower users to seamlessly categorize and organize any type of PDF by simply providing clear AI instructions and destination folders, without changing the underlying pipeline engine.

## Requirements

### Validated

- ✓ Multi-Pass Classification — Pass 1 (vision extraction), Pass 1.5 (audit/cleaning), Pass 2 (tenant/logical grouping), Pass 3 (organization/routing).
- ✓ LLM Integration — Providers for Gemini, OpenRouter, Groq.
- ✓ Automated PDF Segmentation — Splits large PDFs into categories.

### Active

- [ ] Implement a user-provided configuration file (YAML/JSON) parser.
- [ ] Migrate Pass 1 (Vision Extraction) to use config-defined metadata extraction instructions.
- [ ] Migrate Pass 1.5 (Audit & Cleaning) to use config-defined global cleaning instructions.
- [ ] Migrate Pass 2 (Grouping) to use config-defined grouping constraints.
- [ ] Migrate Pass 3 (Organization) to map generated document groups to config-defined "Destination Folders".
- [ ] Create a `sample-config.yaml` for users (e.g. replicating the tenant/real-estate structure).
- [ ] Create a private config for local testing to ensure backward compatibility.

### Out of Scope

- [Changing the core pipeline implementation] — The engine (ingestion, 4 passes) must remain identical, only the instructions/rules are externalized.

## Context

The current tool was hardcoded for a very specific real estate/tenant use case. It is already fully functional, but users cannot bring their own categories or grouping logic. The codebase is fully mapped in `.planning/codebase/`.

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
*Last updated: 2026-07-01 after initialization*
