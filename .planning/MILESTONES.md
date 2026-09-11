# Milestones History

## v14.0 Power-User Operations & Portfolio Expansion (Shipped: 2026-09-10)

**Phases completed:** 4 phases (105-108) + 14 quick refinements (QCK-01 through QCK-14), 4 plans, comprehensive multi-stack test verification (84 .NET xUnit, 32 Pytest tests, 145 Vitest across 13 files, 49 Playwright E2E)

**Key accomplishments:**

- **Tenure-Based Active Tenant Colors in Tenant Selection & House Overview (Quick Refinement QCK-14):**
  - Replaced the uniform hardcoded brand blue highlight for current/active tenants with dynamic tenure-duration-based colors matching the house overview standards across the entire tenant selection experience (`house-profile.js` and `area-grid.js`):
    - `< 5 years`: Emerald green (`short`, `bg-emerald-50`, `border-emerald-200`, `text-emerald-700`, `🟢`)
    - `5–10 years`: Amber yellow (`medium`, `bg-amber-50`, `border-amber-200`, `text-amber-700`, `🟡`)
    - `> 10 years`: Rose red (`long`, `bg-rose-50`, `border-rose-200`, `text-rose-700`, `🔴`)
    - Past tenants remain clean slate neutral (`bg-white`, `border-slate-200`, `text-slate-500`, `👤`).
  - Added dual-backend parity: dynamic computation of `duration_category` (`short`/`medium`/`long`) in FastAPI (`HouseTenantProfile.duration_category`) and ASP.NET Core (`HouseTenantProfileDto.DurationCategory`).
  - Dynamically updated export options modal tenant select options with duration category emojis (`🟢`, `🟡`, `🔴`).
  - Added unit test coverage in `tests/frontend/components/house_profile.test.js` covering emerald, amber, rose, and slate tenure rendering.
- **Harmonize Move, Copy, and Delete Action Colors (Quick Refinement QCK-13):**
  - Standardized semantic color themes across document multi-select buttons, modals, and 3-dot dropdown menu items (Move: Amber, Copy: Indigo, Delete: Rose, Rename: Blue, Timeline: Emerald).
- **Replace Folder "Select All" Text Button with Select Checkbox (Quick Refinement QCK-12):**
  - Replaced `.btn-select-all-folder` text button on category cards with `.folder-select-checkbox` positioned directly before `.folder-icon-box`, matching the document select checkbox styling.
  - Clicking this checkbox un-hides collapsed documents (`docsContainer.classList.remove('hidden')`) and selects all documents in the folder, or deselects all if already selected.
  - Added reactive synchronization: individual document checkbox changes update parent folder checkbox (checked / indeterminate / unchecked), and global select/deselect synchronizes all folder checkboxes across the view.
  - Added 8 unit tests in `tests/frontend/components/folder_select_checkbox.test.js` and expanded `batch_operations.test.js` (16 tests).
- **Category-Specific Folder Icons (01-13) & Empty Folder for Custom Categories (Quick Refinement QCK-11):**
  - Implemented distinct, descriptive Heroicons outline icons for each standard category 01 through 13 in Folders view (`FOLDER_ICONS`, `.folder-icon-box`, `getFolderIconSvg`), while retaining the clean empty folder icon for custom folders (14+).
  - Added 6 unit tests in `tests/frontend/components/categories_folder_icons.test.js` validating prefix matching, Arabic name resolution, fallback, and DOM rendering.
- **Category Folder Circular Document Count Badge & Refined Document Date Sizing (Quick Refinement QCK-10):**
  - Replaced folder header card document count text badge with a sleek circular count badge (`.doc-count-badge min-w-[20px] h-5 rounded-full`) showing just the count number inside a circle with tooltip.
  - Refined document date badge on document rows in Categories view to `text-[9px] font-mono tracking-tight`, freeing ~12-15px horizontal width per row to prevent document name truncation while keeping date clean and legible.
