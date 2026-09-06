# Phase 87: Extended Search Intelligence

## Context
This phase is part of `v9.0 Hierarchical Web Dashboard` milestone.
We need to enhance `/api/search` with the following intelligence capabilities:
1. **Typo Tolerance for Arabic OCR Variations**:
   - Add fuzzy matching (e.g. using `difflib`) when searching for tenant names.
   - Arabic names sometimes have OCR artifacts or typos.

2. **Full-Text Document Search**:
   - Parse `report.json` for each house (`.source_files/{house_id}_report.json`).
   - Iterate over the `documents` array.
   - Match the search query against `content` and `brief_arabic_title`.
   - Return these matches in the `/api/search` response with type `document`.

## Requirements
- Update `SearchResultResponse` model to support `type="document"`.
- Implement `difflib.get_close_matches` or similar for tenant names.
- Read `report.json` during search to fetch document matches.
- Ensure API returns valid JSON.
- Make tests pass.
