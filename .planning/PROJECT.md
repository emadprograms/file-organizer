# Housing Application

## What This Is

A high-performance document management system and web dashboard for housing digital archives. It stores scanned documents in an immutable vault with relational SQLite metadata, delivering sub-10ms queries, dual Tree/Grid views, tenure color-coding, multi-tenant chronological timelines, category folder drill-downs, phonetic/fuzzy global search, in-browser PDF viewing, and one-click ZIP/PDF archive exports. Built natively on a pure ASP.NET Core 8.0 Minimal API architecture and vanilla JS, with zero Python runtime dependencies.

## Current Milestone: Complete (Ready for Next Milestone)

## Past Milestones

<details>
<summary>v16.1 Document-Anchored Tenancy Dates & Minimalist Register (Shipped: 2026-09-14)</summary>

- **Document-Anchored Start Dates (Phase 115):**
  - Tenant and applicant start dates are automatically anchored to their earliest document date in the archive (`MIN(primary_date)`), eliminating manual start date guessing and timeline date conflicts.
  - Zero-document edge case handled: brand new tenants/applicants allow null/empty start date upon creation, displaying "Auto (on first upload)" until their first document is uploaded, upon which start date snaps automatically.
- **User-Decided End Date & Tenancy Status (Phase 115):**
  - Retained user control over `end_date` and the `Present` checkbox in the House Settings modal.
  - Vacated date conflict checks continue to protect against accidental post-vacate filing for residents without restricting ongoing files.
- **Streamlined Minimalist House Profile Register (Phase 115):**
  - Re-architected the House Profile tenancy register into a clean two-tier layout:
    - Resident tenants at top with simple title: `المستأجرون` (Tenants).
    - Exactly 1 subtle divider line separating residents from applicants.
    - Applicants at bottom with simple title: `المتقدمون` (Applicants).
    - Completely stripped wordy boilerplate and confusing subtitle phrases.
- **Comprehensive Testing & Parity (Phase 115):**
  - Added unit tests in `RepositoryTests.cs` verifying start date anchoring to earliest document and null start date snapping on first upload.
  - Updated Vitest specifications across `applicant_workflow.test.js` and `house_profile.test.js`.
  - 161/161 .NET xUnit tests and 293/293 web tests passing cleanly (454 total).

</details>

<details>
<summary>v16.0 Settings Streamlining & Applicant Alignment (Shipped: 2026-09-13)</summary>

- **Tenant Modal UI Streamlining & Rebalancing (Phase 114):**
  - Removed redundant `Notes` column header from `#tenant-modal` in `index.html`.
  - Rebalanced the tenant management table into a clean 12-column responsive grid: Name (4 spans), Type (2 spans), Start/Application Date (2 spans), End Date (2 spans), Present checkbox (1 span), Delete action (1 span).
- **Tenant Manager Script & Payload Clean-Up (Phase 114):**
  - Removed `.tenant-notes-input` and its container from dynamic row creation in `tenant-manager.js`.
  - Maintained backward database compatibility by sending `notes: null` in `handleSaveTenants`.
  - Preserved fluid two-way switching between `Resident` (`is_resident = 1`) and `Applicant` (`is_resident = 0`).
- **Applicant Card Visual Simplification (Phase 114):**
  - Removed `.applicant-notes` badge from applicant profile card template in `house-profile.js`, keeping the cards focused on applicant name, application date, document count, and folder count.
- **Vacated Tenancy Backend Safeguard (Phase 114):**
  - Updated `Program.cs` `/api/ingest` date conflict check to explicitly require `resolvedTenant.IsResident == 1` before performing `TextUtils.IsDocDateAfterVacated`.
  - Guarantees non-residing applicants (`IsResident == 0`) never trigger false vacated warnings when files dated after allocation or application dates are uploaded.
- **Comprehensive Testing & Verification (Phase 114):**
  - Added unit test `PostIngest_ApplicantNonResident_WithFutureDate_DoesNotConflict_AndSucceeds` to `ApiEndpointTests.cs`.
  - Updated Vitest suites in `house_settings_modal.test.js`, `applicant_workflow.test.js`, and `house_profile.test.js`.
  - 159/159 .NET xUnit tests and 293/293 web tests passing cleanly.

</details>

<details>
<summary>v15.0 Decoupled .NET Core Architecture & Non-Residing Applicants Archive (Shipped: 2026-09-13)</summary>

- **Pure .NET 8.0 Minimal API Architecture & Python Elimination (Phase 109):**
  - Completely purged all Python runtime source files (`src/` Python, `.venv`, `requirements.txt`, `patch_index.py`, pytest files).
  - Restructured codebase into idiomatic .NET solution layout (`src/HousingApplication.Web/` and `HousingApplication.sln`).
  - Consolidated backend testing under `tests/HousingApplication.Tests/` and re-anchored Vitest frontend tests to load assets directly from `src/HousingApplication.Web/wwwroot/js/`.
  - Updated `run-mac.sh` and `package.json` for pure .NET operation with zero Python dependencies.
- **Database Schema Additions & Vacancy Guardrails (Phase 110):**
  - Extended SQLite `tenants` table with `is_resident INTEGER NOT NULL DEFAULT 1` and `notes TEXT`, complete with automated idempotent migrations in `DatabaseInitializer.cs`.
  - Guarded house occupancy queries so that only residing tenants (`is_resident = 1`) count towards occupancy; houses with only non-residing applicants/unfulfilled allocations remain styled as `Vacant` (`grey`).
  - Guarded document auto-reallocation (`BulkUpdateTenantsAsync`) so date-window matching and default fallback strictly exclude non-residing applicants, preventing general house/utility documents from being misassigned to applicants.
- **Segregated House Profile UI (Phase 111):**
  - Segregated the House Profile tenancy register into two visually distinct sections: **المستأجرون المقيمون** (Resident Tenants) and **سجل المتقدمين وطلبات التخصيص** (Applicants & Unfulfilled Allocations).
  - Implemented distinctive applicant cards with `📋 متقدم (لم يسكن)` badge, application/order date, document count, and notes (e.g. `ألغي التخصيص`, `لم يستلم المفتاح`).
  - Enabled direct drill-down navigation from applicant cards into their category folders.
