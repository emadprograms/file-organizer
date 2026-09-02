# Pitfalls Research

**Domain:** Hierarchical Web Dashboard & Global Search (Document Viewer)
**Researched:** 2026-09-02
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: "Mocking Hell" in Directory Scanning APIs

**What goes wrong:**
Backend pytest tests for directory scanning and file retrieval become extremely brittle, passing locally but failing in CI or production. The tests miss real-world edge cases like Windows `.lnk` shortcut resolution.

**Why it happens:**
Developers manually mock `os.walk`, `os.listdir`, or `pathlib` using `unittest.mock.patch`, creating artificial environments that don't replicate true filesystem behaviors or the specific Vault/shortcut architecture of the app.

**How to avoid:**
Use the `pyfakefs` plugin or pytest's built-in `tmp_path` fixture to create real, isolated, in-memory file systems during tests. Ensure tests specifically create and resolve `.lnk` files (using `pylnk3`).

**Warning signs:**
Tests require 3+ `@patch` decorators for `os` functions; tests pass but production encounters Path/OS errors; heavy use of `mock_open`.

**Phase to address:**
Backend API Development

---

### Pitfall 2: Flaky Playwright Tests on Hierarchical Sidebars

**What goes wrong:**
E2E tests for the hierarchical sidebar fail intermittently. Developers resort to adding arbitrary `page.waitForTimeout()` delays or using `click({ force: true })` to force interactions, hiding actual UI bugs.

**Why it happens:**
Hierarchical menus rely on dynamic visibility and animations. Relying on deep CSS selectors (`div > ul > li > span`) or assuming synchronous rendering leads to race conditions.

**How to avoid:**
Use web-first assertions (`await expect(menu).toBeVisible()`) to automatically wait for animations. Use accessibility-based locators like `getByRole('treeitem')` and chain locators (`page.getByRole('navigation').getByRole('link')`) instead of deep CSS paths.

**Warning signs:**
Presence of `waitForTimeout` in test files; CI builds failing randomly on menu click steps; heavily nested CSS/XPath locators.

**Phase to address:**
Frontend E2E Testing

---

### Pitfall 3: Over-Nesting and Cognitive Overload in Sidebar

**What goes wrong:**
The sidebar perfectly mirrors the raw disk structure (Areas -> Houses -> Tenants -> Timelines -> Files) but becomes visually cluttered, requiring excessive clicking and vertical scrolling, overwhelming the user.

**Why it happens:**
Translating a 1-to-1 filesystem mapping directly into a UI component without accounting for interaction costs or visual space constraints.

**How to avoid:**
Limit sidebar depth to 2-3 levels (e.g., Areas -> Houses). Use the main content area for deeper drill-downs (like Tenants and Timelines). Implement clear visual hierarchy (collapsible sections, active state highlighting).

**Warning signs:**
Sidebar requires horizontal scrolling to read nested items; users lose context of their location; high visual noise.

**Phase to address:**
UI Specification / Frontend Implementation

---

### Pitfall 4: Search Erasure and Poor Empty States

**What goes wrong:**
When a user searches for a house number or person, the search input clears upon submission. If no results are found, they hit a dead-end "0 results" page with no suggestions, causing friction.

**Why it happens:**
Treating search as a stateless functional query rather than an iterative user journey.

**How to avoid:**
Keep the search query persistently in the search bar after execution. Implement fuzzy matching (e.g., ignoring exact Arabic name spellings/diacritics). Offer fallback suggestions or quick links to Areas when a search fails.

**Warning signs:**
Users manually typing the same query multiple times; high abandonment rate after search; no autocomplete or predictive text.

**Phase to address:**
Frontend Implementation / Backend Search API

---

### Pitfall 5: Global Search Ignoring Windows .lnk Architecture

**What goes wrong:**
The top navigation search bar successfully finds file names but fails to link them to the correct Vault document or resolve the actual target path, returning dead links or raw Vault IDs instead of contextual shortcuts.

**Why it happens:**
The backend search API is built as a generic text matcher and ignores the v5.0 architectural constraint where all organization relies on `.lnk` files pointing to immutable Vault storage.

**How to avoid:**
Ensure the backend search API resolves `.lnk` metadata and returns the contextual path (Tenant/Timeline) alongside the document reference, integrating with `pylnk3` during indexing or live searching.

