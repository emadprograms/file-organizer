# Phase 111: Segregated Tenancy & Applicant Register UI - Context

**Gathered:** 2026-09-13
**Status:** Ready for planning
**Mode:** Autonomous execution

<domain>
## Phase Boundary

Phase 111 delivers the user interface presentation in House Profile (`house-profile.js`):
- **REG-01**: Update House Profile (`house-profile.js`) to segregate the Tenancy Register into two distinct visual sections: **المستأجرون المقيمون** (Resident Tenants: Current with tenure colors & Past sorted by vacate date) and **سجل المتقدمين وطلبات التخصيص** (Applicants & Unfulfilled Allocations).
- **REG-02**: Implement distinctive card styling for applicants featuring an `📋 متقدم (لم يسكن)` badge, application/order date, document count, and optional notes (e.g. `ألغي التخصيص`, `لم يستلم المفتاح`).
- **REG-03**: Enable clicking an applicant's card in House Profile to navigate directly to their dedicated category folders (`03 - أمر تخصيص`, `02 - بيانات شخصية`, etc.) in Folders view.

</domain>

<decisions>
## Implementation Decisions

### 1. Segregated Sections in House Profile
- In `renderHouseProfile(profile)`:
  - Separate `profile.tenants` into two groups:
    - `residents = profile.tenants.filter(t => t.is_resident === 1 || t.is_resident === undefined || t.is_resident === true);`
    - `applicants = profile.tenants.filter(t => t.is_resident === 0 || t.is_resident === false);`
  - Section 1: **المستأجرون المقيمون**
    - Displays active and past resident cards with their existing tenure color themes (`short` emerald green, `medium` amber yellow, `long` rose red, and past neutral slate).
    - If `residents.length === 0`, display empty resident message: "لا يوجد مستأجرون مقيمون مسجلون لهذا المنزل حالياً."
    - Section header displayed with resident icon and count pill.
  - Section 2: **سجل المتقدمين وطلبات التخصيص**
    - Rendered when `applicants.length > 0` (or empty section note if desired, but cleanly rendered with header when applicants exist).
    - Distinct header: clipboard icon, "سجل المتقدمين وطلبات التخصيص", count badge.

### 2. Applicant Card Styling (REG-02)
- Dashed border with subtle purple/indigo theme:
  `applicant-profile-card tenant-profile-card p-3 rounded-xl border border-dashed border-purple-200 dark:border-purple-800/60 bg-purple-50/20 dark:bg-purple-950/20 hover:border-purple-400 hover:bg-purple-50/40 transition-all cursor-pointer group shadow-2xs hover:shadow-sm`
- Avatar:
  Clipboard document icon with purple background:
  `<div class="w-8 h-8 rounded-lg bg-purple-100/80 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 flex items-center justify-center flex-shrink-0">...</div>`
- Badge:
  `<span class="applicant-badge inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border border-purple-200 dark:border-purple-800/60 bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300">📋 متقدم (لم يسكن)</span>`
- Date row:
  `طلب / تخصيص: ${sDate}`
- Metric counts:
  Document count (`t.document_count`) and Category count (`t.category_count`).
- Notes callout:
  If `t.notes` is provided, render a compact amber or purple tag:
  `<div class="applicant-notes mt-1.5 text-[11px] text-amber-700 dark:text-amber-400 bg-amber-50/80 dark:bg-amber-950/40 px-2 py-0.5 rounded border border-amber-200/60 dark:border-amber-800/40 inline-flex items-center gap-1"><span class="font-medium">${t.notes}</span></div>`

### 3. Folder Navigation on Click (REG-03)
- Retain the exact click handler:
  `card.onclick = () => { window.location.hash = `#/area/${encodeURIComponent(profile.area_id)}/house/${encodeURIComponent(profile.house_id)}/tenant/${encodeURIComponent(profile.house_id + '_' + t.name)}`; };`
- Ensure applicants have dedicated folder browsing in Folders View, showing only documents assigned to that applicant.

### 4. Stats Badge Polish
- When applicants exist:
  `statsBadge.textContent = `${residents.length} مستأجرين · ${applicants.length} طلبات تخصيص · ${profile.archive.total_documents} وثيقة`;`

</decisions>

<code_context>
## Existing Code Insights

- `src/HousingApplication.Web/wwwroot/js/house-profile.js`: Renders the house profile view.
- `tests/frontend/components/house_profile.test.js`: Contains Vitest unit tests for house profile rendering.

</code_context>

<specifics>
## Specific Requirements

- Existing tests in `house_profile.test.js` must continue passing without breakage.
- New unit tests verifying the segregated sections, applicant card classes, badges, notes, and click navigation must be added.

</specifics>
