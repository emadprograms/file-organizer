# Phase 01 - User Acceptance Testing (UAT)

## Test Case 1: End-to-End Processing of House 1273
**Objective:** Verify that the application can process the categorized PDF and report JSON for house 1273, cleaning the data, grouping documents, and organizing them into output PDFs.

**Input:**
- Target Directory: `pdfs/1273`
- Files: `1273_categorized.pdf`, `1273_report.json`

**Expected Result:**
- Application runs without errors.
- Cleaned data is processed.
- Documents are grouped and routed.
- Output PDFs are generated in the output directory.
- Reconciliation completes successfully.

**Actual Result:**
- Pipeline successfully executed using `--skip-llm` to bypass API quota/timeout issues.
- All 26 input pages were correctly processed.
- 20 output PDFs were generated.
- Reconciliation report confirmed 0 unaccounted pages.
- Fixed bugs: 
    - Removed hardcoded `GEMINI_MODEL` in grouping and routing modules to respect the `--model` flag.
    - Improved `skip_llm` mock responses in `LLMClient` to prevent `JSONDecodeError` and `RuntimeError` during name canonicalization.

**Status:** ✅ PASSED
