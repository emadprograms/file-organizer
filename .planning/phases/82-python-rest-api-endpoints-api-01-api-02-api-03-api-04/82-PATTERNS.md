# Phase 82: Pattern Map - Python REST API Endpoints

This document maps the architectural patterns for the new Python REST API endpoints (API-01 to API-04) based on the Phase 82 context. 

## Files to Create/Modify

1. `src/api/__init__.py` (New)
2. `src/api/models.py` (New)
3. `src/api/routes.py` (New)
4. `src/api/server.py` (New)
5. `src/main.py` (Modify)

---

## 1. `src/api/models.py`

*   **Role:** Defines the data schemas (DTOs) for API request and response payloads, ensuring data validation and schema compliance.
*   **Data Flow:** Validates JSON payloads from clients and serializes internal Python objects into JSON responses.
*   **Closest Analog:** `src/core/models.py` and `src/core/schemas.py`. These files heavily utilize Pydantic for defining strict data shapes.
*   **Code Excerpt (`src/core/models.py`):**
    ```python
    from typing import Optional, Any
    from pydantic import BaseModel, field_validator
    
    class PageData(BaseModel):
        category: str | None = None
        content_explanation: str | None = None
        expected_tenant_name: Optional[str] = None
        original_index: int
        user_locked: bool = False
    ```

## 2. `src/api/routes.py`

*   **Role:** Exposes HTTP endpoints (API-01: general/classification, API-02: list vault files, API-03: retrieve Timeline View, API-04: serve PDF contents).
*   **Data Flow:** Intercepts HTTP requests (GET/POST), routes them to internal business logic modules (e.g., `src.core.vault`, `src.core.state`, `src.llm.llm`), and returns `src.api.models` schemas.
*   **Closest Analog:** `src/reconcile/core.py` and `src/ingest/core.py`. These act as controller functions that orchestrate the interaction between the CLI and the underlying core logic.
*   **Code Excerpt (`src/reconcile/core.py` structure logic):**
    ```python
    def run_reconcile_mode(args) -> int:
        house_id = extract_house_id(args.target_dir)
        vault_manager = VaultManager(args.target_dir)
        # ... interacts with state and business logic
    ```

## 3. `src/api/server.py`

*   **Role:** Initializes and configures the FastAPI application instance, wires up the routers, and handles CORS/middleware.
*   **Data Flow:** Acts as the ASGI entry point that processes all incoming web traffic before delegating to `routes.py`.
*   **Closest Analog:** The setup block inside `main.py` where application-level dependencies (like logging config, environment variables, config loading) are initialized before dispatching to a specific command handler.

## 4. `src/main.py`

*   **Role:** The main CLI entry point for the file organizer.
*   **Data Flow:** Parses command-line arguments. Needs to be modified to include a new `serve` or `api` subcommand to launch the uvicorn web server.
*   **Closest Analog:** The existing CLI subparser definitions.
*   **Code Excerpt (`src/main.py`):**
    ```python
    # verify mode
    verify_parser = subparsers.add_parser("verify", help="Deep verify the integrity of a v5 house vault structure")
    verify_parser.add_argument("target_dir", type=Path, help="Path to the target house directory to verify")
    verify_parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    ```
    *Modification Pattern:*
    ```python
    # serve mode
    serve_parser = subparsers.add_parser("serve", help="Start the file organizer REST API")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind the server")
    ```
