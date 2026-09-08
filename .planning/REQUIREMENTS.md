# Requirements: Milestone v11.0 Database Backend & Clean Storage Architecture

## Milestone v11.0 Requirements

### Database Layer & Data Models
- [ ] **DB-01**: Implement SQLite schema (`areas`, `houses`, `tenants`, `batches`, `pages`, `documents`) with foreign keys, cascading deletes, unique constraints, and performance indices.
- [ ] **DB-02**: Implement a clean Data Access Layer / Repository with connection management, transactions, and comprehensive unit tests.

### Legacy Data Migration & Storage Restructuring
- [ ] **MIG-01**: Build an idempotent migration pipeline that ingests all existing houses from `state.json`/`report.json` and legacy vault directories into SQLite.
- [ ] **MIG-02**: Restructure physical house storage on disk to clean two-folder layout (`{area}/{house_id}/batches/` and `{area}/{house_id}/vault/`), removing `.lnk` shortcuts, Arabic subfolder trees, and JSON files safely.

### Ingestion Pipeline Redesign
- [ ] **ING-01**: Redesign the ingestion workflow to register raw uploads as `batches` and persist page-level OCR/classifications in `pages`.
- [ ] **ING-02**: Directly slice PDFs into `{house}/vault/` and insert records into `documents`, completely eliminating index-shifting math and the reconciliation loop.

### FastAPI High-Performance Backend
- [ ] **API-01**: Rewrite core API endpoints (`/api/tree`, `/api/areas/{area}/houses/{house}/timeline`, `/api/areas/{area}/houses/{house}/categories`) to query SQLite with indexed joins.
- [ ] **API-02**: Implement fast SQLite search endpoint (`/api/search`) across houses, tenants, and documents.
- [ ] **API-03**: Eliminate SMB filesystem glob latency and remove in-memory tree cache workarounds, achieving sub-10ms response times.

### Comprehensive Testing & Verification
- [ ] **VER-01**: Full pytest test suite covering database models, repository queries, migration parity, and ingestion workflows.
- [ ] **VER-02**: Playwright E2E verification confirming Tree View, Grid Overview, Timeline, Categories, and PDF viewers function flawlessly on the database backend.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DB-01 | Phase 92 | Pending |
| DB-02 | Phase 92 | Pending |
| MIG-01 | Phase 93 | Pending |
| MIG-02 | Phase 93 | Pending |
| ING-01 | Phase 94 | Pending |
| ING-02 | Phase 94 | Pending |
| API-01 | Phase 95 | Pending |
| API-02 | Phase 95 | Pending |
| API-03 | Phase 95 | Pending |
| VER-01 | Phase 96 | Pending |
| VER-02 | Phase 96 | Pending |