- **House Settings Modal Toggle & Ingestion Badging (Phase 112):**
  - Added Resident / Applicant toggle in House Settings modal (`#tenant-modal`), automatically hiding/disabling "Present" and "End Date" fields and relabeling "Start Date" to "Application / Order Date".
  - Badged applicant options across Ingest Station, Batch Move, and Batch Copy modals (`📋 فلان (متقدم - لم يسكن)`).
  - Displayed purple applicant badges in Timeline view and Command Palette (`⌘K`) search results.
- **Comprehensive Verification & Milestone Audit (Phase 113):**
  - 158 backend xUnit tests (100% passing) and 293 frontend Vitest tests across 28 test files (100% passing).
  - Full milestone audit passed with 17/17 requirements validated.

</details>

<details>
<summary>v14.0 Power-User Operations & Portfolio Expansion (Shipped: 2026-09-12)</summary>

- **One-Click House Archive Export & Chronological Dossier (Phase 105 + Quick Refinements QCK-01, QCK-03, QCK-04):**
  - Categorized ZIP Archive Export (`GET /api/areas/{area}/houses/{house}/export-zip` across FastAPI & ASP.NET Core) streaming collision-free ZIP archives with standard 2-digit folder numbering normalization (`FOLDER_PREFIXES` ensuring proper `01 - `, `05 - `, `06 - ` prefixes).
  - Interactive Export Options Modal (`#export-archive-modal`): Selectable Format Cards (Format Card A: Categorized ZIP Archive; Format Card B: Combined Chronological PDF Dossier with recent documents first) and Tenancy Scope Filter (All Tenants / Full House Record vs Individual active/past tenant).
  - Combined Chronological PDF Dossier (`GET /api/areas/{area}/houses/{house}/export-pdf` via PyMuPDF in Python and PdfSharpCore in .NET) with descending chronological sort (most recent document on Page 1, older documents towards the back, undated at the end).
  - Minimalist 3-Column Running Footer on every page of the PDF dossier:
    - Bottom-Left: Document primary filing date (`YYYY-MM-DD`), blank if undated.
    - Bottom-Center: Category name with number prefix preserved (e.g. `05 - عقود`, `06 - كهرباء وماء`).
    - Bottom-Right: Group & Master pagination `X/Y  (Z)` (e.g. `1/3  (14)`).
    - Typography & Layout: 7.5 pt muted slate gray (`#64748b`), 16 pt margin, zero verbose labels (no "Date:", "Category:", "Page:").
  - Arabic Cursive Text Shaping & BiDi Visual Reordering (QCK-04):
    - Python FastAPI (`src/api/routes.py`): Leverages `arabic-reshaper` + `python-bidi` (`get_display(arabic_reshaper.reshape(cat))`), preventing disjointed "terminal Arabic" letters and calculating precise text width for 100% centered rendering.
    - ASP.NET Core 8.0 (`web-net/Common/ArabicReshaper.cs` & `web-net/Program.cs`): Implements zero-dependency pure C# `ArabicReshaper.ReshapeAndReorder` mapping standard Arabic characters (`\u0600`–`\u06FF`) to Unicode Presentation Forms-B (`\uFE80`–`\uFEFC`), supporting dual-joining letters, right-joining letters, Lam-Alef ligatures (`لا`, `لأ`, `لإ`, `لآ`), and BiDi visual run reversal while preserving LTR numeric tokens (`05 - `) and mirroring bracket punctuation.
- **Multi-Select Batch Document Operations (Phase 106 + Quick Refinements QCK-02, QCK-08):**
  - Multi-select checkbox UI on document cards, folder-level toggle, and global Select All / Deselect All.
  - Glassmorphism dark floating action dock (`#batch-action-bar`) with dynamic selection counter and quick action buttons (`[ Move Selected ]`, `[ Copy Selected ]`, `[ Delete Selected ]`, `[ Deselect ]`).
  - Batch Move (`POST .../batch-move`): Atomic relocation to target standard or custom folder with optional target tenant reassignment (`target_tenant_id`).
  - Batch Delete (`POST .../batch-delete`): Cascade deletion with confirmation modal and vault file unlinking.
  - Batch Copy (`POST .../batch-copy`): Copies documents to an additional category folder for instant reference with optional target tenant reassignment.
  - Timeline De-duplication Architecture: Added `is_timeline_visible INTEGER DEFAULT 1` to `documents` table with automatic column migrations across Python and C#; secondary copies are automatically stored with `is_timeline_visible = 0`; timeline queries filter out copies so the timeline strictly reflects 1 real-world event per row (zero duplicate clutter); single 3-dot Copy (`POST .../documents/{vault_id}/copy`) also unified with `is_timeline_visible = 0`; physical vault storage stores 1 physical file without wasteful disk duplication.
- **Portfolio Expansion (Phase 107):**
  - "+ Add House" UI trigger and modal (`#add-house-modal`) in the Area Grid overview.
  - Backend endpoint `POST /api/areas/{area}/houses` across FastAPI & ASP.NET Core with conflict detection (409 on duplicates).
  - Automatic physical directory scaffolding (`{area}/{house}/batches/` and `{area}/{house}/vault/`).
  - Dynamic grid refresh without full page reload.
- **Global Keyboard Shortcuts Helper Modal (Phase 108):**
  - Pressing `?` or Shift+/ opens `#keyboard-shortcuts-modal` displaying `⌘K` Search, `⌘I` Ingest, `Space` Quick Look, `Esc` Close, `?` Shortcuts.
  - Subtle navbar trigger button (`#btn-shortcuts-trigger`).
  - Strict input/textarea typing suppression guards and backdrop/Escape dismissal.
- **Double-Click Inline Document Renaming (Quick Refinement QCK-05):**
  - Instant inline document title renaming triggered by double-clicking the title text in both Categories view folder lists and the chronological Timeline view.
  - Prominent, comfortable input styling (`text-sm font-medium`, `px-3 py-1.5`, ~34px height, `border-2 border-blue-500 rounded-lg shadow-sm`) with `dir="auto"` for bidirectional Arabic/English alignment.
  - Full-width row expansion (`flex-1 min-w-0` on container spans and headings) preventing input collapse on short filenames, with automatic removal of `truncate` / `line-clamp-2` during active editing.
  - Keyboard shortcuts and accessibility: `Enter` to commit changes, `Escape` to cancel and revert without network traffic, and `blur` to save or restore.
  - Event isolation: stops event propagation on `click`, `dblclick`, `mousedown`, `dragstart`, and keyboard events to prevent accidental parent card selection, card click opening, or drag-and-drop triggering while typing.
  - Dual-backend integration: calls `PATCH /api/areas/{area}/houses/{house}/documents/{vault_id}` with `{ "arabic_title": newTitle }`, updating in-memory document state (`brief_arabic_title`, `filename`), DOM text, and providing toast notifications on success/error.
