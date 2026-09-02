---
status: complete
---

# Summary

Implemented cross-lingual phonetic search matching in `src/api/routes.py`. The `phonetic_normalize` function converts Arabic characters to their English consonant equivalents and strips English vowels and semi-vowels. This normalized string is then compared against the query's normalized form. This allows queries like `mohammad` to instantly and accurately match Arabic strings like `محمد` without requiring an LLM or complex translation database at query time. The search endpoint logic has been updated to use this phonetic matching as a fallback for both substring searches and fuzzy difflib matching.
