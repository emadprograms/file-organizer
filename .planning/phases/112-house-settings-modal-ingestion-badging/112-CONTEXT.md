# Phase 112: House Settings Modal & Ingestion Badging - Context

**Gathered:** 2026-09-13
**Status:** Ready for planning
**Mode:** Autonomous execution

<domain>
## Phase Boundary

Phase 112 delivers:
- **SET-01**: Update House Settings modal (`#tenant-modal` in `tenant-manager.js` and `index.html`) to support adding/editing applicants via a Resident / Applicant toggle, automatically disabling/hiding "Present" and "End Date" and relabeling "Start Date" to "Application / Order Date".
- **ING-01**: Update Ingest Station (`ingest-station.js`), Batch Move, and Batch Copy modals (`categories-view.js`) to clearly group or badge applicant options in tenant dropdowns (`📋 فلان (متقدم - لم يسكن)`).
- **TIM-01**: Display an applicant badge in Timeline View (`timeline-view.js`) and Command Palette search results (`command-palette.js`) for documents and tenants belonging to applicants.

</domain>

<decisions>
## Implementation Decisions

### 1. House Settings Modal (`tenant-manager.js` & `index.html`)
- In `tenant-manager.js`:
  - Each tenant row in `tenantModalRows` (`addTenantRow(t)`) will include a type selector (`.tenant-type-select`):
    `<select class="tenant-type-select ..."><option value="resident">🏠 Resident • مقيم</option><option value="applicant">📋 Applicant • متقدم (لم يسكن)</option></select>`
  - When `type === 'applicant'` (`is_resident = 0`):
    - Present checkbox (`.tenant-present-check`) is disabled, unchecked, and styled with `cursor-not-allowed opacity-30`.
    - End date input (`.tenant-end-input`) is disabled, cleared, and styled with `cursor-not-allowed bg-slate-100 text-slate-400`.
    - Start date input (`.tenant-start-input`) title and placeholder relabeled to `Application / Order Date • تاريخ الطلب/التخصيص`.
    - Optional notes input (`.tenant-notes-input`) stores/edits `t.notes`.
  - When `type === 'resident'` (`is_resident = 1`):
    - Present checkbox is enabled.
    - End date input is enabled (unless Present is checked).
    - Start date input title is `Start Date • تاريخ البدء`.
  - When saving (`saveTenantsAndReallocate`):
    - Reads `is_resident = typeSelect.value === 'applicant' ? 0 : 1`.
    - Reads `notes = notesInput ? notesInput.value.trim() || null : null`.
    - Passes `is_resident` and `notes` in `tenantsPayload` sent to `POST /api/areas/{area}/houses/{house}/tenants`.
- In `index.html`:
  - Update table headers in `#tenant-modal` to include `Type • النوع` column alongside Name, Dates, Present, and Delete.

### 2. Ingest Station & Batch Move/Copy Dropdowns (ING-01)
- In `ingest-station.js`:
  - In `populateHousebatchTenantSelect` and `populateTenants`:
    - When `t.is_resident === 0 || t.is_resident === false`, format option text as:
      `📋 ${t.name} (متقدم - لم يسكن)`
    - In `resolveLatestTenant`: filter `candidates = residentTenants.length > 0 ? residentTenants : tenants;` so applicants are never auto-selected as latest tenant when residents exist.
- In `categories-view.js`:
  - In `formatBatchTenantLabel(t)`:
    - If `t.is_resident === 0 || t.is_resident === false`, return `📋 ${t.name || 'Applicant'} (متقدم - لم يسكن)`.

### 3. Timeline View & Command Palette Badges (TIM-01)
- In `HousingApplication.Web`:
  - In `TimelineItemDto`: add `[JsonPropertyName("is_resident")] public int IsResident { get; init; } = 1;`.
  - In `FileOrganizerRepository.GetTimelineAsync`: select `COALESCE(t.is_resident, 1) AS IsResident` and map to DTO.
- In `timeline-view.js`:
  - When rendering document cards in timeline, if `doc.is_resident === 0 || doc.is_resident === false`, render purple applicant badge:
    `<span class="bg-purple-50 text-purple-700 px-2 py-0.5 rounded-md font-medium text-[10px] border border-purple-200 truncate max-w-[140px] flex items-center gap-1" title="متقدم (لم يسكن)"><span class="w-1.5 h-1.5 rounded-full bg-purple-500"></span>${escapeHtml(doc.primary_tenant || 'No Tenant')}</span>`
- In `command-palette.js`:
  - When rendering tenant search results, if `t.is_resident === 0 || t.isResident === 0 || t.is_resident === false`:
    - Avatar shows `📋` in purple box.
    - Theme applies purple card border and badge.
    - Extra info shows `📋 متقدم (لم يسكن)` or `طلب تخصيص`.

</decisions>

<code_context>
## Existing Code Insights

- `src/HousingApplication.Web/wwwroot/js/tenant-manager.js`: Controls house settings modal.
- `src/HousingApplication.Web/wwwroot/js/ingest-station.js`: Ingestion dropdowns.
- `src/HousingApplication.Web/wwwroot/js/categories-view.js`: Batch move/copy modals.
- `src/HousingApplication.Web/wwwroot/js/timeline-view.js`: Timeline document cards.
- `src/HousingApplication.Web/wwwroot/js/command-palette.js`: Spotlight command palette results.
- `tests/frontend/components/house_settings_modal.test.js`: Tests for house settings modal.

</code_context>

<specifics>
## Specific Requirements

- Existing tests for house settings modal, batch operations, ingest station, and command palette must continue passing.
- New unit tests for applicant toggle, disabled fields, dropdown badging, and timeline badges must be added.

</specifics>
