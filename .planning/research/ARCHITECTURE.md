# Architecture Research

**Domain:** Web Dashboard & Global Search Integration (Python FastAPI + Vanilla JS)
**Researched:** 2026-09-02
**Confidence:** HIGH

## Standard Architecture

### System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                       Frontend (Vanilla JS / HTML)          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Top Nav Bar  │  │ Sidebar Nav  │  │ Document Viewer   │  │
│  │ (Search)     │  │ (Tree Drill) │  │ (Timeline/PDF)    │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬──────────┘  │
│         │                 │                   │             │
├─────────┴─────────────────┴───────────────────┴─────────────┤
│                      Backend REST API (FastAPI)             │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐    ┌───────────────────────────┐  │
│  │ Hierarchy API        │    │ Global Search API         │  │
│  │ (/api/areas/...)     │    │ (/api/search?q=)          │  │
│  └──────────┬───────────┘    └─────────────┬─────────────┘  │
├─────────────┴──────────────────────────────┴────────────────┤
│                         Data Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Directory FS │  │ tenants.yaml │  │ state.json        │  │
│  └──────────────┘  └──────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Sidebar Nav** | Renders nested areas, houses, and tenants | Recursive DOM generation in Vanilla JS |
| **Top Nav Bar** | Captures user input and displays jump links | HTML Input with debounced fetch and dropdown list |
| **Hierarchy API** | Serves directory structure for drill-down | FastAPI endpoints mapping `areas_root_path` to Area/House models |
| **Search API** | Scans filesystem/state for house/person names | FastAPI endpoint returning flattened `SearchResult` models |
| **Pytest Suite** | Validates backend search & hierarchy logic | Standard `pytest` testing `routes.py` and FS indexing |
| **Playwright E2E**| Simulates UI navigation & search accuracy | `playwright-python` in `test_ui.py` interacting with DOM elements |

## Recommended Project Structure

```text
src/
├── api/
│   ├── routes.py          # Existing routes + New /api/search and /api/areas
│   ├── models.py          # Pydantic models for SearchResult, Area, House, Tenant
│   └── static/
│       ├── index.html     # HTML structure with new TopNav and Sidebar
│       ├── app.js         # Logic for tree expansion, search debounce, state sync
│       └── styles.css     # Styling for nested tree and search dropdown
tests/
├── frontend/
│   └── test_ui.py         # Playwright E2E tests for sidebar drill-down and search
└── test_api.py            # Pytest for backend endpoints (Hierarchy & Search)
```

### Structure Rationale

- **`src/api/routes.py`**: Centralizes all backend integrations to the filesystem. Easy to test via `TestClient`.
- **`src/api/static/app.js`**: Keeps frontend simple and dependency-free (Vanilla JS). Will utilize separate logical functions for rendering the tree and handling search queries.
- **`tests/frontend/test_ui.py`**: E2E tests are kept independent from unit tests for faster TDD loop on backend logic.

## Architectural Patterns

### Pattern 1: Lazy Loaded Hierarchy
**What:** The sidebar initially only loads top-level "Areas". When an Area is clicked, it fetches the "Houses" inside it. When a House is clicked, it fetches the "Tenants/Timelines".
**When to use:** Ideal when `areas_root_path` contains hundreds of directories.
**Trade-offs:** Introduces slight network latency on expansion, but heavily reduces initial page load time and memory consumption.

**Example:**
```javascript
async function expandArea(areaId) {
    const res = await fetch(`/api/areas/${areaId}/houses`);
    const houses = await res.json();
    renderHouseNodes(areaId, houses);
}
```

### Pattern 2: Debounced Search with In-Memory Caching
**What:** The search bar waits for the user to stop typing before firing a request. The backend caches a mapping of House IDs and Tenant Names on startup (or builds it dynamically and caches) to prevent expensive disk I/O on every keystroke.
**When to use:** Needed for "instant jump" search across many directories and `state.json` files.
**Trade-offs:** Cache invalidation can be tricky if files are modified externally while the server is running.

## Data Flow

### Request Flow

```text
[User Types in Search]
    ↓ (300ms debounce)
[Frontend Top Nav] → [GET /api/search?q=...] → [FastAPI Route]
                                                     ↓
                                           [Cache / Filesystem]
                                                     ↓
[Render Dropdown UI] ← [JSON: SearchResult[]] ← [Return Matches]
```

### State Management

```text
[URL / Global Variables]
    ↓ (subscribe via hashchange or manual update)
[Sidebar Component] ←→ [Highlight Active Node]
    ↓
[Document Viewer] ← [Fetch House Vault / Timeline Data]
```

### Key Data Flows

1. **Tree Drill-Down:** Frontend requests `/api/areas`, user clicks Area -> frontend requests `/api/areas/{id}/houses`, user clicks House -> `/api/houses/{id}/timeline` (reused).
2. **Search Jump:** Frontend receives search results mapping to specific `house_id` and optionally `tenant_id`. Clicking a result updates the application state, forcefully expands the corresponding sidebar tree nodes, and loads the document viewer.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-1k files | Direct filesystem scanning (`Path.rglob`) and parsing `state.json` per request is acceptable. |
| 1k-100k files | Cache directory structure in memory on server boot. Search API reads from memory cache rather than touching disk. |

### Scaling Priorities

1. **First bottleneck:** Disk I/O during global search if scanning thousands of `state.json` files per keystroke. Fix by building an in-memory dictionary cache of names/houses on startup.
2. **Second bottleneck:** DOM size in the frontend if all nodes are expanded. Fix by strictly enforcing lazy DOM updates or pagination for tenants.

## Anti-Patterns

### Anti-Pattern 1: Synchronous Full-Disk Search
**What people do:** Call blocking `os.walk` or heavy JSON parsing in standard `def` FastAPI endpoints.
**Why it's wrong:** Blocks the event loop, freezing the server for all other API requests (like loading PDFs).
**Do this instead:** Use `async def` with `run_in_threadpool` or `asyncio.to_thread` for heavy filesystem scanning, or pre-cache.

### Anti-Pattern 2: Monolithic API Responses
**What people do:** Returning the entire Area -> House -> Tenant structure in one giant `/api/hierarchy` request.
**Why it's wrong:** Wastes bandwidth and slows down initial load time for data the user hasn't even clicked on.
**Do this instead:** Build granular endpoints (e.g., `/api/areas`, `/api/areas/{area_id}/houses`).

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Filesystem | Async IO / Cached Reads | Treat `areas_root_path` as read-only for these endpoints. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Frontend ↔ Backend | REST (JSON) | Ensure search returns consistent `SearchResult` objects containing `type` (house/tenant) and target `ids` for jumping. |
| Search API ↔ Vault | File Reading | Must read `.source_files/*_state.json` to extract tenant names accurately. |

## Suggested Build Order

1. **Backend TDD (Pytest)**: Implement Pydantic models & endpoints for Hierarchy (`/api/areas`) and Search (`/api/search`).
2. **Backend Logic**: Hook up endpoints to filesystem operations, with caching if needed.
3. **Frontend TDD (Playwright)**: Write UI tests for expected DOM elements (nested tree elements, search input).
4. **Frontend Implementation**: Update `index.html` layout, implement `app.js` tree rendering and search debounce fetching.
5. **Integration Testing**: Verify instant jump logic successfully expands the right path in the hierarchical sidebar.

## Sources

- `.planning/PROJECT.md`
- Codebase inspection: `src/api/routes.py`, `src/api/static/`, `tests/frontend/test_ui.py`

---
*Architecture research for: Web Dashboard and Global Search Integration*
*Researched: 2026-09-02*
