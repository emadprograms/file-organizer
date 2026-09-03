# Quick Task: Make Frontend Static-First for IIS Without Python on PC 2

## Description
Eliminate the requirement for Python on PC 2 by allowing the frontend dashboard to run as a 100% static web application hosted via IIS. On PC 1 (Python), add an `export-web` command that compiles `tree.json` and `search_index.json` into the root of the areas directory. Update `index.html` to auto-detect static mode: loading `tree.json`, searching `search_index.json`, parsing each house's `.source_files/<id>_state.json` directly in the browser, and loading PDFs directly from `.source_files/vault/doc_<vault_id>.pdf`. Also generate a minimal `web.config` so IIS serves `.json` and `.pdf` files without MIME type errors.

## Tasks
1. **Create Static Exporter Module & CLI Command**
   - Create `src/presentation/export_static.py` containing:
     - `generate_tree(areas_root)`: builds hierarchical areas/houses/tenants tree matching `/api/tree` output.
     - `generate_search_index(areas_root)`: builds search index matching `/api/search` structure.
     - `generate_web_config(target_dir)`: writes `web.config` with IIS MIME types for `.json` and `.pdf`.
     - `export_static_web(config, target_dir)`: writes `tree.json`, `search_index.json`, `web.config`, and copies `index.html` into `target_dir` (defaulting to `areas_root_path`).
   - Register `export-web` command in `src/main.py`.

2. **Update `src/api/static/index.html` for Static-First Mode**
   - Detect static mode (or probe if `/api/tree` is not responding / running on static host).
   - In static mode:
     - Load `tree.json` instead of `/api/tree`.
     - Perform in-browser client-side fuzzy search on `search_index.json` instead of `/api/search`.
     - Load house data directly from `./<area>/<house>/.source_files/<id>_state.json`.
     - Compute timeline items and categorized document cards in pure client-side JavaScript.
     - Point PDF viewer directly to `./<area>/<house>/.source_files/vault/doc_<vault_id>.pdf`.
   - Ensure backward compatibility if served through FastAPI.

3. **Verification**
   - Run tests (`pytest tests/frontend/`).
   - Validate `export-web` logic with automated test or invocation.
   - Verify `STATE.md` and document completion.
