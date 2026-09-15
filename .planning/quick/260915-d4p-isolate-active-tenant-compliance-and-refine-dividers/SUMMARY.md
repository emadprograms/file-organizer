---
status: complete
quick_id: 260915-d4p
slug: isolate-active-tenant-compliance-and-refine-dividers
date: 2026-09-15
description: Isolate Active Tenant Compliance Document Counts (House 500 Fix) & Refine Card/Profile Dividers
commit: HEAD
---

# Quick Task Summary: Isolate Active Tenant Compliance Document Counts (House 500 Fix) & Refine Card/Profile Dividers

**Task ID**: 260915-d4p  
**Status**: Complete  
**Date**: 2026-09-15  

## Overview
Addressed two user feedback items regarding compliance layout and resolved a critical data integrity bug:
1. **House 500 Active Tenant Document Isolation**:
   - In House 500, active resident Fawaz (فواز خليل الطارش) has 1 contract, but the compliance check reported 3 contracts because past tenant Abdullah (عبد الله حميدة رضا فرج) had 2 contracts.
   - Root cause: frontend checked profile.archive.categories and house.category_counts, which aggregate documents across the entire house's historical archive.
   - Fix: Added CategoryCounts to HouseTenantProfileDto and ActiveTenantCategoryCounts to TreeHouseDto / HouseCardDto. Refactored computeTenantCompliance in house-profile.js to strictly check ctiveTenant.category_counts and ctiveTenant.categories, completely cutting off archive leakage.
2. **House Card (rea-grid.js)**:
   - Reverted placing warning pill in the card footer (which was squeezed awkwardly between stay duration / doc count metrics).
   - Restored clean card footer.
   - Placed the missing documents warning strip inside the card's tenant section, cleanly separated with a dedicated divider (.card-warning-divider).
3. **Tenant Selection UI (house-profile.js)**:
   - Kept the 5 mandatory document categories open by default.
   - Substantially reduced vertical height with compact item cards (p-1.5 px-2), tighter grid gaps (gap-1.5), and removed verbose subtitle paragraphs.
   - Added a clean visual divider (.tenant-section-divider) between the compliance card and the tenants list (المستأجرون).

---

## Accomplishments

### 1. Backend Granularity (DTOs.cs, FileOrganizerRepository.cs)
- Added [JsonPropertyName(category_counts)] public Dictionary<string, int> CategoryCounts to HouseTenantProfileDto.
- Added [JsonPropertyName(active_tenant_category_counts)] public Dictionary<string, int>? ActiveTenantCategoryCounts to TreeHouseDto and HouseCardDto.
- Updated GetHouseProfileAsync to compute 	enantCatCounts[d.TenantId][cleanCat] and assign directly to each tenant profile.
- Updated GetTreeAsync and GetHousesAsync to compute ActiveTenantCategoryCounts for the active residing tenant.

### 2. Frontend Compliance Refactoring (house-profile.js, rea-grid.js)
- house-profile.js: In computeTenantCompliance, removed all references to profile.archive.categories. Each category's existence and document count are derived strictly from ctiveTenant.category_counts or ctiveTenant.categories.
- rea-grid.js: In computeHouseIntegrity, prioritized house.active_tenant_category_counts.
- Restored clean card footer in enderHouseCard and placed .missing-docs-strip under tenants with .card-warning-divider.
- Rendered .tenant-section-divider in House Profile separating the compact compliance box from .residents-section.

### 3. Static Asset Parity
- Updated and synchronized dist/win-x64/wwwroot/js/area-grid.js and dist/win-x64/wwwroot/js/house-profile.js.

---

## Verification
- **Live API Test on Production Database**: Queried /api/areas/Safra/houses/500 confirming active resident Fawaz returns عقود: 1, past tenant Abdullah returns عقود: 2, and archive returns عقود: 3.
- **Vitest Frontend Tests**: All 36 test files passed, 435/435 tests passed (including updated House 500 scenario, divider, and open-by-default tests in 	enant_file_integrity.test.js).
- **.NET Backend Tests**: All 926 tests passed (0 failures) including new GetHouseProfileAsync_PopulatesTenantLevelCategoryCounts_IsolatedPerTenant in RepositoryTests.cs.
- **Live Background Server**: Successfully restarted on Windows (un-windows.ps1) listening on port 5000.
