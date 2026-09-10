# Quick Task Summary: House Archive Export Options Modal (PDF Dossier vs Categorized ZIP & Tenancy Scope)

## Overview
Replaced the direct house archive export with a unified, modern, bilingual modal dialog (`#export-archive-modal`) that allows the user to configure export options in a single screen before downloading:
1. **Export Format**:
   - **Categorized ZIP Archive** (`أرشيف ZIP مصنف في مجلدات`): Full house vault documents categorized in standard numbered folders (`05 - عقود`, `03 - أمر تخصيص`, etc.).
   - **Combined Chronological PDF Dossier** (`ملف PDF مدمج مرتب زمنياً`): All documents merged into a single multi-page chronological timeline PDF from oldest to newest.
2. **Tenancy Scope**:
   - **All Tenants / Full House Record** (`🏛️ جميع المستأجرين / كامل سجل المنزل`): Comprehensive archive for the entire house history.
   - **Specific Tenant** (`👤 / 🟢 Individual Tenant`): Restricts export to documents filed under the selected tenant.
3. **Folder Numbering Normalization** (Urgent User Requirement):
   - Fixed unnumbered category folder names in ZIP archives (e.g., raw "عقود" or "أمر تخصيص") by normalizing all folders to standard two-digit numbered prefixes (e.g., `05 - عقود/`, `03 - أمر تخصيص/`, `06 - كهرباء وماء/`).

---

## Changes Implemented

### 1. Frontend UI Modal (`src/api/static/index.html`)
- Added `#export-archive-modal` with Tailwind CSS classes consistent with macOS system style:
  - Header with icon and bilingual title: `تصدير أرشيف المنزل • Export House Archive`.
  - Question 1 (صيغة التصدير / Export Format) with two selectable modern cards:
    - Card A: `📦 أرشيف ZIP مصنف في مجلدات (Categorized ZIP Archive)` (active by default).
    - Card B: `📄 ملف PDF مدمج مرتب زمنياً (Combined Chronological PDF)`.
  - Question 2 (نطاق المستأجر / Tenancy Scope):
    - Modern styled select dropdown `#export-archive-tenant-select`.
    - Option 1 (Default): `🏛️ جميع المستأجرين / كامل سجل المنزل (All Tenants / Full Record)`.
    - Options 2..N: Populated from `profile.tenants`.
  - Modal Footer with action buttons:
    - `[ ⬇️ بدء التحميل / Download Archive ]` (`#btn-confirm-export-archive`) with `#export-archive-spinner`.
    - `[ إلغاء / Cancel ]` (`#btn-cancel-export-archive`).

### 2. Frontend Controller (`src/api/static/js/house-profile.js`)
- Updated `btn-export-house-zip` click handler to call `openExportArchiveModal(profile)`.
- Implemented:
  - `openExportArchiveModal(profile)`: Populates tenant dropdown from `profile.tenants`, resets format to ZIP, mounts event listeners, and reveals modal.
  - `closeExportArchiveModal()`: Dismisses modal, resets spinner and button state.
  - `setExportFormat(format)`: Toggles active visual styling between ZIP and PDF option cards.
  - `confirmExportArchive()`: Resolves selected format and tenant scope, formats download URL (`/export-zip` or `/export-pdf` + optional `?tenant_id=X`), triggers download via hidden `<a>`, fires bilingual toast notification (`showToast`), and closes modal.
  - Added backdrop click and Escape key dismissal listeners.

### 3. Backend FastAPI (`src/api/routes.py`)
- Updated `GET /api/areas/{area_id}/houses/{house_id}/export-zip`:
  - Accepts optional `tenant_id: Optional[int] = None`.
  - Filters documents by `tenant_id` when supplied.
  - Normalizes every category folder using `FOLDER_PREFIXES` via `_format_category_with_prefix(doc.category)`.
  - Content-Disposition uses ASCII fallback for `filename="..."` and RFC 5987 / RFC 6266 `filename*=UTF-8''...` for Unicode/Arabic names to prevent `UnicodeEncodeError: 'latin-1'`.
- Implemented `GET /api/areas/{area_id}/houses/{house_id}/export-pdf`:
  - Accepts optional `tenant_id: Optional[int] = None`.
  - Sorts documents chronologically by `primary_date` ASC (non-empty dates ascending, null/empty dates at the end, ties broken by `vault_id`).
  - Merges physical PDF files into a single in-memory document via PyMuPDF (`fitz.open()`).
  - Returns fallback 1-page document if archive has no files.
  - Streams response with `media_type="application/pdf"` and RFC 6266 headers.

### 4. Backend ASP.NET Core 8.0 (`web-net/Program.cs`)
- Updated `GET /api/areas/{areaId}/houses/{houseId}/export-zip`:
  - Accepts optional `int? tenantId = null` from query string.
  - Filters `allDocs` by `tenantId` if provided.
  - Ensures folder names are formatted with standard prefixes using `Constants.FormatCategoryWithPrefix(doc.Category)`.
  - Supports `AREAS_ROOT_PATH` and `AreasRoot` configuration and environment variables.
- Implemented `GET /api/areas/{areaId}/houses/{houseId}/export-pdf`:
  - Accepts optional `int? tenantId = null` from query string.
  - Sorts documents chronologically by `Date` ASC.
  - Merges physical PDF files into a single `PdfSharpCore.Pdf.PdfDocument`.
  - Falls back to 1-page document if empty.
  - Returns `Results.File(..., "application/pdf", filename)`.

### 5. Monorepo Synchronization
- Executed `~/.dotnet/dotnet build web-net/FileOrganizer.Web.csproj` to copy static assets to `web-net/wwwroot/`.
- Verified 0 diff with `diff -r src/api/static/ web-net/wwwroot/`.

---

## Verification & Test Results

1. **Python Pytest (`tests/test_v14_features.py`)**:
   - `test_export_house_archive_zip` (PASSED)
   - `test_export_house_archive_zip_empty_house` (PASSED)
   - `test_export_house_archive_zip_with_tenant_filter` (PASSED)
   - `test_export_house_archive_zip_folder_numbering_normalization` (PASSED)
   - `test_export_house_archive_pdf` (PASSED)
   - `test_export_house_archive_pdf_with_tenant_filter` (PASSED)
   - `test_export_house_archive_pdf_empty_house` (PASSED)
   - **Total: 11 passed in 0.80s (100% pass rate)**.

2. **ASP.NET Core xUnit (`web-net/FileOrganizer.Tests/ApiEndpointTests.cs`)**:
   - `ExportZip_ReturnsZipArchive` (PASSED)
   - `ExportZip_WithTenantFilter_ReturnsFilteredZip` (PASSED)
   - `ExportPdf_ReturnsChronologicalMergedPdf` (PASSED)
   - `ExportPdf_WithTenantFilter_ReturnsFilteredPdf` (PASSED)
   - **Total: 50 passed in 0.29s (100% pass rate)**.

3. **Frontend Vitest (`tests/frontend/components/export_archive_modal.test.js`)**:
   - `renders house profile and opens modal on clicking export button` (PASSED)
   - `switches export format between ZIP and PDF` (PASSED)
   - `allows tenant dropdown selection` (PASSED)
   - `triggers download and toast with selected format and tenant` (PASSED)
   - `closes modal on close button, cancel button, backdrop click, and Escape key` (PASSED)
   - **Total Suite: 98 passed across 9 test files in 1.47s (100% pass rate)**.
