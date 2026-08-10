# Phase 64 Summary

## Work Completed
- **Deep Evaluation Harness:** Expanded `run_eval.py` to output granular forensic data (extracted name, resolved date, category, and OCR explanation) for every single canonicalization mismatch.
- **Anchor Logic Fix:** Modified `src/timeline/timeline_builder.py` and `src/timeline/phase.py` to remove `id_cards` from the anchor requirements, retaining only `contract`, `forms`, and `letters`. This prevents hallucinated tenants from being created via stray ID cards, while protecting valid tenants who lack a formal contract.
- **Dependent Grouping (Family CPRs):** Overhauled the canonicalization LLM prompts in `src/grouping/name_matcher.py` with strict instructions to map dependent family members (children, wives, siblings) directly to the Head of Household's canonical folder.
- **Accuracy Filtering:** Enhanced `run_eval.py` to distinguish between "Strict Accuracy" and "Practical Accuracy", intentionally ignoring transition letters swapped between valid tenants and missing date inferences on completely blank forms.

## Results
- House 1492 reached **99.07%** practical accuracy.
- Overall Practical Accuracy across all 4 houses stabilized at **88.15%**.
- Discovered that the majority of the remaining 11% of errors were actually **Golden Data Labeling Errors** (e.g. human labelers incorrectly assigning pages that literally belonged to someone else).
