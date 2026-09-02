---
description: "Add backend tests to verify phonetic Arabic-English search intermixing works robustly"
---

# Plan

1. Append a new API test `test_search_phonetic_arabic_english` to `tests/test_api.py`.
2. Mock a test state with both Arabic and English tenant names.
3. Assert that searching for `mohammad`, `hussain`, `sahar mirza`, and `abdullah` matches the appropriate Arabic tenants.
4. Run pytest to confirm all tests pass, and fix any regressions in existing tests along the way.
