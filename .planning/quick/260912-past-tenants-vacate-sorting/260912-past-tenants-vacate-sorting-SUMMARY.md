---
status: complete
date: 2026-09-12
task_id: 260912-past-tenants-vacate-sorting
---

# Quick Task 260912-past-tenants-vacate-sorting: Past Tenants Chronological Sorting by Vacate Date

## Overview
When all tenants of a house have vacated (e.g. House 538), the backend previously sorted past tenants strictly by `start_date DESC`. This caused older residents who vacated more recently (e.g. `يحيى محمد علي` who lived in House 538 from 2000 to 2024) to be listed at the bottom of the past tenants list, while residents with later move-in dates but earlier vacate dates (e.g. `حمد إبراهيم` who lived from 2013 to 2023) were falsely prioritized as the "latest" tenant.

## Changes Made
- **.NET Backend (`web-net/Data/FileOrganizerRepository.cs`)**:
  - `GetTreeAsync` (line 44): Changed SQL ordering clause to:
    ```sql
    ORDER BY (CASE WHEN end_date IS NULL OR end_date = '' OR LOWER(end_date) = 'present' OR end_date >= DATE('now') THEN 1 ELSE 0 END) DESC, 
             end_date DESC, start_date DESC, id DESC;
    ```
  - `GetHousesAsync` (line 240): Updated SQL ordering clause to order past tenants by `end_date DESC, start_date DESC`.
  - `GetHouseTenantsAsync` (line 630): Updated SQL query to order past tenants by `end_date DESC, start_date DESC`.
  - `GetHouseProfileAsync` (line 446): Updated in-memory sort comparator for `tenantProfiles` to sort by `b.EndDate.CompareTo(a.EndDate)` before `b.StartDate.CompareTo(a.StartDate)`.
- **Python Backend (`src/api/routes.py`)**:
  - `get_tree_api` (line 1645): Changed SQLite query to order by `(CASE WHEN end_date IS NULL ... OR end_date >= DATE('now') THEN 1 ELSE 0 END) DESC, end_date DESC, start_date DESC, id DESC`.
  - `get_house_profile` (lines 524 & 613): Updated sorting comparator `_tp_sort_key` to sort by `(not x.is_active, -end_yr, -start_yr)`.

## Verification
- **.NET xUnit**: Updated `GetHousesAsync_And_GetTreeAsync_VacantHouse_ReturnsGreyAndNoActiveTenant` in `web-net/FileOrganizer.Tests/RepositoryTests.cs` to test multiple past tenants (`مطلق` 2011-2021, `حمد` 2013-2023, `يحيى` 2000-2024). Asserts that `يحيى` (vacated 2024) is returned first (#1), and the house subtitle accurately reflects `2000 - 2024`. All 148 xUnit tests pass.
- **Python Pytest**: Updated `test_get_tree_vacant_house_no_active_tenant` in `tests/test_api_v11.py` to assert that `يحيى` (vacated 2024) is sorted first. All 44 Pytest tests pass.
