# Quick Task Plan: Remove Redundant Emojis from Tenant Selection List and Folders Tab

**Task ID**: `260911-nh3`  
**Description**: Remove emojis from tenant selection list and the folders tab, ensuring clean SVG iconography matching Timeline  
**Date**: 2026-09-11  

---

## 1. Problem Statement
In the segmented tab bar of the document panel:
- `tab-timeline` displays an SVG calendar/clock icon followed by clean text: `Timeline` (no emojis).
- `tab-categories` had an SVG icon followed by an emoji and text:
  - In tenant selection list state (house level): `[SVG icon] 📋 سجل المستأجرين`
  - In folders tab state (tenant level): `[SVG icon] 📁 Folders`
Because both states already have distinct SVG icons (like Timeline does), the inline emojis (`📋` and `📁`) are redundant and create visual inconsistency with Timeline.
Additionally, any tenant select options in the export modal (`🏛️`, `🟢`, `🟡`, `🔴`, `👤`) should be cleaned to maintain a minimalist typography.

## 2. Proposed Changes

### 1. `src/api/static/index.html`
- In `tab-categories`, change `<span id="tab-categories-label">📁 Folders</span>` to `<span id="tab-categories-label">Folders</span>`.
- Add `id="tab-categories-icon"` to the tab's `<svg>` element for reliable selection and dynamic icon toggling.
- In `#export-archive-modal`, remove `🏛️ ` from `<option value="">كامل السجل • All Records</option>`.

### 2. `src/api/static/js/router.js`
- In `selectHouse`:
  - Change `tabCategoriesLabel.textContent = tenantName ? 'Folders' : 'سجل المستأجرين';` (removing `📁 ` and `📋 `).
  - Dynamically switch `tab-categories-icon` SVG between Users icon (`M17 20h5...`) when in tenant selection mode and Folder icon (`M3 7v10...`) when in folders mode.

### 3. `src/api/static/js/house-profile.js`
- In `populateExportTenantSelect`, remove `theme.emoji` and `👤 ` prefixes from option text so tenant selection dropdown options are clean and consistent.

### 4. Static Asset Synchronization & Verification
- Synchronize modified files to `web-net/wwwroot/` and `dist/win-x64/wwwroot/`.
- Verify `diff -ru src/api/static/ web-net/wwwroot/` and `diff -ru src/api/static/ dist/win-x64/wwwroot/` are 0.
- Re-run all multi-stack tests (Vitest, xUnit, Pytest, Playwright).
