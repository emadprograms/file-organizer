# Requirements: Milestone v13.0 Decoupled Monorepo Architecture & Native ASP.NET Core Web Server

## Milestone v13.0 Goals

Decouple the lightweight web dashboard/UI completely from the Python AI batch ingestion pipeline by building an ASP.NET Core 8.0 Minimal API application in `web-net/`. The web server shares only `organizer.db` (SQLite in WAL mode) and the clean disk vault (`{area}/{house}/vault/`), serving the existing vanilla JS/HTML frontend from `wwwroot/` with 100% JSON parity. The Python pipeline remains in `src/` for offline/batch AI processing, and a self-contained Windows single-file executable (`FileOrganizer.exe`) is provided for restricted Windows server environments.

## Requirements

### Monorepo Architecture

- [x] **ARCH-01**: Decoupled monorepo structure (`web-net/` for ASP.NET Core, `src/` for Python AI pipeline, shared `organizer.db`). Clear directory boundary where the .NET runtime has zero dependency on the Python virtual environment, sharing only SQLite database contracts and vault file paths.

### ASP.NET Core Data Layer

- [x] **NET-01**: ASP.NET Core 8.0 project with Dapper and `Microsoft.Data.Sqlite` in WAL mode. Database connection pooling, read-optimized parameterized queries, model mapping matching existing SQLite schema (`areas`, `houses`, `tenants`, `batches`, `pages`, `documents`), and robust transaction handling.

### API Endpoints & Frontend Serving

- [x] **NET-02**: Port all read API endpoints with 100% JSON parity:
  - `GET /api/tree`: Hierarchical navigation tree matching Python schema.
  - `GET /api/houses`: Area & house summaries with metrics.
  - `GET /api/areas/{area}/houses/{house}` (and profile/vault): Specific house metadata, vault document lists, and tenancy profile.
  - `GET /api/timeline`: Multi-tenant chronological document timeline.
  - `GET /api/categories`: Category breakdown and folder groupings.
  - `GET /api/tenants`: Tenant listings and document allocations.
  - `GET /api/search`: Global search across houses, tenants, and documents (with Arabic normalization / fuzzy matching parity).
  - `GET /api/pdf/{vault_id}`: Stream PDF files directly from vault storage with proper headers and byte-range support.
- [x] **NET-03**: Implement zero-Python manual ingestion endpoint (`POST /api/ingest`) in .NET directly writing vault PDFs and SQLite records with transactional integrity, supporting multipart form upload, page counting, and folder allocation.
- [x] **NET-04**: Static file serving from `wwwroot/` with existing frontend assets (`index.html`, `js/`, `css/`), guaranteeing zero frontend rewrite.

### Verification & Deployment

- [ ] **VER-05**: API parity test suite verifying response parity between Python and .NET backends, ensuring identical JSON keys, data types, and status codes across all read and ingest endpoints.
- [ ] **VER-06**: Windows self-contained single-file publish verification (`win-x64`), generating a standalone executable (`FileOrganizer.exe`) requiring zero pre-installed .NET runtimes or Python environments.

## Traceability

| Requirement | Description | Phase | Status |
|-------------|-------------|-------|--------|
| ARCH-01 | Decoupled monorepo structure (`web-net/`, `src/`, shared `organizer.db`) | Phase 101 | Complete |
| NET-01 | ASP.NET Core 8.0 with Dapper & `Microsoft.Data.Sqlite` in WAL mode | Phase 102 | Complete |
| NET-02 | Port all read API endpoints with 100% JSON parity | Phase 103 | Complete |
| NET-03 | Zero-Python manual ingestion endpoint (`POST /api/ingest`) in .NET | Phase 103 | Complete |
| NET-04 | Static file serving from `wwwroot/` with existing frontend assets | Phase 103 | Complete |

| VER-05 | API parity test suite verifying Python vs .NET response parity | Phase 104 | Pending |
| VER-06 | Windows self-contained single-file publish verification (`win-x64`) | Phase 104 | Pending |
