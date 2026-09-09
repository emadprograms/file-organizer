# Quick Task Summary: House Tenancy Register & Digital Archive Profile (Arabic First)

**Slug:** `260909-house-tenancy-register-and-archive-profile`  
**Date:** 2026-09-09  
**Status:** Completed  

---

## What Was Done

1. **Backend Profile Endpoint (`GET /api/areas/{area_id}/houses/{house_id}/profile`)**:
   - Added models in `src/api/models.py`:
     - `HouseTenantProfile`: `id`, `name`, `start_date`, `end_date`, `is_active`, `duration_str_ar`, `document_count`, `category_count`.
     - `CategoryBreakdownItem`: `category`, `document_count`.
     - `HouseArchiveProfile`: `total_documents`, `total_pages`, `batch_count`, `oldest_date`, `newest_date`, `timespan_years`, `timespan_str_ar`, `categories`.
     - `HouseProfileResponse`: `house_id`, `area_id`, `tenants`, `archive`.
   - Implemented `GET /api/areas/{area_id}/houses/{house_id}/profile` in `src/api/routes.py`:
     - Arabic duration formatters (`_format_arabic_duration`, `_format_arabic_timespan`).
     - Support for SQLite Database repository with seamless fallback to legacy JSON state.

2. **Frontend Tenancy Register & 3-Level Drill-Down UI**:
   - In `src/api/static/index.html`:
     - Added `#tab-categories-label` and `#tab-timeline-label` spans.
   - In `src/api/static/js/app.js`:
     - When selecting a house without a tenant (`currentTenant` is null):
       - Tab 1 label updates dynamically to **سجل المستأجرين** (Tenancy Register).
       - Loads and renders `renderHouseProfile(profile)`:
         - Tenancy succession cards: Active tenant (`🟢 المستأجر الحالي`, `مستمر`) and past tenants (`⚪ مستأجر سابق`, dates, stay duration, document counts, and folder counts).
         - Quick action drill-down: clicking tenant card immediately navigates to that tenant's categorized folders.
         - Digital Archive Profile box: scanned pages, total documents, timespan in Arabic, and main category pills with document counts.
     - When selecting a tenant:
       - Tab 1 updates to **Folders**.
       - Header displays `[House] - [Tenant]` with a quick `← سجل المنزل` (Back to House Register) button to return to the house overview.
       - Category folders (`.category-folder-card`) render for that tenant.

3. **Comprehensive Testing & Verification**:
   - Backend unit tests (`tests/test_house_profile_api.py`):
     - Verified profile endpoint with DB repository (active vs past tenants, duration strings, timespans, category breakdown).
     - Verified legacy fallback support.
   - Frontend Playwright E2E tests (`tests/frontend/test_house_register.py`):
     - Verified house-level selection displays Arabic Tenancy Register by default.
     - Verified active vs past tenant cards and digital archive metadata.
     - Verified clicking tenant card navigates to folders view and back button returns to register.
   - Updated existing Playwright tests (`tests/frontend/test_tabs.py`, `tests/frontend/test_v11_e2e_db.py`) to align with the new 3-level hierarchy (House Register → Tenant Folders → Documents).
   - All 52 frontend Playwright tests and 59 backend pytest tests pass (100% green).
