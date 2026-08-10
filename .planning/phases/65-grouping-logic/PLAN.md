# Phase 65: Grouping Logic

## Context
With name canonicalization reaching 99% accuracy on clean datasets, the next step in the pipeline is evaluating and refining the **Grouping Logic**. This phase determines whether sequential pages belonging to the same tenant and category are correctly grouped together into multi-page "Documents" (e.g. keeping all 4 pages of a Lease Agreement together).

## Objectives
- [ ] Add an `evaluate_grouping` function to `run_eval.py` to score the accuracy of our Document boundary grouping against the golden data YAML structure.
- [ ] Investigate how well the dynamic LLM chunking (using the `_process_chunk` logic in `src/grouping/core.py`) correlates with human-labeled boundaries.
- [ ] Tweak grouping LLM prompts (e.g., `LETTER_PROMPT`, `FORM_PROMPT`) or deterministic fallback logic to achieve 95%+ grouping accuracy.

## Approach
1. Modify `tests/golden_data/run_eval.py` to instantiate `Pipeline` and execute `_group_documents()`.
2. Compare the output `DocumentGroup` start and end pages against the `documents[].pages[]` arrays in the golden data YAMLs.
3. Run the evaluation and log instances where documents are over-fragmented or over-merged.
4. Refine chunking sizes, threshold behaviors, and prompt instructions based on the evaluation output.
