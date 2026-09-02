---
wave: 1
depends_on: []
files_modified:
  - src/api/__init__.py
  - src/api/models.py
  - src/api/routes.py
  - src/api/server.py
  - src/main.py
autonomous: true
---

# Phase 82: Python REST API Endpoints (API-01, API-02, API-03, API-04)

## Threat Model
<threat_model>
ASVS Level: 1
Blocking Threshold: high
Scope: Web API Endpoints

Potential Threats:
1. Path Traversal (High): `/api/houses/{house_id}/pdf/{vault_id}` could be manipulated to read arbitrary files via `../` if not strictly validated against `.source_files/vault/doc_{vault_id}.pdf`.
2. Denial of Service (Medium): Serving large PDFs without rate limiting.
3. Information Exposure (Low): Exposing system path structure in error messages.

Mitigations:
- Validate `house_id` and `vault_id` using regex (`^[a-zA-Z0-9_-]+$`) to prevent path traversal.
- Ensure `FileResponse` only resolves within the designated `areas_root_path/house_id/.source_files/vault/`.
- Use a generic error message for 404s: `{"error": "Resource not found.", "solution": "Verify the endpoint URL and the resource ID."}` as per UI-SPEC.
</threat_model>

## Wave 1: API Models & Server Setup

<task>
<action>
Create `src/api/__init__.py` and `src/api/models.py`.
In `src/api/models.py`, define Pydantic models for responses:
1. `HouseResponse(BaseModel)`: fields `id: str`, `name: str`
2. `VaultFileResponse(BaseModel)`: fields `vault_id: str`, `filename: str`, `start_page: int`, `end_page: int`, `date: str`, `tenant: str`
3. `CategoryResponse(BaseModel)`: fields `name: str`, `document_count: int`
4. `TimelineGroupResponse(BaseModel)`: fields `vault_id: str`, `primary_tenant: str`, `dates: list[str]`, `brief_arabic_title: str`
</action>
<read_first>
- src/core/schemas.py
</read_first>
<acceptance_criteria>
- `src/api/models.py` can be imported without errors.
- Pydantic models exist with exact names.
</acceptance_criteria>
</task>

<task>
<action>
Create `src/api/routes.py` with FastAPI `APIRouter()`.
Implement endpoints:
1. `GET /api/houses` -> returns `list[HouseResponse]`. Scans `config.areas_root_path` for directories.
2. `GET /api/houses/{house_id}/vault` -> returns `list[VaultFileResponse]`. Reads `.source_files/{house_id}_report.json` and parses it. (Validates `house_id` with regex `^[a-zA-Z0-9_\-\s]+$`).
3. `GET /api/houses/{house_id}/timeline` -> returns `list[TimelineGroupResponse]`. Reads `.source_files/{house_id}_state.json`, extracts `grouped_documents`.
4. `GET /api/houses/{house_id}/categories` -> reads `tenants.yaml` and `.source_files/{house_id}_state.json` to count documents per tenant/category.
5. `GET /api/houses/{house_id}/pdf/{vault_id}` -> serves actual PDF using `fastapi.responses.FileResponse`. Validates `vault_id` with `^[a-zA-Z0-9_-]+$`. Absolute path must be `areas_root_path / house_dir / .source_files/vault/doc_{vault_id}.pdf`.
Use `request.app.state.config.areas_root_path` to get the root path.
If files or houses are missing, raise `HTTPException(404, detail="{\"error\": \"Resource not found.\", \"solution\": \"Verify the endpoint URL and the resource ID.\"}")`.
</action>
<read_first>
- src/api/models.py
- src/core/config.py
</read_first>
<acceptance_criteria>
- `src/api/routes.py` has the 5 defined `GET` routes.
- Path traversal mitigation is in place for `house_id` and `vault_id`.
</acceptance_criteria>
</task>

<task>
<action>
Create `src/api/server.py` with FastAPI `app` definition.
Include `CORS` middleware (allow all origins for now).
Include the router from `src.api.routes`.
Add a lifespan context manager or dependency to load `AppConfig` and store it in `app.state.config`. If loading fails, fallback gracefully or raise.
</action>
<read_first>
- src/api/routes.py
- src/core/config.py
</read_first>
<acceptance_criteria>
- `src/api/server.py` defines `app = FastAPI()`.
- CORS middleware is added.
- `app.state.config` is initialized on startup.
</acceptance_criteria>
</task>

## Wave 2: CLI Integration

<task>
<action>
Modify `src/main.py`.
In `get_parser()`, add a new subparser for `serve` mode:
```python
serve_parser = subparsers.add_parser("serve", help="Start the file organizer REST API")
serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind the server")
```
In `main()`, add logic to handle `args.command == "serve"`:
```python
if args.command == "serve":
    import uvicorn
    # Make sure to run it gracefully
    uvicorn.run("src.api.server:app", host="127.0.0.1", port=args.port, reload=False)
    return 0
```
</action>
<read_first>
- src/main.py
</read_first>
<acceptance_criteria>
- `python src/main.py serve -h` shows the serve command options.
- Running `python src/main.py serve --port 8000` starts the web server.
</acceptance_criteria>
</task>

## Verification Criteria
- `curl http://127.0.0.1:8000/api/houses` returns JSON array.
- `curl http://127.0.0.1:8000/openapi.json` returns OpenAPI spec.
- CLI command `python src/main.py serve` functions as expected.

## must_haves
- All UI-SPEC error states correctly injected as HTTPException detail strings.
- Path traversal mitigation implemented.
- `serve` CLI command bound to uvicorn.

## Artifacts this phase produces
- `src/api/__init__.py`
- `src/api/models.py` (HouseResponse, VaultFileResponse, CategoryResponse, TimelineGroupResponse classes)
- `src/api/routes.py` (FastAPI router with 5 GET endpoints)
- `src/api/server.py` (FastAPI app, lifespan manager)
- CLI subparser `serve` in `src/main.py`
