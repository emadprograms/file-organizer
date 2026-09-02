---
status: resolved
trigger: "the timeline is always for the entire house. not the specific tenant. so the first tab should be categories. second one timeline and the timeline should be the same for the entire house. update the tests and the code."
updated: 2026-09-02
---

# Debug Session: global-timeline

## Symptoms
- **Expected behavior**:
  1. The "Categories" tab should be the default first tab.
  2. The "Timeline" tab should be the second tab.
  3. The Timeline should always show all documents for the entire house, regardless of which tenant is selected in the sidebar.
  4. Clicking a tenant in the sidebar should switch the view to "Categories" to show their specific folders.
- **Actual behavior**: 
  - "Timeline" was the first default tab.
  - Clicking a tenant switched the tab to Timeline.
  - The Timeline filtered its view down to the selected tenant.
- **Error messages**: None.
- **Timeline**: Always.
- **Reproduction**: Click a house and observe default tabs and filtering behavior.

## Resolution
- **root_cause**: Frontend JavaScript state management intentionally favored the Timeline and applied `doc.primary_tenant === currentTenant` filtering locally before rendering.
- **fix**: 
  - Swapped the HTML tab buttons so Categories is visually first.
  - Changed `currentTab` initial state to `'categories'`.
  - Updated the `hashchange` routing logic: clicking a tenant now auto-switches `currentTab` to `'categories'` instead of `'timeline'`.
  - Removed the `if (currentTenant)` filter block inside `renderTimeline()`, ensuring `displayTimeline = currentTimeline` is always true.
  - Updated the Playwright frontend UI tests (`tests/frontend/test_tabs.py`) to assert the new default Categories load order, verify Timeline doesn't filter, and check the tenant click auto-switch to Categories.
- **verification**: Tests passed and manual review confirms the new layout and logic.
- **files_changed**:
  - `src/api/static/index.html`
  - `tests/frontend/test_tabs.py`
