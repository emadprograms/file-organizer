# Quick Task Plan: Clean Up House Settings Modal & Danger Zone

**Task ID**: `260911-nh6` (QCK-22)  
**Description**: Streamline House Settings modal (`#tenant-modal`): remove massive top info notes, restructure into clean settings sections (Tenants vs Danger Zone), improve tenant row layout with aligned table columns, and clarify settings trigger.  
**Date**: 2026-09-11  

---

## 1. Problem Statement
The user raised several usability and visual issues with the House Settings experience:
1. **Unclear trigger intent**: The settings button title and modal title previously focused only on "Tenants", confusing users looking for general house settings and danger actions.
2. **Massive explanatory banner**: A large blue priority rules info banner at the top of the modal pushed content down and added visual noise.
3. **Disjointed tenant rows**: Each tenant row repeated loud uppercase labels (`NAME / الاسم`, `START DATE`, `END DATE`) with a misaligned `pt-5` checkbox and an orphaned "Add Tenant" button at the bottom.
4. **Random Danger Zone placement**: The Danger Zone box was unceremoniously dropped at the bottom of the scroll area without clear section hierarchy.

## 2. Proposed Changes

### 1. `src/api/static/index.html`
- In Document Panel header:
  - Enhance `#btn-manage-tenants` title to `House Settings • إعدادات المنزل` with clean hover styles.
- In `#tenant-modal`:
  - Widen modal dialog container from `max-w-3xl` to `max-w-4xl` (896px) for generous breathing room.
  - **Remove the massive top info note banner** completely.
  - Concise modal header: `#tenant-modal-title` ("Manage Tenants") and `#tenant-modal-subtitle` ("House Settings").
  - Structure body into distinct settings sections:
    - **Section 1 (Tenants / المستأجرون)**:
      - Section header with title, subtitle, and streamlined English-only `+ Add Tenant` button (`#btn-add-tenant-row`).
      - Unified table container (`border border-slate-200 rounded-xl overflow-hidden`) eliminating bulky, oversized per-row card borders.
      - Column headers with `gap-4`: `Tenant Name • اسم المستأجر` (`col-span-4`), `Start Date • تاريخ البدء` (`col-span-3`), `End Date • تاريخ الانتهاء` (`col-span-3`), `Present` (`col-span-1`), `Delete` (`col-span-1`).
      - Sleek `#tenant-modal-rows` container using subtle row dividers (`divide-y divide-slate-100`).
    - **Section Divider**: Subtle `border-t border-slate-200/80`.
    - **Section 2 (Danger Zone / منطقة الخطر)**:
      - Dedicated warning header with exclamation icon.
      - Danger card with clean title `Delete House • حذف المنزل`, zero verbose gray boilerplate sentences, and concise `Delete House...` action button.
  - Modal Footer: Streamlined English-only `Cancel` and `Save Changes` buttons.

### 2. `src/api/static/js/tenant-manager.js`
- In `openTenantModal`:
  - Set `tenantModalTitle.textContent = \`Manage Tenants: \${currentHouse} (\${currentArea})\``.
  - Set `#tenant-modal-subtitle` to `\${currentArea} • House \${currentHouse}`.
- In `addTenantRow`:
  - Modern, compact row layout (`sm:grid-cols-12 gap-4 px-4 py-2 hover:bg-slate-50/60 transition-colors`) without bloated individual card boxes or margins.
  - Compact inputs (`px-2.5 py-1.5 text-xs`) and sequential numbering badges (`.tenant-row-number`).
  - Dedicated centered `Present` toggle badge and `Delete` button separated by distinct whitespace.
  - Streamlined button states (`Saving...` / `Save Changes`) and concise validation/status messages.

### 3. Cache Busting & Tri-Directory Asset Synchronization
- Bump asset cache version to `?v=260911-30` in `index.html`.
- Synchronize `index.html` and `tenant-manager.js` to `web-net/wwwroot/` and `dist/win-x64/wwwroot/`.
- Verify `diff -ru src/api/static/ web-net/wwwroot/` and `diff -ru src/api/static/ dist/win-x64/wwwroot/` report 0 differences.

### 4. Automated Tests & Verification
- Create / update `tests/frontend/components/house_settings_modal.test.js` verifying:
  - Removal of massive top note banner and gray boilerplate text.
  - Streamlined title, subtitle, and English-only action buttons.
  - Clean table container and sleek tenant rows with row numbers and present toggle.
  - Distinct Danger Zone section.
- Re-run all test suites (Vitest, .NET xUnit, Python API pytest, Playwright E2E).

### 5. Milestone Documentation Updates
- Update `STATE.md`, `PROJECT.md`, `ROADMAP.md`, `milestones/v14.0-ROADMAP.md`, `MILESTONES.md`, and `v14.0-MILESTONE-AUDIT.md`.
