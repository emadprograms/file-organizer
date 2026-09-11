# Quick Task Plan: Remove Redundant Tenancy Register Sub-Header from Tenant Selection Area

**Task ID**: `260911-nh4` (QCK-19)  
**Description**: Remove redundant tenancy register sub-header (`سجل المستأجرين المتعاقبين` and `3 مستأجرين` badge) from the tenant selection area in `house-profile.js`  
**Date**: 2026-09-11  

---

## 1. Problem Statement
In the tenant selection area (house profile view in `#document-list`):
- The tab bar above already displays the tab label `سجل المستأجرين` accompanied by the Users SVG icon (standardized in QCK-15).
- Inside `#document-list`, an inner sub-header bar (`tenantsHeader`) currently repeats the title `سجل المستأجرين المتعاقبين` alongside an Arabic tenant count badge (e.g., `3 مستأجرين` or `1 مستأجر`).
- Having this secondary header bar immediately below the tab header is redundant, adds visual clutter, and consumes vertical screen real estate.
- Removing this inner sub-header allows the tenant cards (`.tenant-profile-card`) to be positioned cleanly and immediately at the top of the tenant selection area.

## 2. Proposed Changes

### 1. `src/api/static/js/house-profile.js`
- In `renderHouseProfile(profile)`:
  - Remove `tenantsHeader` element creation, template string (`سجل المستأجرين المتعاقبين` and `.tenants-count-badge`), and `container.appendChild(tenantsHeader)`.
  - Directly append `tenantsList` into `container`.
  - Adjust `container.className = 'space-y-2 py-1';` for clean spacing.

### 2. Static Asset Synchronization & Cache Bumping
- Bump asset cache version from `?v=260911-25` to `?v=260911-26` in `index.html` (scripts and stylesheets).
- Synchronize modified `house-profile.js` and `index.html` to `web-net/wwwroot/` and `dist/win-x64/wwwroot/`.
- Verify `diff -ru src/api/static/ web-net/wwwroot/` and `diff -ru src/api/static/ dist/win-x64/wwwroot/` report 0 differences.

### 3. Test Updates
- `tests/frontend/components/house_profile.test.js`:
  - Update tests to verify that `سجل المستأجرين المتعاقبين` and `.tenants-count-badge` are NOT rendered in `#document-list`.
  - Verify tenant cards are directly rendered and visible at the top.
- `tests/frontend/test_house_register.py`:
  - Update assertions on lines 175 and 226 from `#document-list` containing `"سجل المستأجرين المتعاقبين"` to asserting `.tenant-profile-card` is visible and `#tab-categories-label` contains `"سجل المستأجرين"`.
- `tests/frontend/test_tabs.py`:
  - Update line 127 from `#document-list` containing `"سجل المستأجرين المتعاقبين"` to checking `.tenant-profile-card` is visible.

### 4. Milestone Documentation & Audit Updates
- Update `STATE.md`, `PROJECT.md`, `ROADMAP.md`, `milestones/v14.0-ROADMAP.md`, `MILESTONES.md`, and `v14.0-MILESTONE-AUDIT.md` to document QCK-19.