- **Export Button Relocation & Archive Summary Box Removal (Quick Refinement QCK-06):**
  - Removed confusing and redundant digital archive summary box (`بيانات الأرشيف الرقمي للمنزل`) from the bottom of the House Profile, eliminating bottom visual clutter and keeping focus squarely on the Tenancy Register.
  - Relocated the Export House Archive button (`#btn-export-house-archive`) to the Document Panel header right beside `#btn-manage-tenants` for 0-scroll permanent visibility across all views (Profile, Folders, and Timeline).
  - Maintained full backward compatibility for `#btn-export-house-zip` and synchronized static assets across Python and ASP.NET Core with 0 diff.
- **Streamline Export Modal & Remove Batch Button Emojis (Quick Refinement QCK-07):**
  - Stripped verbose explanatory paragraphs from `#export-archive-modal` in favor of a minimalist, intuitive visual layout: streamlined header title (`تصدير الأرشيف • Export Archive`), large format icons (`📦 ZIP` with `مجلدات • Folders`, `📄 PDF` with `تسلسل زمني • Timeline`), clean tenant scope label (`المستأجر • Tenant`) with default option `🏛️ كامل السجل • All Records`, and action buttons (`Cancel` and `⬇️ Download`).
  - Polished `#batch-action-bar` by removing distracting button emojis (`📁`, `📋`, `🗑️`) from Move, Copy, and Delete while retaining `✕` on Deselect and keeping clear action labels ("Move Selected", "Copy Selected", "Delete Selected", "Deselect").
- **Batch Tenant Selection & Remove Copy Note (Quick Refinement QCK-08):**
  - Removed verbose amber explanatory note (`💡 ملاحظة: النسخ يتيح ظهور الوثائق في مجلد إضافي...`) from `#batch-copy-modal` without replacement.
  - Added Target Tenant dropdown (`المستأجر • Target Tenant`) to both Move Selected (`#batch-move-tenant-select`) and Copy Selected (`#batch-copy-tenant-select`) modals, defaulting to `🏛️ المستأجر الحالي للوثيقة • Same Tenant` (empty value, preserving existing tenancy).
  - Cleaned confirm button labels to `Move Documents` and `Copy Documents`.
  - Added dynamic tenant dropdown population (`populateBatchTenantSelect`) with active lease indicators (`🟢 ` vs `👤 `) and lease years, with graceful fallback to distinct tenants in `currentCategories`.
  - Added full dual-stack backend support for `target_tenant_id: Optional[int]` in both FastAPI and ASP.NET Core 8.0, allowing cross-tenant or same-tenant batch moves and copies.
- **Document 3-Dots Dropdown Action Menu & Folders Date Badge (Quick Refinement QCK-09):**
  - Replaced the large Document Action Modal (`#doc-action-modal`) when clicking the 3-dots button with an ergonomic floating context menu anchored to the trigger button (`.doc-dropdown-menu`).
  - Provided 5 direct action buttons: Rename Document (triggers inline rename), Move Document (`openBatchMoveForDoc`), Copy Document (`openBatchCopyForDoc`), Show in Timeline, and Delete Document (`handleDeleteSingleDoc`).
  - Added Show in Timeline navigation: switches to timeline view tab, clears conflicting tenant filters, smoothly scrolls target card to center viewport, pulses blue highlight (`ring-4 ring-blue-500 bg-blue-50`), and selects the document.
  - Added an always-visible document date badge with light gray background (`doc-date-badge bg-slate-100 text-slate-500 font-mono text-[10px]`) in the Folders / Categories section immediately preceding the 3-dots button.
- **Category Folder Circular Document Count Badge & Refined Document Date Sizing (Quick Refinement QCK-10):**
  - Replaced the folder header card document count text badge with a circular count badge (`.doc-count-badge min-w-[20px] h-5 rounded-full`) showing just the count number inside a circle with tooltip.
  - Refined document date badge on document rows in Categories view to `text-[9px] font-mono tracking-tight`, freeing ~12-15px horizontal width per row to prevent document title truncation while keeping the date crisp, legible, and neatly contained.
- **Category-Specific Folder Icons (01-13) & Empty Folder for Custom Categories (Quick Refinement QCK-11):**
  - Implemented distinct, descriptive Heroicons outline icons for each standard category 01 through 13 in Folders view (`FOLDER_ICONS`, `.folder-icon-box`, `getFolderIconSvg`), while retaining the clean empty folder icon for custom folders (14+).
- **Replace Folder "Select All" Text Button with Select Checkbox (Quick Refinement QCK-12):**
  - Replaced the text button `.btn-select-all-folder` on category folder cards with a select checkbox (`.folder-select-checkbox`) positioned right before `.folder-icon-box`, matching the document item checkbox styling.
  - Clicking this checkbox un-hides collapsed documents (`docsContainer.classList.remove('hidden')`) and selects all documents in the folder, or deselects all if already selected.
  - Added reactive synchronization: individual document checkbox changes update the parent folder's checkbox state to checked, indeterminate, or unchecked. Global select/deselect synchronizes all folder checkboxes across the view.
- **Harmonize Document Action Colors (Quick Refinement QCK-13):**
  - Standardized semantic color themes across document multi-select buttons, modals, and 3-dot dropdown menu items (Move: Amber, Copy: Indigo, Delete: Rose, Rename: Blue, Timeline: Emerald).
