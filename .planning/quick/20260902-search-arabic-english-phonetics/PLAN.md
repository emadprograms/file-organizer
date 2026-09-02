---
description: "Support Arabic-English intermixing in search queries with phonetic matching"
---

# Plan

1. Create a `phonetic_normalize` function in `src/api/routes.py` to normalize Arabic strings to English consonants and strip English vowels.
2. Update the `/api/search` route to compare phonetically normalized versions of the query and tenant names alongside standard substring and difflib matching.
3. Allow `mohammad` to match `محمد` perfectly by using fuzzy matching on phonetically normalized strings.
