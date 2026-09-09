---
status: resolved
trigger: Assigned tenant shows the tenant multiple times in the Ingest Station dropdown and document modal.
---
# Debug Session: Duplicate Assigned Tenant Options

## Symptoms
- **Expected behavior**: In the Ingest Station (`ingest-station.js`) and Document Manager modal (`doc-manager.js`), selecting an area/house or opening the station should display each assigned tenant exactly once in the tenant selection dropdown.
- **Actual behavior**: When opening the Ingest Station or selecting a house, tenants were duplicated (appearing 2x or more). In addition, concurrent requests could interleave and append multiple copies of the same tenant options.
- **Error messages**: None (silent UI duplication bug).

## Root Causes
1. **Redundant Trigger in `openIngestStation` (`src/api/static/js/ingest-station.js`)**:
   `openIngestStation()` called `populateAreas(activeArea)` (which calls `populateHouses(activeArea)` which in turn calls `populateTenants(activeArea, activeHouse)`). Immediately after, it called `if (activeHouse) populateHouses(activeArea, activeHouse)` a second time, triggering two concurrent asynchronous `populateTenants` calls for the same house.
2. **Race Condition & Missing Deduplication in `populateTenants` (`src/api/static/js/ingest-station.js`)**:
   `populateTenants` cleared `tenantSelect.innerHTML` before calling `await fetch(...)`. When two concurrent calls were in flight, both cleared early, then both completed and sequentially appended their `<option>` elements, duplicating all tenants. Furthermore, there was no request sequencing (out-of-order / stale response rejection) and no deduplication `Set` on tenant ID or normalized name.
3. **Missing Deduplication in `doc-manager.js` (`populateTenantOptions`)**:
   `populateTenantOptions` did not track seen tenant IDs or normalized names with a `Set`, leaving it vulnerable if backend data had duplicate entries.
4. **Backend Missing Deduplication Guardrails**:
   - `list_house_tenants` in `src/api/routes.py` did not deduplicate by tenant ID or normalized name before returning.
   - `add_tenant` in `src/db/repository.py` inserted duplicate rows even if a tenant with the same normalized name already existed for that house.

## Fixes Implemented

### 1. Frontend: Ingest Station (`src/api/static/js/ingest-station.js`)
- Updated `populateAreas(targetArea = null, targetHouse = null)` to forward `targetHouse` directly into `populateHouses(areaSelect.value, targetHouse)`.
- In `openIngestStation()`, passed `(activeArea, activeHouse)` directly to `populateAreas(activeArea, activeHouse)` and removed the redundant second `if (activeHouse) populateHouses(...)` invocation.
- In `populateTenants()`, added request sequencing counter (`let tenantFetchSeq = 0; const currentSeq = ++tenantFetchSeq;`):
  - Any stale or superseded fetch response is rejected early with `if (currentSeq !== tenantFetchSeq) return;`.
- Replaced innerHTML only right before rendering options and used `const seen = new Set()` to deduplicate on both `id:${t.id}` and `name:${normName}` for both API responses and tree fallback nodes.

### 2. Frontend: Document Manager Modal (`src/api/static/js/doc-manager.js`)
- In `populateTenantOptions()`, added a `const seen = new Set()` filter to guarantee tenant options are deduplicated by ID and normalized name before appending to `docModalTenantSelect`.

### 3. Backend: Route Deduplication (`src/api/routes.py`)
- In `list_house_tenants()`, added `seen_ids = set()` and `seen_names = set()` deduplication logic to return only unique tenant records per house.

### 4. Backend: Repository Deduplication (`src/db/repository.py`)
- In `add_tenant()`, added an existence lookup by `house_id` and normalized tenant name before insertion. If an identical tenant already exists, the existing `Tenant` model record is returned instead of inserting a duplicate row.

## Verification & Automated Tests
1. **Frontend Vitest Suites (`tests/frontend/components/ingest_station.test.js`)**:
   - Added test: `does not duplicate tenants in ingest-tenant-select when openIngestStation is called`
   - Added test: `deduplicates duplicate tenant IDs and normalized names in populateTenants`
   - Added test: `ignores stale out-of-order responses in populateTenants`
   - Added test: `handles concurrent populateTenants calls without duplicating tenant options`
   - **Result**: 51/51 tests passing in `npm run test:frontend`.
2. **Backend Pytest Suites**:
   - Added unit test in `tests/db/test_repository.py`: duplicate normalized name returns existing tenant record.
   - Added API test in `tests/test_tenant_reallocation_api.py`: `test_list_house_tenants_deduplication`.
   - Executed `.venv/bin/pytest tests/test_v12_ingest_e2e.py tests/test_ingest_api.py tests/test_ingest_manual.py tests/db/ tests/test_api_v11.py -v` (49/49 passing).
   - Executed `.venv/bin/pytest tests/test_tenant_reallocation_api.py -v` (8/8 passing).