- **Tenure-Based Active Tenant Colors in Tenant Selection & House Overview (Quick Refinement QCK-14):**
  - Replaced the uniform hardcoded brand blue highlight for current/active tenants with dynamic tenure-duration-based colors matching the house overview standards across the entire tenant selection experience (`house-profile.js` and `area-grid.js`):
    - `< 5 years`: Emerald green (`short`, `bg-emerald-50`, `border-emerald-200`, `text-emerald-700`, `🟢`)
    - `5–10 years`: Amber yellow (`medium`, `bg-amber-50`, `border-amber-200`, `text-amber-700`, `🟡`)
    - `> 10 years`: Rose red (`long`, `bg-rose-50`, `border-rose-200`, `text-rose-700`, `🔴`)
    - Past tenants remain clean slate neutral (`bg-white`, `border-slate-200`, `text-slate-500`, `👤`).
  - Added dual-backend parity: dynamic computation of `duration_category` (`short`/`medium`/`long`) in FastAPI (`HouseTenantProfile.duration_category`) and ASP.NET Core (`HouseTenantProfileDto.DurationCategory`).
  - Dynamically updated export options modal tenant select options with duration category emojis (`🟢`, `🟡`, `🔴`).
- **Remove Redundant Emojis from Tenant Selection List and Folders Tab (Quick Refinement QCK-15):**
  - Removed redundant inline emojis (`📁` and `📋`) from the segmented tab buttons in the left Document List panel in favor of clean text labels (`Folders` and `سجل المستأجرين`).
  - Added dynamic SVG iconography (`#tab-categories-icon`) matching the Timeline tab's clean design: rendering the Users SVG icon (`M17 20h5...`) in tenant selection list state, and the Folder SVG icon (`M3 7v10...`) in category folders mode.
  - Cleaned emojis (`🏛️`, `🟢`, `🟡`, `🔴`, `👤`) from the export archive modal tenant dropdown options (`#export-archive-tenant-select`), ensuring unified minimalist typography across all views.
- **Merge Area Overview Headers into Single Top Bar (Quick Refinement QCK-16):**
  - Consolidated area overview controls (`#grid-area-stats` house count badge, tenure duration legend `< 5y | 5–10y | > 10y`, and `+ إضافة منزل جديد` add house button) directly into the primary application top navbar (`#top-navbar`).
  - Removed the redundant secondary sub-header bar inside `#area-grid-panel`, allowing the house cards grid to sit directly below the navbar and saving vertical screen real estate.
  - Dynamically showed/hid area overview navbar controls across `area-grid.js` and `router.js` upon house navigation or DB inspector mode.
- **Arabic Tenant Count Badge in Tenancy Register Header (Quick Refinement QCK-17):**
  - Replaced the bare digit in a tiny circle in the Tenancy Register header (`سجل المستأجرين المتعاقبين`) with an Arabic tenant count badge (e.g. `3 مستأجرين` or `1 مستأجر`).
  - Styled as a rounded pill (`.tenants-count-badge`, `px-2.5 py-0.5 rounded-full`) matching metadata standards across the application.
- **Delete House Feature in Settings Modal Danger Zone (Quick Refinement QCK-18):**
  - Implemented dual-backend `DELETE /api/areas/{areaId}/houses/{houseId}` across ASP.NET Core 8.0 and FastAPI with SQLite cascade deletion across 5 tables (`pages`, `documents`, `batches`, `tenants`, `houses`) and recursive directory removal on disk (`areas/{area}/{house}`).
  - Added red-themed Danger Zone container in House Settings & Tenants modal (`#tenant-modal`) with trigger button `#btn-open-delete-house`.
  - Built GitHub-style type-to-confirm modal `#delete-house-modal` requiring explicit typing of `delete <house_id>` to unlock the deletion button.
  - Automated post-deletion state reset (`currentHouse = null`, `currentTenant = null`), navigation back to Area Grid view, sidebar and grid refresh, and toast notification.
- **Remove Redundant Tenancy Register Sub-Header from Tenant Selection Area (Quick Refinement QCK-19):**
  - Removed the redundant inner sub-header bar (`tenantsHeader`) and Arabic count badge (`.tenants-count-badge`) from the tenant selection area inside `#document-list`.
  - Since the tab label above already identifies the section as `سجل المستأجرين` with the Users SVG icon (standardized in QCK-15), removing this repetitive secondary title (`سجل المستأجرين المتعاقبين`) and count badge eliminates visual clutter and allows tenant profile cards (`.tenant-profile-card`) to be positioned directly at the top of the container.
- **Add House Grid Card with Dashed Outline & Remove Top Navbar Button (Quick Refinement QCK-20):**
  - Replaced the top navbar Add House button with a modern dashed-outline "Add House" card (`#add-house-grid-card`) placed at the end of the houses list in Area Grid view.
  - Card features a prominent central plus icon, Arabic and English labels (`+ إضافة منزل جديد` / `Add New House`), and descriptive prompt (`انقر هنا لتسجيل منزل جديد في هذه المنطقة`), supporting both clicks and keyboard activation (`Enter` / `Space`) as well as empty area states.
  - Completely removed `#open-add-house-modal-btn` from the top navbar.
- **Make Pinned Lock Emoji and Text Smaller in Timeline View (Quick Refinement QCK-21):**
  - Scaled down the pinned status badge (`.doc-pinned-badge`) on manually assigned documents in the chronological Timeline view.
  - Wrapped the lock emoji in a dedicated span with `text-[8px] leading-none inline-block` to prevent oversized emoji rendering.
  - Reduced badge typography to `text-[8.5px] font-medium leading-none` with tightened padding and spacing (`gap-0.5`), keeping the pinned indicator crisp, lightweight, and non-distracting next to document titles.
- **Clean Up House Settings Modal Layout & Danger Zone (Quick Refinement QCK-22):**
  - Expanded House Settings modal (`#tenant-modal`) to `max-w-4xl` (896px), removed the massive explanatory note banner at the top, and reorganized into two clean sections: Section 1 (Tenants / المستأجرون) and Section 2 (Danger Zone / منطقة الخطر).
  - Corrected title to `House Settings: ${currentHouse} (${currentArea})` and subtitle to useful guidance: `Configure tenant residency timelines and house configuration`.
  - Strictly enforced single present tenant exclusivity: checking Present on one row automatically unchecks all other rows and re-enables their end date inputs, with new rows defaulting to not present when an active tenant exists.
  - Removed redundant outer border box around the Present checkbox, leaving a clean, standard, unobstructed checkbox.
  - Streamlined action buttons to clean English (`Add Tenant`, `Save Changes`, `Cancel`) without bulky Arabic text cluttering controls.
  - Eliminated bulky, oversized individual card boxes around each tenant row in favor of a single unified table container (`border border-slate-200 rounded-xl overflow-hidden`) with sleek row dividers (`divide-y divide-slate-100 py-2 px-4`).
  - Dedicated separate, generous columns with `gap-4` for Name (`col-span-4`), Start Date (`col-span-3`), End Date (`col-span-3`), Present (`col-span-1`), and Delete (`col-span-1`), ensuring ample horizontal spacing between Present and Delete.
  - Aligned Arabic deletion instructions in Danger Zone directly beneath the section title with left alignment, and removed trailing ellipsis from the `Delete House` button.
  - Added compact sequential tenant row numbering badges (`.tenant-row-number`: `1`, `2`, `3`) with automatic re-indexing via `updateRowNumbers()`, and removed repetitive uppercase labels inside rows.
