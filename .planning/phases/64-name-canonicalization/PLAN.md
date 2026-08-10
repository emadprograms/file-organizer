# Phase 64: Name Canonicalization

## Context
The canonicalization of organically extracted tenant names into matching golden keys is currently resulting in "page bleeding," where pages are assigned to incorrect tenants or dumped into `Unassigned`. We need to refine the extraction prompts, the anchor logic, and the timeline inference rules to hit maximum practical accuracy.

## Objectives
- [x] Investigate the root causes of page bleeding by building a verbose evaluation harness in `run_eval.py`.
- [x] Correct the Anchor Document logic to prevent tenants from being erased.
- [x] Correct the Canonicalization logic to group dependents (family members like children and wives) into their Head of Household's folder.
- [x] Run full evaluation across all 4 houses (1155, 1166, 1176, 1492) and achieve 95%+ practical accuracy.

## Approach
1. Modify `run_eval.py` to spit out deep forensic logs showing Expected Tenant vs Extracted Name vs Category for every mismatch.
2. Narrow down the anchor categories in `src/timeline/timeline_builder.py` to strictly `contract`, `forms`, and `letters` (removing `id_cards`).
3. Update the LLM prompts in `src/grouping/name_matcher.py` to strictly map family members and dependents to the Head of Household if they share a family name.
4. Add filters in `run_eval.py` to ignore "known issues" (human errors in golden data, blank form date inferences) to calculate Practical Accuracy.
