# Phase 101 Summary: Architecture & Monorepo Restructuring Research

## Overview
Phase 101 delivers the complete architectural research, design contract, and execution blueprint for **Milestone v13.0: Decoupled Monorepo Architecture & Native ASP.NET Core Web Server**. It resolves requirement **ARCH-01** by establishing a strict, decoupled boundary between the web dashboard server (`web-net/`) and the Python AI batch ingestion pipeline (`src/`), bridging them seamlessly through SQLite WAL mode concurrency and the clean physical disk vault (`areas/{area}/{house}/vault/`).

The comprehensive blueprint is authored and published at [`.planning/research/ARCHITECTURE-OPTION-C.md`](../../research/ARCHITECTURE-OPTION-C.md).

---

## Key Architectural Decisions & Research Findings

### 1. Monorepo Directory Organization (Option C)
- **`web-net/` (ASP.NET Core 8.0 Minimal API)**:
  - Self-contained, lightweight C# web application.
  - Minimal dependencies: `Microsoft.Data.Sqlite`, `Dapper`, `Microsoft.Extensions.Hosting.WindowsServices`.
  - Zero Python runtime dependency: Runs independently on client or server machines without Python, virtual environments, or pip packages.
- **`src/` (Python AI Batch Pipeline)**:
  - Retained exclusively for offline, batch, and background AI ingestion tasks (`categorization/`, `llm/`, `pdf/`, `ingest/v11_ingest.py`).
  - Completely decoupled from live web traffic, eliminating GIL bottlenecks and thread pool exhaustion during heavy AI processing.
- **Frontend Asset Strategy (Zero Code Rewrite)**:
  - The canonical single source of truth for frontend assets remains at `src/api/static/` (`index.html`, `css/styles.css`, and `js/*.js`).
  - An automated build-time synchronization target in `FileOrganizer.Web.csproj` mirrors these assets into `web-net/wwwroot/` before build and publish.
  - The frontend remains 100% agnostic to whether FastAPI or ASP.NET Core is serving it, guaranteeing 0 changes to JavaScript files or HTML templates.

### 2. SQLite Concurrency & WAL Mode Bridge
- **Multi-Process Concurrency Mechanics**:
  - In WAL (Write-Ahead Logging) mode, readers read consistent snapshots from `organizer.db` and `organizer.db-wal` without blocking writers, and writers append to the WAL without blocking readers.
- **`Microsoft.Data.Sqlite` Connection Configuration**:
  - Connection string: `Data Source=organizer.db;Mode=ReadWrite;Cache=Default;Pooling=True;`
  - Connection factory enforces mandatory PRAGMAs on every connection:
    - `PRAGMA journal_mode = WAL;` (Enables write-ahead logging)
    - `PRAGMA busy_timeout = 5000;` (Critical: Waits up to 5,000ms if Python holds an active write lock, avoiding `SQLITE_BUSY` errors)
    - `PRAGMA synchronous = NORMAL;` (Ensures crash resilience without blocking fsync on every commit)
    - `PRAGMA foreign_keys = ON;` (Enforces relational integrity across all tables)
    - `PRAGMA temp_store = MEMORY;` (RAM temporary tables and query sorting)
    - `PRAGMA cache_size = -20000;` (~20MB memory cache per active connection)
- **Multi-Process Safety Rules**:
  - Short write transaction lifetimes (< 50ms): All file I/O, PDF parsing, and AI inference occur *before* opening the DB transaction.
  - Passive WAL auto-checkpointing (`PRAGMA wal_autocheckpoint = 1000;`) to avoid lock-blocking truncations while readers are active.

### 3. Complete API Contract Mapping (100% JSON Parity)
The architecture document details the exact JSON schemas, query parameters, error responses, and Dapper SQL implementations for all 11 core endpoints:
1. `GET /api/tree`: Hierarchical navigation tree with tenure categories and document counts.
2. `GET /api/houses`: Flat house list.
3. `GET /api/areas/{area_id}/houses/{house_id}/profile`: Arabic Tenancy Register and digital archive profile.
4. `GET /api/areas/{area_id}/houses/{house_id}/timeline`: Multi-tenant chronological document timeline.
5. `GET /api/areas/{area_id}/houses/{house_id}/categories`: Prefixed category groupings and document lists.
6. `GET /api/areas/{area_id}/houses/{house_id}/tenants`: Deduplicated tenant roster.
7. `GET /api/search`: Global search with Arabic phonetic normalization and Levenshtein fuzzy matching.
8. `GET /api/pdf/{vault_id}` & `/api/areas/{area_id}/houses/{house_id}/pdf/{vault_id}`: Vault PDF streaming with byte-range support.
9. `POST /api/ingest`: Zero-AI manual direct ingestion endpoint writing batch/vault PDFs and relational records with page inheritance.
10. `POST /api/areas/{area_id}/houses/{house_id}/documents/{vault_id}/copy`: Physical and relational document duplication.
11. `PATCH /api/areas/{area_id}/houses/{house_id}/documents/{vault_id}`: Document metadata update and manual lock assignment.

### 4. Windows Restricted Server & IIS Deployment Strategy
- **Self-Contained Single-File Publish**:
  ```bash
  dotnet publish web-net/FileOrganizer.Web.csproj \
      -c Release \
      -r win-x64 \
      --self-contained true \
      -p:PublishSingleFile=true \
      -p:IncludeNativeLibrariesForSelfExtract=true \
      -p:EnableCompressionInSingleFile=true \
      -o ./publish/win-x64
  ```
  Produces a standalone `FileOrganizer.exe` (~65-75MB) requiring zero pre-installed runtimes on the target Windows machine.
- **IIS In-Process Hosting**:
  - Configured via `web.config` using `AspNetCoreModuleV2` with `hostingModel="inprocess"` for maximum throughput directly inside `w3wp.exe`.
  - Detailed application pool NTFS permission specifications for `organizer.db*` and `areas/`.
- **Windows Background Service Deployment**:
  - Integration with `Microsoft.Extensions.Hosting.WindowsServices` (`builder.Host.UseWindowsService()`).
  - Automated service management commands via `sc.exe` with crash auto-restart recovery policies.

---

## Verification & Traceability

| Requirement | Description | Status | Verification Reference |
|---|---|---|---|
| **ARCH-01** | Decoupled monorepo structure (`web-net/`, `src/`, shared `organizer.db` with SQLite WAL bridge) | **Complete** | Full architecture specification in [`.planning/research/ARCHITECTURE-OPTION-C.md`](../../research/ARCHITECTURE-OPTION-C.md) |

---

## Next Steps
Proceed to **Phase 102: ASP.NET Core Data Layer & Repository (Dapper + SQLite WAL)**:
- Scaffold the `web-net/` C# project with minimal dependencies.
- Implement `SqliteConnectionFactory` with WAL mode and PRAGMA initialization.
- Implement Dapper repository models and queries matching existing SQLite schema (`areas`, `houses`, `tenants`, `batches`, `pages`, `documents`).
- Add comprehensive data layer unit tests.
