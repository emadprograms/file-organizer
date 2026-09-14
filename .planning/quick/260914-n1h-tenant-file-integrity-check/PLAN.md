# Quick Task 260914-n1h: Tenant File Integrity Check (Idea B + Idea C)

## Overview
Implement a comprehensive tenant file integrity and compliance check system for residing tenants across the application, combining:
- **Idea B (Area Grid Overview):** Quick filter pills (`All Houses`, `Incomplete`, `Complete`, `Vacant`), compliance sort options (`Missing First`, `Complete First`), and visual integrity badges on house cards (`5/5 Complete` vs `⚠️ X/5 Missing`).
- **Idea C (House Profile View):** Interactive "Tenant File Compliance Checklist" (فحص اكتمال ملف الساكن) at the top of the house profile for the current active resident tenant, highlighting each of the 5 mandatory categories:
  1. `02 - بيانات شخصية` (Personal Details)
  2. `03 - أمر تخصيص` (Allotment Order)
  3. `04 - محضر تسليم مفتاح` (Key Handover)
  4. `05 - عقود` (Contracts)
  5. `07 - استقطاع إيجار` (Rent Deduction)
  With 1-click Ingest Station trigger pre-filling Area, House, Active Tenant, and the exact missing category.

---

## Tasks

### Task 1: Backend DTO & Repository Support for Tenant Categories
- **Files:**
  - `src/HousingApplication.Web/Models/DTOs.cs`
  - `src/HousingApplication.Web/Data/FileOrganizerRepository.cs`
- **Action:**
  - Add `Categories` property (`List<string>`) to `HouseTenantProfileDto`.
  - In `GetHouseProfileAsync`, populate `Categories` from `tenantCatSets[t.Id]` so the client receives the exact categories associated with each tenant.
- **Verify:** `~/.dotnet/dotnet test` compiles and passes.

### Task 2: Idea B - Area Grid Integrity Filter, Sorting, and Card Badges
- **Files:**
  - `src/HousingApplication.Web/wwwroot/js/area-grid.js`
  - `src/HousingApplication.Web/wwwroot/index.html`
  - `src/HousingApplication.Web/wwwroot/css/styles.css`
- **Action:**
  - Define `MANDATORY_INTEGRITY_CATEGORIES` (IDs `02`, `03`, `04`, `05`, `07`).
  - Implement `computeHouseIntegrity(house)` checking `category_counts` for the 5 mandatory categories (handling both clean and prefixed category names).
  - Add quick filter pills toolbar in Area Grid (`All Houses`, `⚠️ Incomplete`, `✓ Complete`, `Vacant`) with live counts.
  - Add `compareHouseIntegrityWorst` and `compareHouseIntegrityBest` in `area-grid.js`, and add options to `#grid-house-sort-select`.
  - Render an integrity badge on each house card header (emerald `5/5` for complete, amber/rose `⚠️ X/5` with missing details for incomplete, neutral for vacant).
  - Add styling in `styles.css` for dark mode and responsive layout.

### Task 3: Idea C - House Profile Compliance Checklist & 1-Click Ingestion
- **Files:**
  - `src/HousingApplication.Web/wwwroot/js/house-profile.js`
  - `src/HousingApplication.Web/wwwroot/js/ingest-station.js`
  - `src/HousingApplication.Web/wwwroot/css/styles.css`
- **Action:**
  - In `house-profile.js`, implement `computeTenantCompliance(profile, tenant)` for the active residing tenant.
  - Render the interactive "Tenant File Compliance Checklist" card at the top of the house profile view.
  - Present badges for all 5 mandatory categories:
    - Present: emerald pill with `✓`, count, and click-to-navigate.
    - Missing: amber/rose pill with `⚠️`, "مفقود", and "+ رفع المستند" button.
    - Vacant state: clear message if house has no resident tenant.
  - In `ingest-station.js`, enhance `openIngestStation` (or add `openIngestStationWithPreset(preset)`) to pre-fill Area, House, Tenant, and Category when triggered from the checklist.

### Task 4: Parity, Verification & Testing
- **Files:**
  - Mirror all changes to `dist/win-x64/wwwroot/` with 100% byte parity.
  - `tests/web/components/tenant_file_integrity.test.js`
- **Action:**
  - Create full Vitest test suite covering:
    - Integrity computation for occupied/vacant houses.
    - Area grid filter pills and compliance sorting.
    - House card integrity badge rendering.
    - House profile compliance checklist rendering and upload trigger.
    - Ingest modal preset pre-filling.
  - Run `npm test` and `~/.dotnet/dotnet test` to ensure 100% passing tests.
