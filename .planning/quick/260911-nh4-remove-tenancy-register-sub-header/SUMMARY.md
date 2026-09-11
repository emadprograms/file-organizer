---
status: complete
task_id: 260911-nh4
slug: remove-tenancy-register-sub-header
date: 2026-09-11
---

# Quick Task Summary: Remove Redundant Tenancy Register Sub-Header from Tenant Selection Area

**Task ID**: `260911-nh4` (QCK-19)  
**Status**: Complete  
**Date**: 2026-09-11  

---

## 1. Overview
In the tenant selection area (house profile view in `#document-list`), the segmented tab bar above already displays the tab label `سجل المستأجرين` alongside the Users SVG icon (standardized in QCK-15).
Inside `#document-list`, an inner sub-header bar previously repeated the title `سجل المستأجرين المتعاقبين` with a tenant count badge (e.g., `3 مستأجرين` or `1 مستأجر`).
This redundant inner sub-header has now been completely removed, allowing the tenant cards (`.tenant-profile-card`) to sit directly and cleanly at the top of the tenant selection area, saving vertical space and removing unnecessary repetition.

## 2. Changes Made
1. **`src/api/static/js/house-profile.js`**:
   - In `renderHouseProfile(profile)`: Removed `tenantsHeader` element creation, template string (`سجل المستأجرين المتعاقبين` and `.tenants-count-badge`), and `container.appendChild(tenantsHeader)`.
   - Adjusted `container.className = 'space-y-2 py-1';` so tenant cards list directly within `container`.
2. **`src/api/static/index.html`**:
   - Bumped cache bust version query string from `?v=260911-25` to `?v=260911-26` across all modular JavaScript files and stylesheets.
3. **Static Asset Tri-Directory Parity**:
   - Synchronized `src/api/static/` to `web-net/wwwroot/` and `dist/win-x64/wwwroot/`.
   - Verified 0 diff across all 3 directories.
4. **Automated Test Updates**:
   - `tests/frontend/components/house_profile.test.js`: Updated unit tests to assert absence of `سجل المستأجرين المتعاقبين` and `.tenants-count-badge`, and verified direct rendering of tenant cards.
   - `tests/frontend/test_house_register.py`: Updated Playwright assertions to verify direct rendering of `.tenant-profile-card` and absence of redundant text.
   - `tests/frontend/test_tabs.py`: Updated Playwright tab test to assert absence of redundant text.

## 3. Verification
- Vitest: 158 passed (16 files)
- ASP.NET Core xUnit: 85 passed
- Python Backend API (pytest): 33 passed
- Playwright E2E: Verified