**Warning signs:**
Search results are not clickable; clicking a search result downloads a `.lnk` file instead of rendering the PDF; duplicates appearing in search results.

**Phase to address:**
Backend API Development

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Using `unittest.mock` for file system | Faster initial test writing | Brittle tests that fail to catch Windows path/shortcut edge cases | Never for core file-system APIs |
| `{ force: true }` in Playwright | Bypasses flaky animation timeouts | Masks real bugs where menus are obscured or unclickable by users | Only as a temporary hack during early prototyping |
| Polling backend for directory tree | Simple to implement frontend state | High server load and UI lag when directories scale | Acceptable only for very small directory trees |

## Integration Gotchas

Common mistakes when connecting to external services or layers.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| API to File System | Returning absolute disk paths to frontend | Return relative/virtual paths mapped to the API route, hiding actual Windows disk structure |
| Frontend to API | Requesting the entire Area/House tree on load | Lazy-load children of the tree on-demand (when a node is expanded) |
| Playwright to App | Testing against a mock backend | Test against a real local instance running on a `tmp_path` file system with actual `.lnk` files |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Eager Loading Tree | App freezes on load, high network payload | Implement lazy loading (fetch node children only on expand) | 100+ houses / deep timelines |
| Naive Search API | Search takes >1 second, blocking UI | Use in-memory indexing or optimized caching instead of full disk walk per keystroke | Large tenant vaults (1000+ docs) |
| DOM Node Bloat | Sidebar lags when scrolling | Virtualize the tree component if rendering thousands of items | 500+ rendered tree items |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Path Traversal in APIs | Malicious requests accessing files outside `areas_root_path` | Sanitize inputs and strictly jail directory scanning APIs to the root path |
| Exposing Vault IDs | Users modifying vault internals manually via API | Keep Vault logic strictly on the backend; frontend should interact only via logical paths (Areas/Houses) |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Hiding Search | Users must click a menu to open search, reducing usage | Keep a wide, persistent search bar in the top navigation |
| No Active State | Users lose their place in the hierarchy | Clearly highlight the currently selected tree node and expand its parents |
| Mixing Interactions | Users accidentally trigger navigation when trying to expand a folder | Differentiate the "expand/collapse" chevron click from the "navigate" node click |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Search Bar:** Often missing persistent query retention — verify the input doesn't clear on Enter.
- [ ] **Tree Node Expansion:** Often missing visual loading indicators — verify a spinner shows during lazy load.
- [ ] **Playwright Tests:** Often missing accessibility locators — verify tests use `getByRole` rather than `.sidebar > ul > li`.
- [ ] **Windows Shortcuts:** Often missing `.lnk` resolution — verify the API returns actual document data, not binary `.lnk` files.

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Flaky E2E Tests | MEDIUM | Quarantine the test, rewrite using Web-First assertions, and remove `waitForTimeout` calls. |
| Slow Search API | HIGH | Replace real-time disk walking with a background indexer or cached SQLite mapping of the areas directory. |
| Path Traversal Bug | HIGH | Take API offline, implement strict path jailing (`os.path.commonpath`), and write specific security test cases. |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| "Mocking Hell" in Pytest | Backend API Phase | Review tests for `pyfakefs` or `tmp_path` usage over `patch`. |
| Global Search Ignoring `.lnk` | Backend API Phase | API tests verify search resolves to correct Vault document. |
| Flaky E2E Tests | Playwright E2E Phase | CI runs tests 10x without flakiness using web-first locators. |
| Over-Nesting Sidebar | Frontend UI Phase | UX review confirms max 2-3 levels deep in the sidebar. |
| Search Erasure / Empty States | Frontend UI Phase | E2E tests confirm search input retains text after submission. |

## Sources

- Playwright Best Practices (Web-First Assertions & Flakiness Prevention)
- Pytest File System Testing (`pyfakefs` documentation)
- Nielsen Norman Group (Search & Navigation UX guidelines)
- Project Context (v5.0 Windows `.lnk` Vault Architecture constraints)

---
*Pitfalls research for: Hierarchical Web Dashboard & Global Search*
*Researched: 2026-09-02*
