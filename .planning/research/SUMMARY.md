# Project Research Summary

**Project:** Document Management System Dashboard (File Organizer)
**Domain:** Web Dashboard & Global Search Integration
**Researched:** 2026-09-02
**Confidence:** HIGH

## Executive Summary

The research indicates that the best approach for the File Organizer Dashboard is a lightweight frontend using Vanilla JS and the DOM API interacting with a Python FastAPI backend. The core focus is delivering a hierarchical sidebar (Areas -> Houses -> Tenants) mirroring the physical directory structure and a fast global search bar for instant navigation. 

The recommended testing stack avoids heavy frontend frameworks and relies on `pytest-playwright` for robust E2E UI testing, alongside `httpx` and `pytest-asyncio` for asynchronous API testing. 

Key risks revolve around "Mocking Hell" in testing directory scanning APIs (manually mocking filesystem instead of using `pyfakefs`), flaky E2E Playwright tests due to poor locators, and ignoring the immutable Windows `.lnk` Vault architecture during global searches. Mitigations center around utilizing robust web-first Playwright assertions, using `tmp_path` for accurate file system test isolation, and properly resolving `.lnk` metadata in search indexing.

## Key Findings

### Recommended Stack

The stack favors Python-centric testing tools that seamlessly integrate with the existing FastAPI backend and pytest ecosystem, while maintaining a dependency-free frontend to keep the architecture lightweight.

**Core technologies:**
- **pytest-playwright (0.9.0):** E2E UI Testing — Seamless integration with the existing `pytest` ecosystem; controls browsers directly from Python tests.
- **httpx (0.28.1):** Backend API Testing — Required for FastAPI's `TestClient` to test new directory-scanning and search APIs asynchronously.
- **pytest-asyncio (1.4.0):** Async Backend Testing — Enables native `async/await` in `pytest`, crucial for asynchronous directory scanner endpoints.
- **Vanilla JS + DOM API:** Frontend Interactivity — Used for building the hierarchical drill-down sidebar and search bar without complex framework overhead.

### Expected Features

The feature set prioritizes navigation and fast access without overcomplicating the search indexing mechanisms.

**Must have (table stakes):**
- **Collapsible Sidebar Navigation** — Areas -> Houses -> Tenants mapping directly to directory structure (max 3 levels).
- **Global Search Bar (Basic)** — Match exact or partial strings for house numbers or person names.
- **Click-to-Jump Navigation** — Clicking a search result instantly navigates to the specific tenant/timeline view.
- **Backend API endpoints** — Pytest-covered APIs for directory listing and hierarchical data fetching.

**Should have (competitive):**
- **Command Palette (Cmd/Ctrl+K)** — Instant search trigger for power users without touching the mouse.
- **Instant "Zero-Click" Results** — Displays top matches instantly as the user types before full submit.
- **Deep Linking / URL Routing** — URL routing synced with sidebar expansion so users can share or refresh specific states.

**Defer (v2+):**
- **Fuzzy Matching / Typo Tolerance** — High implementation complexity for Arabic OCR/name inconsistencies.
- **Full-text Document Search** — Complex to implement over large vaults; not essential for initial metadata search.

### Architecture Approach

The system employs a Vanilla JS frontend sending debounced requests to a FastAPI backend. The API layer reads from the local filesystem (directories, `.lnk` files, and `state.json`) and returns optimized JSON structures.

**Major components:**
1. **Hierarchy API (`/api/areas`)** — Maps `areas_root_path` to Area/House models and lazy-loads hierarchical structures to avoid monolithic JSON responses.
2. **Global Search API (`/api/search`)** — Scans filesystem/state for names and returns flattened metadata matches instantly.
3. **Sidebar Nav & Top Nav** — Frontend components utilizing recursive DOM generation and debounced fetching with in-memory caching for instant search updates.

### Critical Pitfalls

