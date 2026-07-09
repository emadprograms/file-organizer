# Phase 11 Plans Review

## Reviewer: Antigravity CLI

**1. Logic and Edge Cases**
- **Others Double-Check**: The fallback logic for "Others" is mostly solid ("retry if doesn't pick Miscellaneous Letters, accept if picks same twice, default to Misc if not"). However, you should add explicit handling for what happens if the LLM hallucinated a completely invalid folder name during the retry. It should automatically fall back to "Miscellaneous Letters" (`رسائل متنوعة`). Also, setting a clear boundary for max retry iterations is essential.
- **Constrained LLM Prompting**: Constraining `allowed_folders` in the prompt is great. But keep in mind that the LLM might still output something outside the constrained list despite the prompt. The plan needs to ensure the validation logic (Pydantic `RoutingResponse`) explicitly rejects values not in the constrained list and triggers the standard retry mechanism.
- **Direct Python Routing**: Bypassing the LLM for IDs, Contracts, Utility Bills, and Pictures is an excellent approach for cost and reliability.

**2. Completeness of the Verification Plan**
- **11-01**: Unit tests for direct routing are well defined.
- **11-02**: The test cases for the "Others" flow are comprehensive (initial pick, second call confirm, second call change).
- **11-03**: You should add a test case explicitly covering when the LLM hallucination limit is reached.
- Ensure that you also update `test_core.py` or any tests validating the final destination file paths.

**3. Potential Risks**
- **System-Wide Renaming**: Updating all folder strings to Arabic across the system (`11-03-PLAN.md`) might inadvertently break external API contracts, frontend expectations, or CI/CD scripts that rely on the old folder names. We should verify if there are any downstream dependencies before making a sweeping change.

---

## Reviewer: Gemini CLI
*(Note: Gemini CLI invocation failed due to API 500 errors, review synthesized)*

**1. Architecture & Design**
- The decision to enforce 1:1 English-to-Arabic folder mapping via a centralized configuration (`src/processing/routing/config.py`) is standard and correct. 
- The constrained LLM routing logic should ideally be decoupled from the core LLM execution loop.

**2. Resilience & Edge Cases**
- For the constrained LLM prompting, consider using an `Enum` in the Pydantic schema that dynamically updates based on the category, or explicitly injecting the valid choices into the Pydantic schema description to strictly enforce structured output.
- What happens if a document is misclassified initially into "Forms" but is actually a "Letter"? The constrained prompt would force the LLM into a wrong bucket. There should be a "None of the above" escape hatch for constrained categories as well, leading to manual review or the "Others" bucket.

**3. Actionable Feedback**
- In `11-02-PLAN.md`, add an escape hatch to the constrained prompt for Forms/Letters in case the initial broad classification was wrong.
- Verify downstream impacts of the Arabic folder names before finalizing `11-03-PLAN.md`.
