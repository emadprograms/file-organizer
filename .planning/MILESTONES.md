# Milestones History

## v10.0 Area Grid Overview & Tenure Visualization (Shipped: 2026-09-06)

**Phases completed:** 4 phases (88-91)

**Key accomplishments:**
- Built dual-view toggle supporting both classic Tree View and new Area Grid Overview.
- Designed responsive house card grid featuring current resident, tenure duration, and tenure color coding (<5y green, 5-10y yellow, >10y red).
- Implemented card metrics with total document counts and category breakdowns.
- Added smooth drill-down navigation from house cards into categories and timeline views with breadcrumb return.
- Resolved SMB mount filesystem hangs with intelligent in-memory TTL caching and fast regex scanning.
- Maintained 100% test pass rate with full Playwright E2E and backend integration suites.

---

## v9.0 Hierarchical Web Dashboard (Shipped: 2026-09-06)

**Phases completed:** 5 phases, 5 plans

**Key accomplishments:**
- Implemented 3-level hierarchical sidebar navigation (Area -> House -> Tenant) with deep URL linking and synchronized active node selection.
- Developed global search across houses, tenants, and full-text PDF documents with instant zero-click search dropdown and keyboard shortcuts (`Cmd/Ctrl+K`, `Esc`).
- Added Arabic-English phonetic intermixing and fuzzy matching for Arabic OCR names.
- Enhanced document viewer with PDF hover preview tooltips and tabbed Category / Timeline views.
- Created static IIS export pipeline (`tree.json`, `search_index.json`) for zero-Python runtime environments.
- Built comprehensive interaction test suite in `tests/frontend/`.

---

## v8.0 Web-Based File Viewer (Shipped: 2026-09-02)

**Phases completed:** 4 phases, 3 plans, 0 tasks

**Key accomplishments:**

- (none recorded)

---

## v5.2: Deep Architecture Integrity & Verification

**Shipped:** 2026-08-01

**Key Accomplishments:**

- Created robust `src/core/verification.py` module to deep-scan houses for file system integrity.
- Handled legacy artifacts, orphan vault files, missing shortcuts, and state vs. physical folder drift securely.
- Resolved tricky cross-platform edge cases involving Pytest mocked environments, `pylnk3`, and Windows long paths.
- Reached 100% passing test coverage (288 tests) across the entire system.

## v5.1: Polishing & Migration Cleanup

**Shipped:** 2026-08-01

**Key Accomplishments:**

- Unified `1_cleaned.json`, `2_grouped.json`, and `3_routed_and_finalized.json` into a single `state.json` file.
- Fixed the Timeline View document index numbering logic to properly jump indices relative to document page count.
- Expanded automated test coverage by refactoring tests away from legacy formats and creating `tests/test_live_e2e.py` targeting actual test sets.
- Fixed `pylnk3` Windows dependency resolution.