- **Replace Tenant Selector with Category Badge in Document Viewer Header (Quick Refinement QCK-23):**
  - Replaced the misplaced `#viewer-tenant-select` and `#viewer-tenant-label` in the document viewer and Live Peek header with a dedicated `#viewer-category-badge` displaying the document's category folder with a crisp folder icon.
  - Enforced multi-source category resolution across Categories view, Timeline view, Live Peek hover, macOS Spacebar Quick Look, and Command Palette (`⌘K`), automatically resolving from arguments, timeline items, active selection, or global tree data.
  - Deprecated legacy tenant dropdown functions to safe no-op stubs and added unit tests in `tests/web/components/doc_viewer.test.js`.
- **Comprehensive Multi-Stack Test Coverage & Verification:**
  - 85 ASP.NET Core xUnit tests (`web-net/FileOrganizer.Tests/`, including 32 in `ArabicReshaperTests.cs`).
  - 33 Python backend tests (18 in `tests/test_v14_features.py`, 13 in `tests/test_document_management_api.py`, 2 in `tests/test_house_profile_api.py`).
  - 176 Frontend Vitest tests across 19 files (`npm run test:web`).
  - 49 Playwright Browser E2E tests.
  - Zero static asset diff between `src/api/static/`, `web-net/wwwroot/`, and `dist/win-x64/wwwroot/`.

</details>

<details>
<summary>v13.0 Decoupled Monorepo Architecture & Native ASP.NET Core Web Server (Shipped: 2026-09-09)</summary>

- Decoupled user-facing web dashboard completely from Python runtime into ASP.NET Core 8.0 Minimal API backend (`web-net/`).
- Implemented high-performance data access layer with Dapper and `Microsoft.Data.Sqlite` in WAL mode (`organizer.db`).
- Achieved 100% JSON API parity across `/api/tree`, `/api/houses`, `/api/timeline`, `/api/categories`, `/api/tenants`, `/api/search`, and `/api/pdf/{vault_id}`.
- Zero-Python manual ingestion endpoint (`POST /api/ingest`) directly writing vault PDFs and SQLite records in .NET.
- Zero frontend rewrite: existing vanilla JS/HTML dashboard served directly from `wwwroot/` with correct MIME types.
- Generated and verified standalone self-contained Windows single-file executable (`dist/win-x64/FileOrganizer.Web.exe`) requiring zero runtime dependencies.
- Verified by 40 .NET tests, 62 pytest tests, and 61 Vitest tests (163 total passing tests).

</details>

<details>
<summary>v12.0 Unified Document Ingestion System (Shipped: 2026-09-09)</summary>

- Built zero-AI manual ingest engine with PyMuPDF page counting and instant execution (`src/ingest/manual_ingest.py`).
- Implemented relational page inheritance in SQLite `pages` table, linking batch pages with parent document metadata and `is_continuation` flag.
- Created FastAPI endpoints `POST /api/ingest` (modes: `manual`, `assisted`, `auto_split`) and `POST /api/ingest/preview-ai` with zero database or disk mutations on preview.
- Developed modern Ingest Station slide-over drawer with `⌘I` / `Ctrl+I` keyboard shortcut, fullscreen drag-and-drop dropzone, live PDF preview, mode switcher, and real-time UI refresh.
- Verified 100% test coverage across backend pytest (62 tests) and frontend Vitest (43 tests).

</details>

<details>
<summary>v11.0 Database Backend & Clean Storage Architecture (Shipped: 2026-09-09)</summary>

- Designed and implemented relational SQLite schema (`areas`, `houses`, `tenants`, `batches`, `pages`, `documents`) with WAL mode, foreign keys, cascading deletes, unique constraints, and performance indices (`src/db/`).
- Built idempotent migration pipeline (`src/migration/v11_migration.py`) restructuring legacy houses into clean `{house}/batches/` and `{house}/vault/` directories, eliminating `.lnk` shortcuts, legacy JSONs, and directory clutter.
- Redesigned multi-page scanned PDF ingestion (`src/ingest/v11_ingest.py`) to register batches and slice standalone vault PDFs directly, completely eliminating index shifting and the reconciliation loop.
- Rebuilt FastAPI backend (`/api/tree`, `/api/houses`, `/api/timeline`, `/api/categories`, `/api/search`) to execute indexed SQL queries directly in <10ms, eliminating SMB filesystem walks and memory caching overhead.
- Verified 100% feature parity with Playwright E2E UI suite (`tests/web/test_v11_e2e_db.py`) covering Tree View, Grid Overview, Tenure Color-Coding (<5y, 5–10y, >10y), Drill-Down, Search, and PDF previews.

</details>

<details>
<summary>v10.0 Area Grid Overview & Tenure Visualization (Shipped: 2026-09-06)</summary>

- Built dual-view toggle supporting both classic Tree View and new Area Grid Overview.
- Designed responsive house card grid featuring current resident, tenure duration, and tenure color coding (<5y green, 5-10y yellow, >10y red).
- Implemented card metrics with total document counts and category breakdowns.
- Added smooth drill-down navigation from house cards into categories and timeline views with breadcrumb return.
- Resolved SMB mount filesystem hangs with intelligent in-memory TTL caching and fast regex scanning.
- Maintained 100% test pass rate with full Playwright E2E and backend integration suites.

</details>

<details>
<summary>v9.0 Hierarchical Web Dashboard (Shipped: 2026-09-06)</summary>

- Hierarchical drill-down sidebar (Areas -> Houses -> Tenants/Timelines).
- Global search bar with Cmd/Ctrl+K, Esc, instant zero-click search dropdown.
- Arabic-English phonetic intermixing and OCR typo tolerance.
- Full-text document search inside PDF contents.
- PDF hover preview tooltips and static IIS export pipeline.
- Frontend interaction test suite.

