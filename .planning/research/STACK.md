# Stack Research

**Domain:** File Organizer Dashboard (Web GUI & Testing)
**Researched:** 2026-09-02
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| pytest-playwright | 0.9.0 | E2E UI Testing | Seamless integration with existing `pytest` ecosystem; controls browser directly from Python tests. |
| httpx | 0.28.1 | Backend API Testing | Required for FastAPI's `TestClient` to test the new directory-scanning and search APIs asynchronously. |
| pytest-asyncio | 1.4.0 | Async Backend Testing | Enables native `async/await` in `pytest`, crucial for testing async FastAPI endpoints (like directory scanners). |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Vanilla JS + DOM API | N/A | Frontend Interactivity | For building the hierarchical drill-down sidebar and search bar without framework overhead. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| playwright install | Browser binaries | Run `playwright install` after installing `pytest-playwright` to fetch Chromium/Firefox/WebKit. |

## Installation

```bash
# Core and Testing Dependencies
pip install pytest-playwright httpx pytest-asyncio

# Install playwright browsers
playwright install
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| pytest-playwright | @playwright/test (Node.js) | If frontend tests needed to be completely decoupled from the Python backend and written in TypeScript. However, Python is heavily preferred given the project is Python-centric. |
| Vanilla JS | HTMX or Alpine.js | If the DOM manipulation for the hierarchical drill-down sidebar becomes too complex for vanilla JavaScript `document.createElement`. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| React / Vue / Angular | Massive bundle sizes and build steps for a simple sidebar/search, conflicting with the current lightweight `src/web` architecture. | Vanilla JS + DOM manipulation |
| Selenium | Slower and more complex setup for modern Web GUI testing compared to Playwright. | pytest-playwright |
| UI Component Libraries | Requires a frontend framework and adds unnecessary weight. | Custom CSS (`styles.css`) + existing Lucide icons |

## Stack Patterns by Variant

**If adding the hierarchical drill-down sidebar:**
- Use Vanilla JS recursive DOM rendering
- Because the data structure (Areas -> Houses -> Tenants) naturally maps to a nested JSON response from the API, which is trivial to iterate and render natively.

**If testing FastAPI directory-scanning APIs:**
- Use `TestClient` from `fastapi.testclient` powered by `httpx`
- Because it allows synchronous-style testing of async APIs directly alongside the database/vault mock tests.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| pytest-playwright | pytest | Both integrate cleanly, allowing unified test runs with a single `pytest` command. |
| httpx | fastapi | Native requirement for `TestClient` in recent FastAPI versions. |

## Sources

- Context7 library ID — pytest-playwright (0.9.0), httpx (0.28.1), pytest-asyncio (1.4.0) versions verified against current PyPI releases.
- Project Context (`PROJECT.md`) — current stack uses vanilla JS and FastAPI.

---
*Stack research for: Web GUI & Testing (v9.0)*
*Researched: 2026-09-02*
