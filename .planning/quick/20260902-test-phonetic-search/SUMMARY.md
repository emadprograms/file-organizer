---
status: complete
---

# Summary

Added the `test_search_phonetic_arabic_english` test suite to `tests/test_api.py`. It comprehensively validates the new `phonetic_normalize` logic in the `/api/search` endpoint by asserting that English phonetics properly map to mock Arabic tenant names in the API response. Additionally, resolved an outdated test assertion (`test_timeline_404_missing_state`) that was still expecting a 404 response instead of the updated 200 with an empty list. All API tests now pass successfully.