</details>

<details>
<summary>v8.0 Web-Based File Viewer (Shipped: 2026-09-02)</summary>

- Initial web dashboard for document viewing and exploration.

</details>

## Core Value

Documents are safely stored once in an immutable vault with relational SQLite metadata, delivering sub-10ms queries, zero SMB network globbing, and an intuitive web interface for managing and reviewing multi-tenant household archives.

## Requirements

### Validated

- ✓ Completely remove all legacy Python source files, .venv, requirements.txt, and pytest files (ARCH-01) — v15.0
- ✓ Reorganize ASP.NET Core project into idiomatic `src/HousingApplication.Web/` with `HousingApplication.sln` (ARCH-02) — v15.0
- ✓ Consolidate test suites under `tests/` with backend in `tests/HousingApplication.Tests/` (ARCH-03) — v15.0
- ✓ Update all Vitest imports across `tests/web/` to load assets from `src/HousingApplication.Web/wwwroot/js/` (ARCH-04) — v15.0
- ✓ Update `run-mac.sh` and `package.json` to reference new paths with zero Python dependencies (ARCH-05) — v15.0
- ✓ SQLite database schema updated with `is_resident INTEGER NOT NULL DEFAULT 1` and `notes TEXT` with auto-migration (DB-01) — v15.0
- ✓ Data models, DTOs, and repository methods read, write, and serialize `is_resident` and `notes` (DB-02) — v15.0
- ✓ Occupancy subqueries strictly filter `is_resident = 1`, keeping houses with only applicants vacant (`grey`) (VCN-01) — v15.0
- ✓ Auto-reallocation ignores non-residing applicants for date-window and default fallback matching (VCN-02) — v15.0
- ✓ Segregate House Profile Tenancy Register into Resident Tenants and Applicants / Unfulfilled Allocations (REG-01) — v15.0
- ✓ Distinctive applicant card styling featuring `📋 متقدم (لم يسكن)`, order date, doc counts, and notes (REG-02) — v15.0
- ✓ Clicking applicant card navigates into dedicated category folders view (REG-03) — v15.0
- ✓ House Settings modal supports adding/editing applicants via Resident/Applicant toggle with disabled fields (SET-01) — v15.0
- ✓ Ingest Station, Batch Move, and Batch Copy modals badge applicant options (ING-01) — v15.0
- ✓ Timeline View and Command Palette search results display applicant badge for documents and tenants (TIM-01) — v15.0
- ✓ Backend xUnit tests covering `is_resident` migrations, vacancy calculations, and reallocation guardrails (VER-01) — v15.0
- ✓ Frontend Vitest tests covering segregated register, applicant card rendering, settings modal, and ingest dropdowns (VER-02) — v15.0
- ✓ Full house archive ZIP export endpoint in FastAPI and ASP.NET Core (EXP-01) — v14.0
- ✓ UI Export Archive ZIP button on House Profile header with toast feedback (EXP-02) — v14.0
- ✓ Multi-select checkboxes and floating bottom action bar in category folders (BAT-01) — v14.0
- ✓ Batch Move and cascade Batch Delete endpoints in FastAPI and ASP.NET Core (BAT-02) — v14.0
- ✓ House creation backend endpoint with physical directory scaffolding (HSE-01) — v14.0
- ✓ "+ Add House" UI modal and dynamic live grid refresh in Area Grid (HSE-02) — v14.0
- ✓ Global Keyboard Shortcuts Helper Modal (`?`) and navbar trigger button (KBD-01) — v14.0
- ✓ Comprehensive multi-stack test suite across Pytest, xUnit, Vitest, Playwright (VER-07) — v14.0
- ✓ Interactive Export Options Modal & Chronological PDF Dossier with Tenancy Filter and 2-digit folder prefixes (QCK-01) — v14.0
- ✓ Multi-Select Batch Copy & Timeline De-duplication Architecture with `is_timeline_visible = 0` (QCK-02) — v14.0
- ✓ Descending Chronological Dossier Sort & Minimalist 3-Column Running Footer with Preserved Category Numbers (QCK-03) — v14.0
- ✓ Arabic Cursive Text Shaping & BiDi Visual Reordering in PDF Export Running Footer (QCK-04) — v14.0
- ✓ Double-click inline document renaming in Categories and Timeline views with Enter/Esc/blur shortcuts and toast feedback (QCK-05) — v14.0
- ✓ Relocation of Export button to Document Panel header and removal of redundant bottom archive summary (QCK-06) — v14.0
- ✓ Streamline export modal to intuitive visual-first layout and remove emojis from batch buttons (QCK-07) — v14.0
- ✓ Batch tenant selection in Move/Copy modals and target tenant assignment (QCK-08) — v14.0
- ✓ Document 3-dots dropdown context menu and always-visible folder date badge (QCK-09) — v14.0
- ✓ Category folder circular document count badge and refined date badge typography (QCK-10) — v14.0
- ✓ Category-specific outline folder icons (01-13) and empty folder fallback for custom categories (QCK-11) — v14.0
- ✓ Folder select checkbox revealing documents and selecting all (QCK-12) — v14.0
- ✓ Harmonized action colors between multi-select bar and 3-dots dropdown menu (QCK-13) — v14.0
- ✓ Tenure-based active tenant colors in tenant selection and house overview cards (QCK-14) — v14.0
- ✓ Clean dynamic SVG iconography in tabs and emoji elimination in modals (QCK-15) — v14.0
- ✓ Area overview controls merged into top navbar removing redundant secondary header (QCK-16) — v14.0
- ✓ Arabic tenant count pill badge in Tenancy Register header (QCK-17) — v14.0
- ✓ Delete house feature in settings modal Danger Zone with type-to-confirm validation (QCK-18) — v14.0
- ✓ Redundant tenancy register sub-header removed from tenant selection container (QCK-19) — v14.0
- ✓ Modern dashed-outline Add House grid card with prominent central plus icon (QCK-20) — v14.0
- ✓ Scaled down pinned lock badge with dedicated inline container in Timeline view (QCK-21) — v14.0
- ✓ Cleaned up House Settings modal layout, single active tenant exclusivity, and Danger Zone (QCK-22) — v14.0
- ✓ Replaced misplaced tenant selector with category badge in Document Viewer header (QCK-23) — v14.0
- ✓ Vertical scrollbar in house overview cards when > 3 tenancies exist (QCK-24) — v14.0
- ✓ Search tenant timeline color coding strictly reflecting active residency (QCK-25) — v14.0
- ✓ Phonetic consonant skeleton isolation and strict Latin/Arabic name precision (QCK-26) — v14.0
- ✓ Decoupled single document move/copy from multi-select batch state (QCK-27) — v14.0
- ✓ Preserved open category folders and scroll position on document move (QCK-28) — v14.0
- ✓ Database-wide real-world name validation and phonetic precision across 716 production tenants (QCK-29) — v14.0
- ✓ Arabic search optimization, Tashkeel/Tatweel stripping, and orthographic normalization (QCK-30) — v14.0
- ✓ Zero-motion and zero-state-shift document move and copy architecture (QCK-31) — v14.0
- ✓ Dynamic category folder lifecycle on move/copy with automatic DOM insertion/removal (QCK-32) — v14.0
- ✓ Comprehensive dark mode support with theme toggle, Shift+D, and FOUC prevention (QCK-33) — v14.0
- ✓ Touchscreen and mobile protection: touch-immune opening, double-click rename suppression, offline canvas PDF (QCK-34) — v14.0
- ✓ Touch press-and-hold drag-and-drop document move on tablets with haptic feedback (QCK-35) — v14.0
- ✓ Default move tenant to open folder, 3-dots pin toggle, and Timeline Show in Categories navigation (QCK-36) — v14.0
- ✓ Multi-select drag and drop for tablets and desktop computers (QCK-37) — v14.0
- ✓ Vacant house grey styling and false active tenant fallback removal (QCK-38) — v14.0
- ✓ Instant cross-tenant document move and DOM folder lifecycle (QCK-39) — v14.0
- ✓ Vacated tenant document date conflict detection and tenancy extension prompt (QCK-40) — v14.0
- ✓ Past tenants chronological sorting by vacate date (`end_date DESC, start_date DESC`) (QCK-41) — v14.0
- ✓ Header bar tenure legend Vacant indicator and full dark mode support (QCK-42) — v14.0
- ✓ Decoupled monorepo structure (`web-net/` for ASP.NET Core, `src/` for Python AI pipeline, shared `organizer.db`) (ARCH-01) — v13.0
- ✓ ASP.NET Core 8.0 project with Dapper and `Microsoft.Data.Sqlite` in WAL mode (NET-01) — v13.0
- ✓ Port all read API endpoints with 100% JSON parity (NET-02) — v13.0
- ✓ Implement zero-Python manual ingestion endpoint (`POST /api/ingest`) in .NET (NET-03) — v13.0
- ✓ Static file serving from `wwwroot/` with existing frontend assets (NET-04) — v13.0
- ✓ API parity test suite verifying response parity between Python and .NET backends (VER-05) — v13.0
- ✓ Windows self-contained single-file publish verification (`win-x64`) (VER-06) — v13.0
- ✓ Zero-AI manual ingest pipeline in Python with PyMuPDF page counting (ING-03) — v12.0
- ✓ Relational page inheritance for manual documents in SQLite pages table (ING-04) — v12.0
- ✓ FastAPI POST /api/ingest supporting manual, assisted, auto_split modes (API-04) — v12.0
- ✓ FastAPI POST /api/ingest/preview-ai with zero mutations on preview (API-05) — v12.0
- ✓ Top navbar + Ingest button with ⌘I / Ctrl+I and drag-and-drop dropzone (UI-01) — v12.0
- ✓ Ingest Station slide-over drawer with preview, mode switcher, live refresh (UI-02) — v12.0
- ✓ Backend pytest test suite for ingest pipeline, preview, and page inheritance (VER-03) — v12.0
- ✓ Frontend Vitest test suite for Ingest Station drawer, dropzone, mode switching, form submission (VER-04) — v12.0
- ✓ SQLite schema with FKs, cascading deletes, unique constraints, and indices (DB-01) — v11.0
- ✓ Data Access Layer / Repository with connection management and transactions (DB-02) — v11.0
- ✓ Idempotent migration pipeline ingesting state.json/report.json into SQLite (MIG-01) — v11.0
- ✓ Physical disk restructuring to batches/ and vault/, removing shortcuts and legacy JSONs (MIG-02) — v11.0
- ✓ Ingestion workflow registering batches and persisting pages (ING-01) — v11.0
- ✓ Direct PDF slicing into vault/ and documents records, eliminating index shifting (ING-02) — v11.0
- ✓ Rewrite /api/tree, /api/timeline, /api/categories to query SQLite with indexed joins (API-01) — v11.0
- ✓ Fast SQLite search endpoint /api/search across houses, tenants, and documents (API-02) — v11.0
- ✓ Sub-10ms query times eliminating SMB globbing and removing memory cache workarounds (API-03) — v11.0
- ✓ Full pytest test suite covering models, repository, migration, and ingestion (VER-01) — v11.0
- ✓ Playwright E2E verification confirming Tree View, Grid Overview, Timeline, Categories, PDF viewers (VER-02) — v11.0
- ✓ Dual-view toggle supporting Tree View and Area Grid Overview (Phase 88) — v10.0
- ✓ House card grid with current resident, tenure duration, and color-coding (Phase 89) — v10.0
- ✓ Card metrics with total document counts and category breakdowns (Phase 89) — v10.0
- ✓ Smooth drill-down navigation from house cards into categories and timeline (Phase 90) — v10.0
- ✓ Playwright E2E test suite for grid view and tenure badges (Phase 91) — v10.0
- ✓ 3-level hierarchical sidebar navigation (Area -> House -> Tenant) — v9.0
- ✓ Global search across houses, tenants, and PDF contents with keyboard shortcuts — v9.0
- ✓ Arabic-English phonetic intermixing and fuzzy matching — v9.0
- ✓ Vault storage system with unique document IDs — v5.0
- ✓ Modular restructuring (core, utils, tenant_config, grouping, timeline, routing) — v2.0
- ✓ Port file-categorizer OCR and Gemini logic to main repository — v3.0