1. **"Mocking Hell" in Directory Scanning APIs** — Relying on `unittest.mock.patch` for `os.walk` leads to brittle tests. Avoid by using `pyfakefs` or pytest's `tmp_path` fixture for real isolated file systems.
2. **Flaky Playwright Tests on Hierarchical Sidebars** — Relying on timeouts and deep CSS paths causes race conditions. Avoid by using web-first assertions (`toBeVisible`) and accessibility locators (`getByRole`).
3. **Over-Nesting and Cognitive Overload in Sidebar** — A 1-to-1 filesystem mapping is visually cluttered. Avoid by constraining depth to 2-3 levels max and using the main view for deeper drill-downs.
4. **Search Erasure and Poor Empty States** — Clearing input or showing blank pages on 0 results causes friction. Retain search query and provide fallback suggestions.
5. **Global Search Ignoring Windows .lnk Architecture** — Returning raw Vault IDs instead of `.lnk` paths. Avoid by integrating `pylnk3` into search indexing to resolve correct target paths.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Backend API Development (Hierarchy & Search)
**Rationale:** The UI fully depends on data structure (Areas, Houses, Tenants). APIs must be robust, tested, and aware of the `.lnk` architecture before frontend development begins.
**Delivers:** Models and endpoints for `/api/areas` (lazy-loaded structure) and `/api/search` with fast metadata lookups.
**Addresses:** Backend Directory & Search APIs.
**Avoids:** "Mocking Hell" in Directory APIs, Global Search Ignoring `.lnk` Architecture.

### Phase 2: Frontend Implementation (Sidebar & Top Nav)
**Rationale:** With backend data stable, the Vanilla JS components can be implemented.
**Delivers:** Collapsible drill-down sidebar, debounced search bar with click-to-jump capabilities, and deep linking/URL routing.
**Uses:** Vanilla JS + DOM API.
**Implements:** Sidebar Nav, Top Nav Bar.
**Avoids:** Over-Nesting (limit depth to 3 levels), Search Erasure and Poor Empty States.

### Phase 3: E2E Testing Integration
**Rationale:** Ensures UI properly interacts with backend logic in real-world scenarios, isolated from unit test phases for faster iteration.
**Delivers:** Full UI test coverage for navigation, drill-down, and global search workflows.
**Uses:** `pytest-playwright`.
**Implements:** `tests/frontend/test_ui.py`.
**Avoids:** Flaky Playwright Tests (by ensuring web-first assertions are properly enforced at the end of the project cycle).

### Phase Ordering Rationale

- Building backend APIs first ensures frontend development doesn't rely on brittle mock data and guarantees structural constraints are enforced early.
- Moving frontend implementation to Phase 2 guarantees true filesystem mappings.
- Finalizing with Playwright E2E testing ensures regression safety across both layers without slowing down the initial API test-driven development (TDD) loop.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1:** In-memory caching strategies or SQLite indexing when directory sizes scale up to 100k files to prevent search API bottlenecking.

Phases with standard patterns (skip research-phase):
- **Phase 2 & Phase 3:** Vanilla JS DOM manipulation and Playwright web-first locators are well-documented and standard.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Pytest tools and vanilla JS are established patterns perfectly matching the project's dependency constraints. |
| Features | HIGH | Clear mapping of table stakes vs. differentiators based on MVP requirements. |
| Architecture | HIGH | Standard REST approach coupled with lazy loading directly addresses expected scaling concerns. |
| Pitfalls | HIGH | Deep understanding of `pylnk3` and testing edge cases ensures robust mitigations. |

**Overall confidence:** HIGH

### Gaps to Address

- **Large-scale caching logic**: The exact implementation for caching thousands of `state.json` file scans on startup vs. maintaining a background indexer requires validation during Phase 1 execution.

## Sources

### Primary (HIGH confidence)
- Context7 library ID — `pytest-playwright` (0.9.0), `httpx` (0.28.1), `pytest-asyncio` (1.4.0) verified versions.
- Project Context (`PROJECT.md`) — Current stack uses vanilla JS and FastAPI; Windows `.lnk` constraints.

### Secondary (MEDIUM confidence)
- UI/UX pattern research — Guidelines on hierarchical drill-down sidebars and debounced global search behavior.
- Pytest and Playwright Documentation — File system mocking (`pyfakefs`, `tmp_path`) and web-first testing assertions.

---
*Research completed: 2026-09-02*
*Ready for roadmap: yes*
