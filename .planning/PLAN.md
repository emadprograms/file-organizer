# Plan: Phase 65 - Integrate Pass 2 Categorization & Comprehensive Testing

## 1. Inject `process_fine_categorization`
- Ensure `run_fine_categorization_pass` in `src/pipeline/runner.py` is properly integrated into the main flow.
- Modify `src/categorization/fine_categorization.py` (`process_fine_categorization`) to support loading/saving intermediate states per page, so we don't lose progress if a crash happens midway.

## 2. Checkpointing (`_categorization.json`)
- Introduce a checkpointing mechanism inside `process_fine_categorization` that writes to `[target_dir]/.source_files/[house_id]_categorization.json` after each page is processed.
- On startup, `process_fine_categorization` will read this file and skip pages that are already categorized.

## 3. CLI Output in `main.py`
- Update `src/main.py` and `src/pipeline/runner.py` to add clear, user-facing logging/CLI output reflecting "Step 2: Fine Categorization" when this pass begins. 

## 4. Comprehensive Tests
- Write `tests/test_categorization_logic.py` to rigorously test the recently fixed edge cases:
  - ID Cards vs Forms (ensuring CPR/National IDs are routed to Personal Details).
  - Allocation Orders vs Modifications.
  - Rent vs Allowances.
- Use mocked `LLMClient` responses or specific fixtures to ensure deterministic testing.