- **Document 3-Dots Dropdown Action Menu & Folders Date Badge (Quick Refinement QCK-09):**
  - Replaced the large Document Action Modal (`#doc-action-modal`) when clicking the 3-dots button (`.doc-menu-btn`) with a compact, floating context menu anchored to the button with bounds checking and Escape/outside-click dismissal.
  - Provided 5 direct action buttons: Rename Document (triggers inline rename), Move Document (`openBatchMoveForDoc`), Copy Document (`openBatchCopyForDoc`), Show in Timeline, and Delete Document (`handleDeleteSingleDoc`).
  - Added Show in Timeline navigation that switches active tab to Timeline, clears conflicting tenant filters, smoothly scrolls target card to center viewport, pulses blue highlight (`ring-4 ring-blue-500 bg-blue-50`), and selects the document.
  - Added an always-visible document date badge with light gray background (`doc-date-badge bg-slate-100 text-slate-500 text-[10px] font-mono`) in the Folders / Categories section immediately preceding the 3-dots button.
  - Comprehensive unit test suite (`tests/frontend/components/doc_dropdown_and_date.test.js`) with 14 automated tests covering dropdown lifecycle, actions, date badge rendering, and timeline navigation.
- **Batch Tenant Selection & Remove Copy Note (Quick Refinement QCK-08):**
  - Removed confusing amber explanatory note from `#batch-copy-modal` without replacement.
  - Added Target Tenant selector (`المستأجر • Target Tenant`) to both Move Selected (`#batch-move-tenant-select`) and Copy Selected (`#batch-copy-tenant-select`) modals, defaulting to `🏛️ المستأجر الحالي للوثيقة • Same Tenant`.
  - Cleaned modal action button labels to `Move Documents` and `Copy Documents`.
  - Added dynamic tenant dropdown population (`populateBatchTenantSelect`) with active lease indicators (`🟢 ` vs `👤 `) and lease years, with graceful fallback to distinct tenants in `currentCategories`.
  - Added full dual-stack backend support for `target_tenant_id: Optional[int]` in both FastAPI and ASP.NET Core 8.0, allowing cross-tenant or same-tenant batch moves and copies.
- **Intuitive Visual-First Export Modal & Clean Batch Bar (Quick Refinement QCK-07):**
  - Streamlined `#export-archive-modal` by removing verbose, explanatory English and Arabic paragraphs to create a clean, intuitive, visual-first dialog.
  - Minimalist header title (`تصدير الأرشيف • Export Archive`) without explanatory subtitle.
  - Intuitive format cards: Card A (`📦 ZIP` with `مجلدات • Folders`), Card B (`📄 PDF` with `تسلسل زمني • Timeline`), eliminating multi-sentence paragraph descriptions.
  - Streamlined Tenancy Scope (`المستأجر • Tenant`) with clear default option `🏛️ كامل السجل • All Records` across HTML and JavaScript.
  - Simplified modal footer buttons: `Cancel` and `⬇️ Download`.
  - Polished floating bottom batch bar (`#batch-action-bar`): removed distracting emojis (`📁`, `📋`, `🗑️`) from Move, Copy, and Delete buttons while preserving the `✕` glyph on the Deselect button (`<span>✕</span><span>Deselect</span>`).
- **Export Button Relocation & Archive Summary Box Removal (Quick Refinement QCK-06):**
  - Removed confusing and redundant digital archive summary box (`بيانات الأرشيف الرقمي للمنزل`) from the bottom of the House Profile, eliminating bottom visual clutter and keeping focus squarely on the Tenancy Register.
  - Relocated the Export House Archive button (`#btn-export-house-archive`) to the Document Panel header right beside `#btn-manage-tenants` for 0-scroll permanent visibility across all views (Profile, Folders, and Timeline).
  - Maintained full backward compatibility for `#btn-export-house-zip` and synchronized static assets across Python and ASP.NET Core with 0 diff.
- **Double-Click Inline Document Renaming (Quick Refinement QCK-05):**
  - Instant inline document title renaming triggered by double-clicking the title text in both Categories view folder lists (`span.doc-title-text`) and Timeline view (`h4.doc-title-text`).
  - Prominent, comfortable input field (`text-sm font-medium`, `px-3 py-1.5`, ~34px height, `border-2 border-blue-500 rounded-lg shadow-sm`) with `dir="auto"` for bidirectional Arabic/English alignment.
  - Full-width row expansion (`flex-1 min-w-0` on container spans and headings) preventing input collapse on short filenames, with automatic removal of `truncate` / `line-clamp-2` during active editing.
  - Full keyboard shortcuts (`Enter` to commit, `Escape` to cancel and revert without network traffic, `blur` to commit or revert).
  - Event propagation isolation preventing card click opening or card drag conflicts.
  - Direct integration with `PATCH /api/areas/{area}/houses/{house}/documents/{vault_id}` with in-memory document state update, DOM refresh, and toast notifications.
