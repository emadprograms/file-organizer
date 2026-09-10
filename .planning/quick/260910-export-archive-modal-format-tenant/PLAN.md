# Quick Task Plan: Export Archive Options Modal (PDF Dossier vs Categorized ZIP & Tenant Scope)

## Objective
Replace direct export with an intuitive, unified modal asking the user two options in a single screen:
1. Export Format: Categorized ZIP Archive vs Combined Chronological PDF Dossier.
2. Tenant Scope: All Tenants (Full House Archive) vs Specific Tenant (Individual Tenancy File).

## Requirements
- UI Modal: `#export-archive-modal` with bilingual English/Arabic labels, format cards (ZIP vs PDF), tenant selector dropdown, and download trigger with progress spinner.
- Backend FastAPI:
  - `GET /api/areas/{area_id}/houses/{house_id}/export-zip`: Add optional `tenant_id` query param.
  - `GET /api/areas/{area_id}/houses/{house_id}/export-pdf`: Add endpoint merging documents chronologically into a single PDF with PyMuPDF, with optional `tenant_id` query param.
- Backend ASP.NET Core:
  - `GET /api/areas/{areaId}/houses/{houseId}/export-zip`: Support optional `tenantId` query param.
  - `GET /api/areas/{areaId}/houses/{houseId}/export-pdf`: Implement chronological PDF merger using `PdfSharpCore`, with optional `tenantId` query param.
- Frontend:
  - Update `src/api/static/js/house-profile.js` and `index.html`.
  - Wire up modal open on `[ 📦 تحميل أرشيف المنزل ]` click.
  - Populate tenant options from `profile.tenants`.
- Sync:
  - `dotnet build` to sync `src/api/static/` to `web-net/wwwroot/`.
- Tests:
  - Backend Pytest in `tests/test_v14_features.py`.
  - Backend xUnit in `web-net/FileOrganizer.Tests/ApiEndpointTests.cs`.
  - Frontend Vitest in `tests/frontend/components/export_archive_modal.test.js`.