### Active

(None — plan next milestone with /gsd-new-milestone)

### Out of Scope

- Client-side document mutation / editing (vault PDFs are immutable).
- Complex multi-master database replication (single SQLite file with WAL mode satisfies all performance requirements).
- Python runtime fallback (the application is 100% powered by native ASP.NET Core 8.0; dual-backend parity is deprecated).
- Automatic OCR classification of applicants (handled deterministically via manual ingestion or explicit assignment).

## Current State

- ✅ Shipped v15.0 Decoupled .NET Core Architecture & Non-Residing Applicants Archive on 2026-09-13.
- ✅ Shipped v14.0 Power-User Operations & Portfolio Expansion on 2026-09-12.
- ✅ Shipped v13.0 Decoupled Monorepo Architecture & Native ASP.NET Core Web Server on 2026-09-09.
- ✅ Shipped v12.0 Unified Document Ingestion System on 2026-09-09.
- ✅ Shipped v11.0 Database Backend & Clean Storage Architecture on 2026-09-09.
- Robust test coverage: 158 ASP.NET Core xUnit tests (100% passing) and 293 frontend Vitest tests across 28 test files (100% passing).
- Pure single-stack runtime: 100% native ASP.NET Core 8.0 Minimal API backend and static file server with zero Python runtime dependencies.