- **One-Click House Archive Export & Chronological Dossier (Phase 105 + Quick Refinements QCK-01, QCK-03, QCK-04):**
  - Full House Archive ZIP Export pipeline (`GET /api/areas/{area}/houses/{house}/export-zip`) across both FastAPI and ASP.NET Core Minimal APIs, packaging vault documents into collision-free structured ZIPs with clean Arabic filenames.
  - Standard 2-digit folder numbering fix (`FOLDER_PREFIXES` normalization so every folder in the ZIP has its proper `01 - `, `05 - `, `06 - `, etc. prefix).
  - Interactive Export Options Modal (`#export-archive-modal`, QCK-01):
    - Format Card A: Categorized ZIP Archive.
    - Format Card B: Combined Chronological PDF Dossier (recent documents first).
    - Tenancy Scope Filter: All Tenants (Full House) vs Individual active/past tenant.
  - Combined Chronological PDF Dossier (`GET /api/areas/{area}/houses/{house}/export-pdf` via PyMuPDF in Python and PdfSharpCore in .NET).
  - Descending Chronological Sort (QCK-03): Most recent document on Page 1, older documents towards the back, undated at the end.
  - Minimalist 3-Column Running Footer (QCK-03):
    - Bottom-Left: Document primary filing date (`YYYY-MM-DD`), blank if undated.
    - Bottom-Center: Category name with number prefix preserved (e.g. `05 - عقود`, `06 - كهرباء وماء`).
    - Bottom-Right: Group & Master pagination `X/Y  (Z)` (e.g. `1/3  (14)`).
    - Typography & Margins: 7.5 pt muted slate gray (`#64748b`), 16 pt margin. Zero verbose labels (no "Date:", "Category:", "Page:").
  - Arabic Cursive Text Shaping & BiDi Visual Reordering (QCK-04):
    - Python FastAPI (`src/api/routes.py`): Utilizes `arabic-reshaper` + `python-bidi` (`get_display(arabic_reshaper.reshape(cat))`), eliminating disjointed "terminal Arabic" isolated characters, connecting cursive letters accurately, and computing shaped text widths for exact centered alignment.
    - ASP.NET Core 8.0 (`web-net/Common/ArabicReshaper.cs` & `web-net/Program.cs`): Engineered zero-dependency pure C# `ArabicReshaper.ReshapeAndReorder` mapping standard Arabic characters (`\u0600`–`\u06FF`) to Unicode Presentation Forms-B (`\uFE80`–`\uFEFC`), supporting dual-joining letters, right-joining letters, Lam-Alef ligatures (`لا`, `لأ`, `لإ`, `لآ`), reversing RTL Arabic runs while preserving LTR numeric tokens (`05 - `) and mirroring bracket punctuation.
- **Multi-Select Batch Document Operations (Phase 106 + Quick Refinement QCK-02):**
  - Multi-select checkbox UI on document cards, folder-level toggle, and global Select All / Deselect All.
  - Glassmorphism dark floating action dock (`#batch-action-bar`) with dynamic selection counter and action buttons (`[ Move Selected ]`, `[ Copy Selected ]`, `[ Delete Selected ]`, `[ Deselect ]`).
  - Batch Move (`POST .../batch-move`): Atomic relocation to target standard or custom folder.
  - Batch Delete (`POST .../batch-delete`): Cascade deletion with confirmation modal and vault file unlinking.
  - Batch Copy (`POST .../batch-copy`): Copies documents to an additional category folder for instant reference.
  - Timeline De-duplication Architecture (QCK-02):
    - `is_timeline_visible INTEGER DEFAULT 1` added to `documents` table with auto-migration across Python and C#.
    - Secondary copies are automatically stored with `is_timeline_visible = 0`.
    - Timeline queries filter out copies so the timeline strictly reflects 1 real-world event per row (0 duplicate clutter).
    - Single 3-dot Copy (`POST .../documents/{vault_id}/copy`) also unified with `is_timeline_visible = 0`.
    - Physical vault storage: Vault stores 1 physical file without wasteful disk file duplication.
