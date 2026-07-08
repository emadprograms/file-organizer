---
wave: 4
depends_on:
  - 04-subpackages-refactoring-PLAN.md
files_modified:
  - src/organize.py
autonomous: true
---

# Plan: Main Application Refactoring

## Requirements
- REF-03

## Context
Split oversized functions across the application into smaller functions. The `main()` function in `src/organize.py` is quite large and handles validation, cleaning, grouping, routing, and file generation.

## Tasks

<task>
<read_first>
- src/organize.py
</read_first>
<action>
Refactor `main()` in `src/organize.py` by extracting distinct logical steps into smaller helper functions.
Extract the cleaning pass into a function like `run_cleaning_pass`.
Extract the grouping and routing pass into a function like `run_grouping_pass`.
Extract the file generation pass into a function like `run_generation_pass`.
The `main()` function should simply coordinate these high-level functions.
</action>
<acceptance_criteria>
- `main()` in `src/organize.py` is reduced in size, ideally under 50 lines.
- The pipeline logic remains functionally identical, passing data between the extracted functions.
</acceptance_criteria>
</task>

## Artifacts this phase produces
- `run_cleaning_pass` function in `src/organize.py`
- `run_grouping_pass` function in `src/organize.py`
- `run_generation_pass` function in `src/organize.py`

## Must Haves
### truths
- The `main()` function acts solely as an orchestrator for smaller pipeline steps.

### prohibitions
- No single function in `src/organize.py` exceeds 60 lines.
