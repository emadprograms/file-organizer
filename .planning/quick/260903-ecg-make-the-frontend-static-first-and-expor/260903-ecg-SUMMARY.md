---
status: complete
quick_id: 260903-ecg
date: 2026-09-03
---

# Quick Task Summary: Make Frontend Static-First for IIS Without Python on PC 2

## Accomplishments
1. **Created Static Web Exporter (`src/presentation/export_static.py`)**:
   - `build_tree_data`: walks the 3-level area/house/tenant directory hierarchy and builds the tree model matching `/api/tree`.
   - `build_search_index`: extracts houses, tenants, and searchable documents matching `/api/search`.
   - `export_static_web`: compiles `tree.json`, `search_index.json`, a corporate-ready IIS `web.config` with `.json`/`.pdf` MIME mappings, and copies `index.html` to the target areas/web directory.
2. **Added `export-web` CLI Command in `src/main.py`**:
   - Allows running `python src/main.py export-web [--output-dir <path>]` to generate or update the static web dashboard assets directly on PC 1.
3. **Updated Dashboard UI (`src/api/static/index.html`)**:
   - Added automatic static-first detection: falls back to `./tree.json` if `/api/tree` is not found.
   - Replaced backend API dependencies with direct client-side state file access: loads `./<area>/<house>/.source_files/<house_id>_state.json` directly.
   - Computes timeline items, date sorting, and categorized document groupings in client-side JavaScript.
   - Implemented fast client-side search across `search_index.json` without API round-trips.
   - Updated document viewing and hover preview tooltips to load static PDFs directly from `.source_files/vault/doc_<vault_id>.pdf`.
4. **Created Unit Tests (`tests/test_export_static.py`)**:
   - Validates tree hierarchy generation, search index generation, IIS `web.config` structure, and full export.