- **Portfolio Expansion (Phase 107):**
  - "+ Add House" UI trigger and modal (`#add-house-modal`) in the Area Grid overview.
  - Backend endpoint `POST /api/areas/{area}/houses` across FastAPI & ASP.NET Core with conflict detection (409 on duplicates).
  - Automatic physical directory scaffolding (`batches/` and `vault/`).
  - Dynamic grid refresh without page reload.
- **Global Keyboard Shortcuts Helper Modal (Phase 108):**
  - Pressing `?` or Shift+/ opens `#keyboard-shortcuts-modal` displaying `⌘K`, `⌘I`, `Space`, `Esc`, `?`.
  - Subtle navbar trigger button (`#btn-shortcuts-trigger`).
  - Input/textarea suppression guards and backdrop/Esc dismissal.
- **Multi-Stack Test Coverage & Verification:**
  - 84 ASP.NET Core xUnit tests (`web-net/FileOrganizer.Tests/`, including 32 in `ArabicReshaperTests.cs`).
  - 32 Python backend tests (17 in `tests/test_v14_features.py`, 13 in `tests/test_document_management_api.py`, 2 in `tests/test_house_profile_api.py`).
  - 145 Frontend Vitest tests across 13 test files (`npm run test:frontend`).
  - 49 Playwright Browser E2E tests.
  - Zero static asset diff between `src/api/static/` and `web-net/wwwroot/`.

---

## v13.0 Decoupled Monorepo Architecture & Native ASP.NET Core Web Server (Shipped: 2026-09-09)

**Phases completed:** 4 phases (101-104), 4 plans, 163 tests passing (40 .NET, 62 pytest, 61 Vitest)

**Key accomplishments:**

- Decoupled monorepo architecture establishing `web-net/` (ASP.NET Core 8.0 Minimal API) and `src/` (Python AI pipeline), with zero Python runtime dependency for web serving or manual ingestion.
- High-performance C# data layer using Dapper and `Microsoft.Data.Sqlite` in WAL mode with connection pooling, transactional integrity, and sub-10ms queries.
- Complete Minimal API endpoint suite matching Python FastAPI routes with 100% JSON parity (`/api/tree`, `/api/houses`, `/api/timeline`, `/api/categories`, `/api/tenants`, `/api/search`, `/api/pdf/{vault_id}`).
- Zero-Python manual ingestion endpoint (`POST /api/ingest`) directly writing vault PDFs and SQLite records in .NET.
- Zero-frontend rewrite serving vanilla JS/HTML assets from `wwwroot/` with correct MIME types.
- Comprehensive API parity test suite (`ParityVerificationTests.cs`) verifying response schemas, model mapping, and static assets.
- Self-contained Windows single-file publish (`dist/win-x64/FileOrganizer.Web.exe`) with IIS In-Process `web.config` and production deployment guide (`DEPLOYMENT-WINDOWS.md`).

---

## v12.0 Unified Document Ingestion System (Shipped: 2026-09-09)

**Phases completed:** 4 phases (97-100), 4 plans, 105 tests passing (62 backend, 43 frontend)

**Key accomplishments:**

- Zero-AI manual ingest engine with PyMuPDF page counting and instant execution (`src/ingest/manual_ingest.py`).
- Relational page inheritance pattern in SQLite `pages` table, linking batch pages to newly created documents with `is_continuation` properly set.
- FastAPI `POST /api/ingest` (multi-mode: manual, assisted, auto_split) and `POST /api/ingest/preview-ai` with zero database or filesystem mutations on preview.
- Modern Ingest Station slide-over drawer with `⌘I` shortcut, fullscreen drag-and-drop dropzone, PDF preview, mode switcher, and live refresh.
- 100% passing test suite across backend (pytest) and frontend (Vitest).

---

## v11.0 Database Backend & Clean Storage Architecture (Shipped: 2026-09-09)

