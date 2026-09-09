---
slug: 260909-house-tenancy-register-and-archive-profile
date: 2026-09-09
description: "House Tenancy Register and Digital Archive Profile view in Arabic when selecting a house without a tenant"
status: complete
---

# Quick Task: House Tenancy Register & Digital Archive Profile (Arabic First)

## Objectives
1. **Backend Profile Endpoint (`src/api/models.py`, `src/api/routes.py`)**:
   - Create Pydantic models: `HouseTenantProfile`, `CategoryBreakdownItem`, `HouseArchiveProfile`, `HouseProfileResponse`.
   - Add endpoint `GET /api/areas/{area_id}/houses/{house_id}/profile`:
     - Returns tenancy succession (active tenant vs past tenants, lease dates, duration string in Arabic, document counts, folder counts).
     - Returns digital archive profile (total docs, scanned pages, batch counts, date timespan in Arabic, top category breakdown).
     - Compatible with both SQLite Database repository and legacy JSON state.

2. **Frontend Tenancy Register & Navigation (`src/api/static/index.html`, `src/api/static/js/app.js`)**:
   - When a house is selected without a tenant (`currentTenant` is null):
     - Tab 1 becomes: **سجل المستأجرين** (Tenancy Register).
     - Tab 2 becomes: **الخط الزمني الكامل** (Full House Timeline).
     - Tab 1 renders the Arabic House Profile:
       - **Tenancy Succession Cards**:
         - Active Tenant (`🟢 المستأجر الحالي`) with start date, stay duration in Arabic, document count, and folder count.
         - Past Tenants (`⚪ مستأجر سابق`) with start/end dates, stay duration, and document count.
         - Quick action button/card click: **استعراض ملف المستأجر ←** (`Open Tenant File`) that immediately selects the tenant.
       - **Archive Profile Section (بيانات الأرشيف الرقمي)**:
         - Document timespan: `النطاق الزمني: من [أقدم تاريخ] إلى [أحدث تاريخ] ([N] سنوات)`.
         - Document & scanned page volume: `[X] وثيقة عبر [Y] صفحة ممسوحة ([Z] دفعة)`.
         - Main categories distribution pills.
   - When a tenant is selected:
     - Tab 1 switches to: **المجلدات والتصنيفات** (Folders & Categories).
     - Tab 2 switches to: **الخط الزمني للمستأجر** (Tenant Timeline).
     - Header displays: `500 - [Tenant Name]`.
     - Include a return link/button: `← سجل المنزل` (Back to House Register) to easily return to the house-level register.

3. **Verification**:
   - Backend unit/API tests for `/profile` endpoint (`tests/test_house_profile_api.py`).
   - Frontend Playwright E2E tests for the Arabic House Register (`tests/frontend/test_house_register.py`):
     - Verify initial house selection displays the Arabic Tenancy Register tab and cards.
     - Verify Current Tenant vs Past Tenant labels and date badges.
     - Verify Archive profile data (timespan, pages, categories).
     - Verify clicking on a tenant card drills down into that tenant's folders with proper header title.
     - Verify returning back to the house register.
   - Run full frontend and backend test suites.
   - Git commit and push to origin main.