## Context

- The codebase has been transitioned from filesystem globbing and JSON state files to a high-performance SQLite relational database (`organizer.db`).
- Disk structure per house is simplified to `{area}/{house}/batches/` (scans) and `{area}/{house}/vault/` (sliced PDFs).
- All Windows `.lnk` shortcuts, nested Arabic directory trees, and `state.json`/`report.json` dependencies are replaced by SQLite records and fast SQL queries.
- Pure ASP.NET Core 8.0 minimal architecture powers both the web API and static dashboard without requiring Python or external runtimes.

## Key Decisions

| Decision | Rationale | Outcome |
|---|---|---|
| Pure .NET Core Architecture | Eliminated all Python dependencies, establishing high performance single-stack ASP.NET Core 8.0 Minimal API. | ✓ Completed (Milestone v15.0). |
| Single-Table Tenant/Applicant Union | Reused `tenants` table with `is_resident INTEGER` rather than creating separate applicant tables, preserving foreign key integrity and folder isolation. | ✓ Completed (Phase 110). |
| Vacancy & Allocation Guardrails | Houses with only non-residing applicants remain grey / vacant; document auto-reallocation strictly excludes non-residing applicants. | ✓ Completed (Phase 110). |
| Segregated Tenancy Register UI | Two visually distinct sections in House Profile separating resident tenants from applicants. | ✓ Completed (Phase 111). |
| Power-User Operations & Portfolio Expansion | Equip property managers with high-utility operations: one-click ZIP export, multi-select bulk operations, UI-based house creation, and global keyboard shortcuts. | ✓ Completed (Milestone v14.0). |
| Export Options Modal & Chronological PDF Dossier | Single entry point modal (`#export-archive-modal`) offering choice between categorized ZIP archive and merged chronological PDF dossier, with tenancy scope filtering and normalized 2-digit folder prefixes. | ✓ Completed (Phase 105 & QCK-01). |
| Timeline De-duplication Architecture | Copying documents to multiple category folders for cross-referencing sets `is_timeline_visible = 0`. Timeline queries filter copies so each physical event appears exactly once, avoiding timeline clutter while keeping category views complete. | ✓ Completed (QCK-02). |
| Minimalist 3-Column Running Footer & Descending Sort | Dossier PDF sorted newest-to-oldest with a 3-column running footer on every page (Date, Category with preserved 2-digit number prefix, Page X/Y) for seamless legal/administrative review and category cross-referencing. | ✓ Completed (QCK-03). |
| Arabic Cursive Shaping & BiDi Visual Reordering | PDF rendering engines lack complex script shaping and render raw Arabic characters as disconnected, isolated glyphs in LTR order. Mapped standard Arabic to Unicode Presentation Forms-B (`\uFE80`–`\uFEFC`) contextually with dual-joining, right-joining, and Lam-Alef ligatures, reversing Arabic runs while preserving LTR numeric tokens (`05 - `) via `arabic-reshaper` + `python-bidi` in Python and zero-dependency `ArabicReshaper` in C#. | ✓ Completed (QCK-04). |
| Double-Click Inline Document Renaming | Enable property managers to quickly correct or refine document titles directly within folder and timeline lists without opening the full 3-dots action modal, isolated from card click and drag events. | ✓ Completed (QCK-05). |
| Export Button Header Relocation & Archive Summary Removal | House Profile bottom archive summary caused visual clutter and pushed download button below fold with multiple tenants. Relocated export button to Document Panel header beside Settings for 0-scroll visibility across all views (Profile, Folders, Timeline). | ✓ Completed (QCK-06). |
| Intuitive Visual-First Export Modal & Clean Batch Bar | Remove verbose explanatory text from export modal to emphasize intuitive visual hierarchy (`📦 ZIP`, `📄 PDF`, `🏛️ كامل السجل • All Records`), and eliminate distracting emojis from Move/Copy/Delete buttons while preserving `✕ Deselect` and clear action text. | ✓ Completed (QCK-07). |
| Decoupled Monorepo & ASP.NET Core Web Server | Decouple read-heavy web dashboard into a high-efficiency native .NET 8 binary (`web-net/`) using Dapper and SQLite in WAL mode. Preserves Python strictly for offline/batch AI ingestion while giving Windows servers a zero-Python runtime footprint. | ✓ Completed (Milestone v13.0). |
| SQLite Relational Schema | Single file with WAL mode provides ACID transactions, sub-10ms query execution, and eliminates SMB directory traversal overhead. | ✓ Completed (Phase 92). |
| Two-Folder Disk Structure (`batches/` and `vault/`) | Clear separation between raw scanned inputs and sliced standalone documents. Eliminates deep Arabic directory nesting. | ✓ Completed (Phase 93). |
| Ingestion Without Reconciler | Slicing directly into `vault/` and recording in `documents` avoids index-shifting math and brittle two-way file moves. | ✓ Completed (Phase 94). |
| Direct SQL API Endpoints | Querying indexed SQLite tables instead of walking disk folders reduces tree rendering latency from seconds to <10ms. | ✓ Completed (Phase 95). |
| Playwright E2E Verification | Verifies real browser behavior against actual database records, guaranteeing zero regressions across Tree, Grid, Search, and PDF viewing. | ✓ Completed (Phase 96). |

---
*Last updated: 2026-09-13 after v15.0 milestone*
