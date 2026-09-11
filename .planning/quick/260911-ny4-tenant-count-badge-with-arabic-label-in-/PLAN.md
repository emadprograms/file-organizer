# Quick Task Plan: Arabic Tenant Count Badge in Tenancy Register Header

**Task ID**: `260911-ny4`  
**Description**: Display tenant count with Arabic noun label (e.g., "3 مستأجرين") in the Tenancy Register header badge instead of just a raw number in a circle  
**Date**: 2026-09-11  

---

## 1. Problem Statement
In the tenant selection list (`#document-list` when a house is selected):
Below the tab bar, the header `سجل المستأجرين المتعاقبين` displayed a circular badge with only a raw numeric digit (e.g. `3`).
The user wants the badge to include the Arabic word for tenants (`3 مستأجرين`), formatted as an elegant pill badge.

## 2. Proposed Changes

### 1. `src/api/static/js/house-profile.js`
- In `renderHouseProfile`:
  - Calculate `tenantLabel = profile.tenants.length === 1 ? 'مستأجر' : 'مستأجرين'`.
  - Format the badge in `tenantsHeader` to display `${profile.tenants.length} ${tenantLabel}` (e.g. `3 مستأجرين`).
  - Adjust styling from a tight circular shape (`min-w-[20px] h-5`) to a comfortable rounded pill badge (`px-2.5 py-0.5 inline-flex items-center justify-center text-xs font-semibold text-slate-600 bg-slate-100 border border-slate-200 rounded-full`).
  - Add class `.tenants-count-badge` for clean selector targeting in tests.

### 2. Synchronization & Verification
- Synchronize `house-profile.js` to `web-net/wwwroot/js/house-profile.js` and `dist/win-x64/wwwroot/js/house-profile.js`.
- Add unit test in `tests/frontend/components/house_profile.test.js` asserting that the badge displays `${count} مستأجرين` (or `مستأجر`).
- Run Vitest suite (`npm run test:frontend`) and Playwright E2E suite (`pytest`).
- Update milestone documentation (`MILESTONES.md`, `PROJECT.md`, `ROADMAP.md`, `v14.0-MILESTONE-AUDIT.md`, `STATE.md`).
- Commit and push to origin.
