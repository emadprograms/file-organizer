---
status: complete
quick_id: 260914-n1h
slug: tenant-file-integrity-check
date: 2026-09-14
description: Tenant File Integrity & Compliance Check System for Residing Tenants (Idea B + Idea C Hybrid)
commit: HEAD
---

# Quick Task Summary: Tenant File Integrity & Compliance Check System (Idea B + Idea C Hybrid)

**Task ID**: `260914-n1h`  
**Status**: Complete  
**Date**: 2026-09-14  

## Overview
Implemented a comprehensive tenant file integrity and compliance verification system for active residing tenants across the application, combining **Idea B** (Area Grid Overview with filter pills, compliance sorting, and house card badges/strips) and **Idea C** (House Profile View with interactive checklist card, green checkmarks, and 1-click Ingest Station trigger).

The system enforces presence of the 5 mandatory documents specified for every residing tenant:
1. `02 - بيانات شخصية` (Personal Details)
2. `03 - أمر تخصيص` (Allotment Order)
3. `04 - محضر تسليم مفتاح` (Key Handover)
4. `05 - عقود` (Contracts)
5. `07 - استقطاع إيجار` (Rent Deduction)

---

## Accomplishments

### 1. Backend DTO & Repository Support
- **`src/HousingApplication.Web/Models/DTOs.cs`**:
  - Added `public List<string> Categories { get; init; } = new();` to `HouseTenantProfileDto`.
- **`src/HousingApplication.Web/Data/FileOrganizerRepository.cs`**:
  - In `GetHouseProfileAsync`, populated `Categories` from `tenantCatSets[t.Id]` so the client receives the exact document category names associated with each tenant.

### 2. Idea B: Area Grid Integrity Filters, Sorting, and Card Badges
- **Toolbar & Filter Pills (`#grid-integrity-toolbar`)**:
  - Added filter pills toolbar above the area grid:
    - `All Houses (X)`
    - `⚠️ Incomplete (Y)`
    - `✓ Complete (Z)`
    - `Vacant (W)`
  - Displays dynamic summary badge (`X houses require documents` with pulse indicator vs `All occupied houses 100% compliant`).
  - Filter state filters house cards in-place while keeping `#add-house-grid-card` accessible at the end of the grid.
  - Implemented celebratory empty state when 0 houses are incomplete (`All Houses Compliant!` with a quick button to reset to `all`).
- **Compliance Sorting**:
  - Added `compareHouseIntegrityWorst` (missing documents first: 1/5 before 3/5 before complete 5/5, then vacant houses last) and `compareHouseIntegrityBest` (complete 5/5 first, then 4/5, 3/5, then vacant houses last).
  - Added `Compliance: Missing First` (`integrity_worst`) and `Compliance: Complete First` (`integrity_best`) to `#grid-house-sort-select` in the top header with `localStorage` persistence.
- **House Card Visual Indicators**:
  - Occupied houses with 5/5 mandatory documents display an emerald `✓ 5/5` badge.
  - Occupied houses missing documents display an amber `⚠️ X/5` badge along with a prominent `.missing-docs-strip` listing the exact missing categories (e.g. `⚠️ ناقص: عقود، استقطاع إيجار`).
  - Vacant houses display a clean neutral `شاغر` badge and no missing docs strip.

### 3. Idea C: House Profile Interactive Compliance Checklist & 1-Click Ingest
- **Compliance Checklist Card (`.tenant-compliance-card`)**:
  - Renders at the very top of the house profile view for the currently residing tenant.
  - Vacant houses display a subtle dashed banner: `المنزل شاغر حالياً — لا يوجد ساكن حالي لإجراء فحص الوثائق الإلزامية` with `شاغر` pill.
  - Occupied houses display:
    - Active resident tenant name with `🛡️` shield and score badge (`5/5 مكتمل ✓` or `X/5 ناقص ⚠️`).
    - 5 category cards for the mandatory documents:
      - **Present documents**: Emerald card with `✓`, document count `متوفر (N)`, and click-to-navigate action opening that tenant's category folder.
      - **Missing documents**: Amber card with `⚠️`, "مفقود", and an action-oriented `+ رفع` button (`.btn-compliance-upload`).
- **1-Click Ingestion Flow (`openIngestStationWithPreset`)**:
  - Enhanced `ingest-station.js` to accept presets: `{ area, house, tenant, category }`.
  - Clicking `+ رفع` on any missing category launches the Ingest Station modal pre-filled with the Area, House, Active Tenant, and auto-selects the missing Category dropdown.

### 4. Verification & Testing
- **New Automated Test Suite**:
  - Created `tests/web/components/tenant_file_integrity.test.js` with 25 unit tests covering:
    - Mandatory categories specification (IDs, keys, prefixes).
    - `computeHouseIntegrity` (occupied, complete, incomplete, vacant, applicants-only).
    - `compareHouseIntegrityWorst` and `compareHouseIntegrityBest` sorting.
    - Area grid filter pills, live counts, filtering, and celebratory empty states.
    - House card integrity badges and missing document strips.
    - `computeTenantCompliance` with backend DTOs and archive categories.
    - House profile compliance checklist UI, click-to-navigate, and `+ رفع` click triggering `openIngestStationWithPreset`.
    - Ingest station preset pre-filling.
- **Full Test Passes**:
  - `npm test`: **36 test files, 435 tests passing cleanly (100%)**.
  - `~/.dotnet/dotnet test`: **925 .NET xUnit tests passing cleanly (100%)**.
  - 100% byte parity confirmed between `src/HousingApplication.Web/wwwroot/` and `dist/win-x64/wwwroot/`.