**Phases completed:** 5 phases (92-96), 5 plans, 67 tests passing

**Key accomplishments:**

- Designed and implemented the relational SQLite schema (`areas`, `houses`, `tenants`, `batches`, `pages`, `documents`) with WAL mode, foreign keys, cascading deletes, unique constraints, and performance indices in `src/db/`.
- Built an idempotent migration engine (`src/migration/v11_migration.py`) restructuring legacy houses into clean `{house}/batches/` and `{house}/vault/` structures, eliminating `.lnk` shortcuts, legacy JSONs, and directory clutter.
- Redesigned multi-page scanned PDF ingestion (`src/ingest/v11_ingest.py`) to register batches and slice standalone vault PDFs directly, completely eliminating index shifting and the reconciliation loop.
- Rebuilt the FastAPI backend (`/api/tree`, `/api/houses`, `/api/timeline`, `/api/categories`, `/api/search`) to execute indexed SQL queries directly in <10ms, eliminating SMB filesystem walks and memory caching overhead.
- Established comprehensive Playwright E2E UI test suite (`tests/frontend/test_v11_e2e_db.py`) verifying 100% feature parity for Tree View, Area Grid Overview, Tenure Color-Coding (<5y, 5–10y, >10y), Drill-Down, Search, and PDF previews.
- Verified live migration integrity against real house data (House 500: 3 historical tenants, 65 vault docs, 131 pages accurately mapped with 0 unlinked pages).

---

## v10.0 Area Grid Overview & Tenure Visualization (Shipped: 2026-09-06)

**Phases completed:** 4 phases (88-91)

**Key accomplishments:**

- Built dual-view toggle supporting both classic Tree View and new Area Grid Overview.
- Designed responsive house card grid featuring current resident, tenure duration, and tenure color coding (<5y green, 5-10y yellow, >10y red).
- Implemented card metrics with total document counts and category breakdowns.
- Added smooth drill-down navigation from house cards into categories and timeline views with breadcrumb return.
- Resolved SMB mount filesystem hangs with intelligent in-memory TTL caching and fast regex scanning.
- Maintained 100% test pass rate with full Playwright E2E and backend integration suites.

---

## v9.0 Hierarchical Web Dashboard (Shipped: 2026-09-06)

**Phases completed:** 5 phases, 5 plans

**Key accomplishments:**

- Implemented 3-level hierarchical sidebar navigation (Area -> House -> Tenant) with deep URL linking and synchronized active node selection.
- Developed global search across houses, tenants, and full-text PDF documents with instant zero-click search dropdown and keyboard shortcuts (`Cmd/Ctrl+K`, `Esc`).
- Added Arabic-English phonetic intermixing and fuzzy matching for Arabic OCR names.
- Enhanced document viewer with PDF hover preview tooltips and tabbed Category / Timeline views.
- Created static IIS export pipeline (`tree.json`, `search_index.json`) for zero-Python runtime environments.
- Built comprehensive interaction test suite in `tests/frontend/`.

---

## v8.0 Web-Based File Viewer (Shipped: 2026-09-02)

**Phases completed:** 4 phases, 3 plans, 0 tasks

**Key accomplishments:**

- (none recorded)

---

## v5.2: Deep Architecture Integrity & Verification

**Shipped:** 2026-08-01

**Key Accomplishments:**

- Created robust `src/core/verification.py` module to deep-scan houses for file system integrity.
- Handled legacy artifacts, orphan vault files, missing shortcuts, and state vs. physical folder drift securely.
- Resolved tricky cross-platform edge cases involving Pytest mocked environments, `pylnk3`, and Windows long paths.
- Reached 100% passing test coverage (288 tests) across the entire system.

## v5.1: Polishing & Migration Cleanup

**Shipped:** 2026-08-01

**Key Accomplishments:**

- Unified `1_cleaned.json`, `2_grouped.json`, and `3_routed_and_finalized.json` into a single `state.json` file.
- Fixed the Timeline View document index numbering logic to properly jump indices relative to document page count.
- Expanded automated test coverage by refactoring tests away from legacy formats and creating `tests/test_live_e2e.py` targeting actual test sets.
- Fixed `pylnk3` Windows dependency resolution.
