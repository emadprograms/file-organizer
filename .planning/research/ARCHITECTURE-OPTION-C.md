# Architecture Blueprint: Decoupled Monorepo (Option C)
## Milestone v13.0: High-Performance ASP.NET Core 8.0 Web Server & Shared SQLite WAL Bridge

**Author:** Architecture & Research Engineering Team  
**Status:** Approved Architectural Blueprint  
**Target Milestone:** v13.0 (Phases 101–104)  
**Date:** 2026-09-09  

---

## 1. Executive Summary & Architectural Motivation

### 1.1 Context & Problem Statement
The **File Organizer** project has evolved across twelve milestones into an enterprise-grade digital archive system. In Milestone v11.0, the core data storage migrated to a relational SQLite database (`organizer.db`), and Milestone v12.0 introduced the unified manual document ingestion pipeline with relational page inheritance.

However, the existing web dashboard relies on Python FastAPI and Uvicorn. While Python is well suited for offline AI batch pipelines (PyMuPDF extraction, Gemini LLM classification, fuzzy OCR reasoning), running a Python runtime for serving web requests and static assets on client/production environments introduces major operational overhead:
1. **Runtime & Dependency Friction:** Deploying Python on restricted corporate Windows servers requires Python 3.12+ runtimes, virtual environments, native C-extension wheels (`PyMuPDF`, `greenlet`), and package management tools (`pip`, `wheel`), which are frequently blocked by corporate IT group policies.
2. **Memory Footprint & Concurrency:** The Python Uvicorn process consumes ~150–250MB RAM at idle and requires thread pool executors for disk I/O and synchronous SQLite queries.
3. **Dual Responsibility Bottleneck:** Combining high-volume batch AI document processing and interactive web dashboard serving within a single runtime leads to resource contention and potential GIL blocking during heavy ingestion jobs.

### 1.2 The Solution: Option C (Decoupled Monorepo)
**Option C** establishes a clean, decoupled boundary within a unified repository:
- **`web-net/`**: A native, self-contained **ASP.NET Core 8.0 Minimal API** application serving the web dashboard, static assets, and read/write REST endpoints with sub-1ms query execution, zero Python runtime dependency, and single-file Windows executable distribution (`FileOrganizer.exe`).
- **`src/`**: The existing **Python AI Pipeline** retained exclusively for offline, batch, and background AI ingestion tasks (`categorization/`, `llm/`, `pdf/`, `ingest/v11_ingest.py`).
- **Shared Data Contract**: The two runtimes interface exclusively through two well-defined operating system abstractions:
  1. The **relational SQLite database (`organizer.db`)** operating in **WAL (Write-Ahead Logging)** mode.
  2. The **clean physical storage hierarchy (`areas/{area}/{house}/vault/` and `batches/`)**.

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                  DECOUPLED MONOREPO                                    │
│                                                                                        │
│   ┌─────────────────────────────────────┐      ┌────────────────────────────────────┐  │
│   │   web-net/ (ASP.NET Core 8.0)       │      │   src/ (Python AI Pipeline)        │  │
│   │   ───────────────────────────       │      │   ─────────────────────────        │  │
│   │   • Minimal APIs (TypedResults)     │      │   • Batch Ingest (v11_ingest.py)   │  │
│   │   • Dapper + Microsoft.Data.Sqlite  │      │   • Gemini LLM & Classification    │  │
│   │   • Static File Serving (wwwroot)   │      │   • PyMuPDF OCR & Parsing          │  │
│   │   • Zero-AI Manual Ingest (/ingest) │      │   • Offline Migration Utilities    │  │
│   │   • Self-Contained Win-x64 Binary   │      │   • Pytest Test Suites             │  │
│   └──────────────────┬──────────────────┘      └─────────────────┬──────────────────┘  │
│                      │                                           │                     │
│                      │  Reads & Zero-AI Writes                   │  Batch AI Writes    │
│                      │                                           │                     │
│                      ▼                                           ▼                     │
│         ┌─────────────────────────────────────────────────────────────┐                │
│         │               SHARED SQLite WAL DATA BRIDGE                 │                │
│         │               ─────────────────────────────                 │                │
│         │   organizer.db  │  organizer.db-wal  │  organizer.db-shm    │                │
│         │   • PRAGMA journal_mode=WAL;                                │                │
│         │   • PRAGMA busy_timeout=5000;                               │                │
│         │   • PRAGMA synchronous=NORMAL;                              │                │
│         │   • PRAGMA foreign_keys=ON;                                 │                │
│         └──────────────────────────────┬──────────────────────────────┘                │
│                                        │                                               │
│                                        ▼                                               │
│         ┌─────────────────────────────────────────────────────────────┐                │
│         │             PHYSICAL STORAGE HIERARCHY (areas/)             │                │
│         │   {area}/{house}/vault/doc_{vault_id}.pdf                   │                │
│         │   {area}/{house}/batches/batch_{batch_id}_{filename}.pdf    │                │
│         └─────────────────────────────────────────────────────────────┘                │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Key Architectural Guarantees
1. **Zero Frontend Rewrite:** The existing frontend located at `src/api/static/` (`index.html`, `css/styles.css`, and modular `js/*.js`) is served directly by ASP.NET Core without modifying a single line of JavaScript or HTML.
2. **Zero Python for Web Users:** End users running the web dashboard require no Python, no Node.js, and no external runtime on their machines.
3. **High-Performance Data Access:** Utilizing `Microsoft.Data.Sqlite` and `Dapper` provides microsecond-level query deserialization directly into strongly typed C# records.
4. **Resilient Multi-Process Concurrency:** SQLite WAL mode allows arbitrary numbers of concurrent web readers alongside a single active batch writer without lock contention or `SQLITE_BUSY` errors.
5. **Windows Production-Ready:** Self-contained single-file publishing produces a standalone `FileOrganizer.exe` capable of running as an interactive console, a Windows Service (`sc.exe`), or hosted in-process inside Internet Information Services (IIS).

---

## 2. Monorepo Directory Organization & Boundary Specifications

### 2.1 Repository Directory Layout
The repository is structured to maintain strict physical and logical boundaries:

```text
file-organizer/
├── .planning/                              # GSD project plans, specs & research
│   ├── codebase/                           # System architecture & stack mappings
│   ├── milestones/                         # Milestone audits & requirements
│   ├── phases/                             # Phase execution plans & summaries
│   └── research/
│       └── ARCHITECTURE-OPTION-C.md        # This specification document
├── areas/                                  # Canonical Physical Storage Root
│   └── {area_id}/                          # e.g., "Safra C", "Riffa A"
│       └── {house_id}/                     # e.g., "514", "101 - ShortStay"
│           ├── batches/                    # Raw uploaded/scanned batch PDFs
│           │   └── batch_{batch_id}_{filename}.pdf
│           └── vault/                      # Standardized, immutable vault PDFs
│               └── doc_{vault_id}.pdf
├── organizer.db                            # Shared SQLite Database in WAL mode
├── organizer.db-wal                        # SQLite Write-Ahead Log file
├── organizer.db-shm                        # SQLite Shared Memory index file
├── src/                                    # Python AI Pipeline & Batch Ingestion
│   ├── api/
│   │   ├── models.py                       # Python API Pydantic models (contract baseline)
│   │   ├── routes.py                       # FastAPI routes (for test verification & parity)
│   │   ├── server.py                       # FastAPI server entry point
│   │   └── static/                         # [SINGLE SOURCE OF TRUTH] Frontend Assets
│   │       ├── index.html                  # Core single-page application UI
│   │       ├── css/
│   │       │   └── styles.css              # Tailwind + Custom Design System CSS
│   │       └── js/                         # Modular Frontend Controllers
│   │           ├── api.js                  # API helpers & global state
│   │           ├── app.js                  # Initialization & tab controllers
│   │           ├── area-grid.js            # Grid view & tenure metrics
│   │           ├── categories-view.js      # Category folders & document lists
│   │           ├── command-palette.js      # Spotlight search (Cmd+K)
│   │           ├── db-inspector.js         # Raw SQLite tables & schema inspector
│   │           ├── doc-manager.js          # Reassign, copy, move & rename modals
│   │           ├── doc-viewer.js           # Fullscreen PDF preview modal
│   │           ├── house-profile.js        # Arabic Tenancy Register & stats
│   │           ├── ingest-station.js       # Drag & drop upload drawer
│   │           ├── pdf-preview.js          # Hover live peek & Spacebar Quick Look
│   │           ├── resizer.js              # Resizable panel handles
│   │           ├── router.js               # Hash-based client routing
│   │           ├── sidebar.js              # Hierarchy navigation sidebar
│   │           └── timeline-view.js        # Multi-tenant chronological timeline
│   ├── categorization/                     # Python LLM Categorization logic
│   ├── core/                               # Python configuration, schema & exceptions
│   ├── db/                                 # Python SQLite connection, schema & repository
│   ├── grouping/                           # Document grouping heuristics
│   ├── ingest/
│   │   ├── manual_ingest.py                # Zero-AI direct ingest reference
│   │   └── v11_ingest.py                   # Multi-page AI batch ingestion engine
│   ├── llm/                                # Gemini LLM client and mock providers
│   ├── pdf/                                # PyMuPDF text & page processing
│   ├── pipeline/                           # Batch processing runners & orchestrators
│   └── routing/                            # Category-to-folder routing maps
├── web-net/                                # [NEW] ASP.NET Core 8.0 Web Server
│   ├── FileOrganizer.Web.csproj            # Modern C# project with minimal dependencies
│   ├── Program.cs                          # Host configuration, DI, and route mapping
│   ├── appsettings.json                    # Configuration (DB path, Areas root, logging)
│   ├── appsettings.Production.json         # Production overrides (relative paths, IIS logging)
│   ├── web.config                          # IIS In-Process hosting configuration
│   ├── Common/
│   │   ├── Constants.cs                    # Folder prefixes ("01".."13"), status constants
│   │   └── TextUtils.cs                    # Arabic normalization & phonetic matching
│   ├── Data/
│   │   ├── IDbConnectionFactory.cs         # SQLite connection factory with WAL PRAGMAs
│   │   ├── SqliteConnectionFactory.cs      # Microsoft.Data.Sqlite implementation
│   │   ├── IRepository.cs                  # High-level repository contract
│   │   ├── SqliteRepository.cs             # Dapper-based relational repository
│   │   └── Entities/                       # Dapper database entity models
│   │       ├── AreaEntity.cs
│   │       ├── HouseEntity.cs
│   │       ├── TenantEntity.cs
│   │       ├── BatchEntity.cs
│   │       ├── DocumentEntity.cs
│   │       └── PageEntity.cs
│   ├── Models/                             # Strongly typed DTOs (100% JSON Parity)
│   │   ├── HouseResponse.cs
│   │   ├── VaultFileResponse.cs
│   │   ├── CategoryResponse.cs
│   │   ├── TimelineGroupResponse.cs
│   │   ├── TreeItemResponse.cs
│   │   ├── SearchResultResponse.cs
│   │   ├── TenantItem.cs
│   │   ├── HouseProfileResponse.cs
│   │   ├── DocumentActionResponse.cs
│   │   ├── DocumentNotesResponse.cs
│   │   └── IngestResponse.cs
│   ├── Endpoints/                          # Minimal API route definitions
│   │   ├── HierarchyEndpoints.cs           # /api/tree, /api/houses
│   │   ├── HouseEndpoints.cs               # /api/areas/{a}/houses/{h}/* (profile, timeline, cat, tenant)
│   │   ├── DocumentEndpoints.cs            # /api/.../documents/{v} (patch, copy, notes, reset-lock)
│   │   ├── PdfEndpoints.cs                 # /api/pdf/{vault_id}, /api/areas/{a}/houses/{h}/pdf/{v}
│   │   ├── SearchEndpoints.cs              # /api/search
│   │   ├── IngestEndpoints.cs              # POST /api/ingest (zero-AI manual ingest)
│   │   └── DatabaseEndpoints.cs            # /api/db/info, /api/db/tables/{table}
│   ├── Services/
│   │   ├── IPdfService.cs                  # Lightweight PDF reader (page counting & slicing)
│   │   ├── NativePdfService.cs             # Fast native byte-stream PDF inspection
│   │   ├── IStorageService.cs              # Safe file vault manager
│   │   └── LocalStorageService.cs          # Local file system storage implementation
│   └── wwwroot/                            # Static asset target (synchronized during build)
│       ├── index.html
│       ├── css/
│       └── js/
└── tests/                                  # Unified Test Suites
    ├── api/                                # .NET API Integration & Parity Tests
    ├── db/                                 # SQLite relational unit tests
    └── frontend/                           # Playwright E2E UI tests
```

### 2.2 Frontend Asset Strategy: Single Source of Truth
To ensure **ZERO code duplication** and **ZERO divergence**, the frontend assets stored in `src/api/static/` remain the **Canonical Single Source of Truth**.

#### Synchronization Mechanism
During development and build, the .NET project automatically synchronizes static assets into `web-net/wwwroot/` via an MSBuild build target in `FileOrganizer.Web.csproj`:

```xml
<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <RootNamespace>FileOrganizer.Web</RootNamespace>
    <AssemblyName>FileOrganizer</AssemblyName>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.Data.Sqlite" Version="8.0.8" />
    <PackageReference Include="Dapper" Version="2.1.35" />
    <PackageReference Include="Microsoft.Extensions.Hosting.WindowsServices" Version="8.0.0" />
  </ItemGroup>

  <!-- Synchronization of Frontend Assets from Canonical Python Directory -->
  <ItemGroup>
    <FrontendSourceFiles Include="$(MSBuildThisFileDirectory)..\src\api\static\**\*.*" />
  </ItemGroup>

  <Target Name="SyncFrontendAssets" BeforeTargets="BeforeBuild">
    <Message Importance="high" Text="Synchronizing frontend assets from src/api/static to wwwroot..." />
    <Copy SourceFiles="@(FrontendSourceFiles)" 
          DestinationFolder="$(MSBuildThisFileDirectory)wwwroot\%(RecursiveDir)" 
          SkipUnchangedFiles="true" />
  </Target>

  <!-- Ensure static assets are included in self-contained publish outputs -->
  <ItemGroup>
    <Content Update="wwwroot\**\*.*">
      <CopyToOutputDirectory>PreserveNewest</CopyToOutputDirectory>
      <CopyToPublishDirectory>PreserveNewest</CopyToPublishDirectory>
    </Content>
  </ItemGroup>
</Project>
```

#### Why This Works Seamlessly
- **Identical HTTP Routing:** In ASP.NET Core, `app.UseDefaultFiles()` and `app.UseStaticFiles()` serve files directly from `wwwroot/`. A request for `GET /` serves `index.html`, `GET /css/styles.css` serves the stylesheet, and `GET /js/app.js` serves the script, mirroring FastAPI's `app.mount("/", StaticFiles(directory=static_dir, html=True))`.
- **Absolute Relative Paths:** The frontend uses relative paths (`./api.js`, `/api/houses`, `/api/search`). Because the API paths are ported with 100% path parity, not a single API call in `js/*.js` requires change.

---

## 3. SQLite Concurrency & WAL Mode Bridge

### 3.1 Understanding SQLite Concurrency in WAL Mode
By default, SQLite uses a rollback journal, which enforces coarse-grained locking: any write lock blocks all concurrent readers, and any active read lock blocks all writers.

In **Write-Ahead Logging (WAL)** mode (`PRAGMA journal_mode = WAL;`):
1. **Readers Never Block Writers:** Readers read a snapshot of the database from the original `.db` file and the `.db-wal` file up to the point of their transaction start.
2. **Writers Never Block Readers:** When a process (such as a Python batch ingestion worker) writes to the database, new pages are simply appended to the end of `organizer.db-wal`. Concurrent readers reading from earlier snapshots continue undisturbed.
3. **Only One Writer at a Time:** SQLite permits at most one concurrent writer across all processes on the operating system.

```text
                           ┌───────────────────────────────┐
                           │      Concurrent Readers       │
                           │   (.NET Web Client Requests)  │
                           └───────┬───────────────┬───────┘
                                   │               │
                            Read Snapshot   Read Snapshot
                                   │               │
                                   ▼               ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        SHARED DISK STORAGE                             │
│                                                                        │
│   ┌───────────────────────────┐      ┌──────────────────────────────┐  │
│   │       organizer.db        │      │      organizer.db-wal        │  │
│   │   (Base Database Pages)   │      │  (Appended Write Operations) │  │
│   └─────────────▲─────────────┘      └──────────────▲───────────────┘  │
│                 │                                   │                  │
│                 │ Passive Checkpoint                │ Atomic Append    │
│                 │ (1000 pages)                      │                  │
└─────────────────┼───────────────────────────────────┼──────────────────┘
                  │                                   │
                  │                            ┌──────┴───────┐
                  └────────────────────────────┤ Single Writer│
                                               │(Python Batch)│
                                               └──────────────┘
```

### 3.2 Microsoft.Data.Sqlite Connection String & PRAGMA Strategy
In .NET 8.0, the recommended ADO.NET provider is `Microsoft.Data.Sqlite`.

#### Connection String
```csharp
"Data Source=organizer.db;Mode=ReadWrite;Cache=Default;Pooling=True;"
```

#### Cache Mode Analysis: Why `Cache=Default` (or `Private`) over `Shared`
In multi-process SQLite environments with WAL mode, `Cache=Shared` (in-process table/page cache sharing between connections) has historical quirks regarding lock escalation and cross-thread table locks. 
**Best practice for ASP.NET Core Minimal APIs:** Use `Cache=Default` (private connection cache) combined with connection pooling (`Pooling=True;`). Each connection maintains its own transaction boundary, while SQLite's shared memory file (`organizer.db-shm`) coordinates WAL frames across all processes.

#### Mandatory PRAGMA Initialization
Every opened SQLite connection in .NET must execute the following PRAGMAs immediately upon opening:

| PRAGMA | Recommended Value | Purpose & Architectural Impact |
|---|---|---|
| `PRAGMA journal_mode = WAL;` | `WAL` | Enables Write-Ahead Logging. (Persistent in DB header, but explicitly verified on connection initialization). |
| `PRAGMA busy_timeout = 5000;` | `5000` | **Crucial for multi-process safety.** If Python holds a write lock, .NET will wait up to 5,000ms for the lock to clear instead of immediately throwing `SQLite Error 5: 'database is locked'`. |
| `PRAGMA synchronous = NORMAL;` | `NORMAL` | In WAL mode, `NORMAL` guarantees full ACID durability across OS crashes while eliminating synchronous disk `fsync` calls on every transaction commit, providing a 10x-50x write throughput boost. |
| `PRAGMA foreign_keys = ON;` | `ON` | Enforces relational integrity across `areas`, `houses`, `tenants`, `batches`, `documents`, and `pages`. SQLite disables foreign keys by default per connection. |
| `PRAGMA temp_store = MEMORY;` | `MEMORY` | Stores temporary tables, indices, and view results in RAM rather than generating temporary disk files. |
| `PRAGMA cache_size = -20000;` | `-20000` | Configures ~20MB page cache in RAM per active connection for instantaneous query execution. |

### 3.3 Multi-Process Concurrency & Safety Rules
When both the Python AI batch ingestion pipeline (`src/ingest/v11_ingest.py`) and the .NET web server (`web-net`) operate against `organizer.db` simultaneously, the following concurrency rules must be enforced:

1. **Short Write Transaction Lifetimes:**
   - Long-running operations (such as PyMuPDF OCR, Gemini LLM calls, image downsampling, or large disk file copies) must **NEVER** occur inside an active database transaction.
   - All AI inference and PDF slicing to disk must be performed first. The database transaction should only be opened to execute the rapid `INSERT/UPDATE` queries, then immediately committed and closed (`< 50ms` transaction duration).
2. **Immediate Transactions for Writers:**
   - Any write transaction should begin with `BEGIN IMMEDIATE` rather than deferred `BEGIN`. This reserves the write lock immediately and prevents deadlock scenarios where two processes read and subsequently try to upgrade to a write lock at the same time.
3. **Passive WAL Checkpointing:**
   - Do not invoke aggressive `PRAGMA wal_checkpoint(TRUNCATE)` during active web serving, as truncate checkpointing requires an exclusive lock that waits for all active readers to drain. 
   - Rely on SQLite's automatic passive checkpointing (`PRAGMA wal_autocheckpoint = 1000;`), which transfers committed frames to the main `.db` file in the background without interrupting active readers.

---

## 4. Complete API Contract Mapping & Schema Specifications

The ASP.NET Core 8.0 server must achieve **100% JSON response parity** with the FastAPI backend. Below is the complete contract mapping for all core endpoints.

### 4.1 `GET /api/tree`
- **Purpose:** Delivers the complete hierarchical navigation tree (Areas → Houses → Tenants) along with document counts and tenure categories.
- **HTTP Method:** `GET`
- **Path:** `/api/tree`
- **Query Parameters:**
  - `include_categories`: `bool` (default: `false`)
  - `include_timeline`: `bool` (default: `false`)
- **Success Status Code:** `200 OK`
- **Response Shape:** `List<TreeItemResponse>`

#### C# Response DTO
```csharp
public record TreeItemResponse(
    string Id,
    string Name,
    string Type, // "area", "house", "tenant", or "category"
    string? Subtitle = null,
    string? DurationCategory = null, // "short" (<5y), "medium" (5-10y), "long" (>10y)
    string? CurrentTenant = null,
    int TotalDocuments = 0,
    Dictionary<string, int>? CategoryCounts = null,
    List<TreeItemResponse>? Children = null
);
```

#### Dapper SQL Optimization Pattern
```csharp
// Execute parallel or joined queries to build tree in memory in < 5ms:
const string sqlAreas = "SELECT id, code FROM areas ORDER BY id;";
const string sqlHouses = "SELECT id, area_id FROM houses ORDER BY id;";
const string sqlTenants = @"
    SELECT id, house_id, name, start_date, end_date 
    FROM tenants 
    ORDER BY (CASE WHEN end_date IS NULL OR end_date = '' OR LOWER(end_date) = 'present' THEN 1 ELSE 0 END) DESC, 
             start_date DESC, id DESC;";
const string sqlDocCounts = @"
    SELECT house_id, category, COUNT(*) AS doc_count 
    FROM documents 
    GROUP BY house_id, category;";
```

---

### 4.2 `GET /api/houses`
- **Purpose:** Returns the flat list of all registered houses across all areas.
- **HTTP Method:** `GET`
- **Path:** `/api/houses`
- **Query Parameters:** None
- **Success Status Code:** `200 OK`
- **Response Shape:** `List<HouseResponse>`

#### C# Response DTO
```csharp
public record HouseResponse(
    string Id,
    string Name
);
```

#### SQL Query
```sql
SELECT id, id AS name FROM houses ORDER BY id;
```

---

### 4.3 `GET /api/areas/{area_id}/houses/{house_id}/profile` (and House Vault List)
- **Purpose:** Returns the Arabic House Tenancy Register (`سجل المستأجرين المتعاقبين`) and digital archive profile metrics.
- **HTTP Method:** `GET`
- **Path:** `/api/areas/{area_id}/houses/{house_id}/profile`
- **Path Parameters:**
  - `area_id`: `string` (e.g. `Safra C`)
  - `house_id`: `string` (e.g. `514` or `514 - Tenant Name`)
- **Success Status Code:** `200 OK`
- **Error Status Code:** `404 Not Found` (`{"detail": "House not found."}`)
- **Response Shape:** `HouseProfileResponse`

#### C# Response DTOs
```csharp
public record HouseProfileResponse(
    string HouseId,
    string AreaId,
    List<HouseTenantProfile> Tenants,
    HouseArchiveProfile Archive
);

public record HouseTenantProfile(
    int Id,
    string Name,
    string StartDate,
    string? EndDate,
    bool IsActive,
    string DurationStrAr,
    int DocumentCount,
    int CategoryCount
);

public record CategoryBreakdownItem(
    string Category,
    int DocumentCount
);

public record HouseArchiveProfile(
    int TotalDocuments,
    int TotalPages,
    int BatchCount,
    string? OldestDate,
    string? NewestDate,
    int TimespanYears,
    string TimespanStrAr,
    List<CategoryBreakdownItem> Categories
);
```

---

### 4.4 `GET /api/areas/{area_id}/houses/{house_id}/timeline`
- **Purpose:** Chronological timeline of all documents in the house, sorted descending by primary date.
- **HTTP Method:** `GET`
- **Path:** `/api/areas/{area_id}/houses/{house_id}/timeline`
- **Success Status Code:** `200 OK`
- **Response Shape:** `List<TimelineGroupResponse>`

#### C# Response DTO
```csharp
public record TimelineGroupResponse(
    string VaultId,
    string PrimaryTenant,
    int? TenantId,
    List<string> Dates,
    string BriefArabicTitle,
    string? Category,
    int IsManual,
    string? Notes
);
```

#### SQL Query
```sql
SELECT d.vault_id AS VaultId,
       COALESCE(t.name, '') AS PrimaryTenant,
       d.tenant_id AS TenantId,
       d.primary_date AS PrimaryDate,
       COALESCE(d.arabic_title, '') AS BriefArabicTitle,
       COALESCE(d.category, '') AS Category,
       COALESCE(d.is_manual, 0) AS IsManual,
       d.notes AS Notes
FROM documents d
LEFT JOIN tenants t ON d.tenant_id = t.id
WHERE d.house_id = @HouseId OR d.house_id = @CleanHouseId
ORDER BY d.primary_date DESC;
```

---

### 4.5 `GET /api/areas/{area_id}/houses/{house_id}/categories`
- **Purpose:** Category folder breakdown containing documents grouped by tenant and prefixed category name.
- **HTTP Method:** `GET`
- **Path:** `/api/areas/{area_id}/houses/{house_id}/categories`
- **Success Status Code:** `200 OK`
- **Response Shape:** `List<CategoryResponse>`

#### C# Response DTO
```csharp
public record CategoryResponse(
    string Tenant,
    string Name,
    int DocumentCount,
    List<VaultFileResponse> Documents
);

public record VaultFileResponse(
    string VaultId,
    string Filename,
    int StartPage,
    int EndPage,
    string Date,
    string Tenant,
    int? TenantId,
    string? Category,
    string? BriefArabicTitle,
    int IsManual,
    string? Notes
);
```

---

### 4.6 `GET /api/areas/{area_id}/houses/{house_id}/tenants`
- **Purpose:** Returns the deduplicated list of tenants for a given house.
- **HTTP Method:** `GET`
- **Path:** `/api/areas/{area_id}/houses/{house_id}/tenants`
- **Success Status Code:** `200 OK`
- **Response Shape:** `List<TenantItem>`

#### C# Response DTO
```csharp
public record TenantItem(
    int? Id,
    string Name,
    string StartDate,
    string? EndDate,
    string? HouseId
);
```

#### SQL Query
```sql
SELECT id AS Id, name AS Name, start_date AS StartDate, end_date AS EndDate, house_id AS HouseId
FROM tenants
WHERE house_id = @HouseId OR house_id = @CleanHouseId
ORDER BY start_date DESC;
```

---

### 4.7 `GET /api/search`
- **Purpose:** Global Spotlight search across houses, tenants, and documents (with Arabic normalization and phonetic matching).
- **HTTP Method:** `GET`
- **Path:** `/api/search`
- **Query Parameters:**
  - `q`: `string` (Search query string)
- **Success Status Code:** `200 OK`
- **Response Shape:** `List<SearchResultResponse>`

#### C# Response DTO
```csharp
public record SearchResultResponse(
    string Id,
    string Type, // "house", "tenant", or "document"
    string Title,
    string? Subtitle,
    string Url,
    string? AreaId,
    string? HouseId,
    string? TenantName,
    string? Category,
    string? Date,
    string? VaultId,
    int? IsManual,
    string? ExtraInfo
);
```

#### Search Ranking & Normalization Architecture
1. **House Matching:** `LOWER(id) LIKE @q OR LOWER(area_id) LIKE @q`.
2. **Tenant Matching:** Evaluates Arabic phonetic normalization (`ar_to_en` phonetic map, removing vowels and duplicate consonants) and Levenshtein distance ratio `> 0.7`.
3. **Document Matching:** Matches `arabic_title`, `notes`, `category`, and `pages.content_explanation`.

---

### 4.8 `GET /api/pdf/{vault_id}` & `/api/areas/{area_id}/houses/{house_id}/pdf/{vault_id}`
- **Purpose:** Fast streaming of PDF files directly from vault storage with byte-range support for instant browser rendering.
- **HTTP Method:** `GET`
- **Paths:**
  - Primary: `/api/areas/{area_id}/houses/{house_id}/pdf/{vault_id}`
  - Vault-Direct Alias: `/api/pdf/{vault_id}`
- **Response:** `FileStreamResult` / `PhysicalFileResult`
- **Media Type:** `application/pdf`
- **Headers:** `Accept-Ranges: bytes`, `Content-Disposition: inline`
- **Resolution Flow:**
  1. Check `{areas_root}/{area_id}/{house_id}/vault/doc_{vault_id}.pdf`
  2. Check `{areas_root}/{area_id}/{house_id}/vault/{vault_id}.pdf`
  3. Query `batches.file_path` from SQLite if not found on standard path.

---

### 4.9 `POST /api/ingest` (Manual Direct Ingestion)
- **Purpose:** Zero-AI direct document ingestion, writing batch/vault PDF files and inserting database records in an atomic transaction.
- **HTTP Method:** `POST`
- **Path:** `/api/ingest`
- **Content-Type:** `multipart/form-data`
- **Form Fields:**
  - `file`: `IFormFile` (PDF file, must start with `%PDF`)
  - `mode`: `string` (`"manual"`, `"assisted"`, `"auto_split"`)
  - `area_id`: `string` (Required)
  - `house_id`: `string` (Required)
  - `tenant_id`: `int?` (Optional)
  - `tenant_name`: `string?` (Optional)
  - `category`: `string?` (Optional, defaults to `"13-رسائل متنوعة"`)
  - `arabic_title`: `string?` (Optional, defaults to original filename)
  - `primary_date`: `string?` (Optional YYYY-MM-DD)
  - `notes`: `string?` (Optional)
  - `dry_run`: `bool` (default: `false`)
- **Success Status Code:** `200 OK`
- **Response Shape:** `IngestResponse`

#### C# Response DTO
```csharp
public record IngestResponse(
    string Status,
    string Mode,
    string? VaultId,
    List<string>? VaultIds,
    int? BatchId,
    int PageCount,
    int DocumentsCreated,
    string HouseId,
    string AreaId,
    string Message
);
```

#### Relational Page Inheritance Logic in .NET
For every page `1..N` of the ingested document:
- `page_number = 1..N`
- `batch_id = batchId`
- `house_id = cleanHouseId`
- `tenant_id = resolvedTenantId`
- `resolved_date = normDate`
- `category = category`
- `fine_category = category`
- `vault_id = vaultId`
- `is_continuation = (page_number > 1)`
- `content_explanation = $"Page {page_number} of {arabicTitle}"`
- `subject = (page_number == 1) ? arabicTitle : null`
- `fine_category_reason = "Manually verified by user"`

---

### 4.10 `POST /api/areas/{area_id}/houses/{house_id}/documents/{vault_id}/copy`
- **Purpose:** Duplicates an existing document to a new target category or tenant, creating a new physical vault copy and relational record.
- **HTTP Method:** `POST`
- **Path:** `/api/areas/{area_id}/houses/{house_id}/documents/{vault_id}/copy`
- **Request Body:**
```json
{
  "target_category": "05 - عقود",
  "target_tenant_id": 12,
  "target_title": "عقد إيجار مكرر"
}
```
- **Response Shape:** `DocumentActionResponse`
```csharp
public record DocumentActionResponse(
    string Status,
    string VaultId,
    string? ArabicTitle,
    string? Category,
    int? TenantId,
    string? TenantName,
    int IsManual
);
```

---

### 4.11 `PATCH /api/areas/{area_id}/houses/{house_id}/documents/{vault_id}`
- **Purpose:** Updates document metadata (title, category, tenant assignment, primary date, notes) and sets `is_manual = 1`.
- **HTTP Method:** `PATCH`
- **Path:** `/api/areas/{area_id}/houses/{house_id}/documents/{vault_id}`
- **Request Body:**
```json
{
  "arabic_title": "فاتورة معدلة",
  "category": "06 - كهرباء وماء",
  "tenant_id": 14,
  "primary_date": "2024-05-01",
  "is_manual": 1,
  "notes": "تم التعديل يدوياً"
}
```
- **Response Shape:** `DocumentActionResponse`

---

## 5. Windows Restricted Server & IIS Deployment Strategy

### 5.1 Corporate Server Constraints
In locked-down enterprise Windows environments:
1. Standard user accounts cannot install runtimes or use administrative installer packages (`.msi`).
2. PowerShell script execution is restricted (`ExecutionPolicy Restricted`).
3. Outbound Internet access is blocked or tightly proxied, preventing package downloads (`pip install`, `nuget`).
4. Applications must run either as a stand-alone desktop executable, a Windows Background Service, or integrated into existing IIS infrastructure.

### 5.2 Single-File Self-Contained Compilation
ASP.NET Core 8.0 natively supports bundling the entire .NET runtime, garbage collector, base class libraries, third-party NuGet assemblies, native SQLite libraries (`e_sqlite3.dll`), and static web assets into a **single self-contained `.exe`**:

#### Publish Command
```bash
dotnet publish web-net/FileOrganizer.Web.csproj \
    -c Release \
    -r win-x64 \
    --self-contained true \
    -p:PublishSingleFile=true \
    -p:IncludeNativeLibrariesForSelfExtract=true \
    -p:EnableCompressionInSingleFile=true \
    -p:DebugType=None \
    -p:DebugSymbols=false \
    -o ./publish/win-x64
```

#### Build Output
- **File:** `FileOrganizer.exe` (~65MB–75MB)
- **Prerequisites on Target Server:** **NONE.** No .NET SDK, no .NET Runtime, no Python, and no C++ redistributable packages required.
- **Execution:** Simply double-clicking `FileOrganizer.exe` starts Kestrel listening on `http://localhost:5000` and immediately opens the web dashboard.

---

### 5.3 Production IIS In-Process Hosting
For environments with existing IIS servers, the application can be hosted inside IIS using the **ASP.NET Core Module v2 (AspNetCoreModuleV2)** with `hostingModel="inprocess"`. In-process hosting executes the .NET Core app directly inside the IIS worker process (`w3wp.exe`), delivering maximum throughput and zero network hop latency.

#### Production `web.config`
```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <location path="." inheritInChildApplications="false">
    <system.webServer>
      <handlers>
        <add name="aspNetCore" path="*" verb="*" modules="AspNetCoreModuleV2" resourceType="Unspecified" />
      </handlers>
      <aspNetCore processPath=".\FileOrganizer.exe" 
                  arguments="" 
                  stdoutLogEnabled="true" 
                  stdoutLogFile=".\logs\stdout" 
                  hostingModel="inprocess">
        <environmentVariables>
          <environmentVariable name="ASPNETCORE_ENVIRONMENT" value="Production" />
          <environmentVariable name="ORGANIZER_DB_PATH" value="..\organizer.db" />
          <environmentVariable name="AREAS_ROOT_PATH" value="..\areas" />
        </environmentVariables>
      </aspNetCore>
      <security>
        <requestFiltering>
          <!-- Allow up to 100MB PDF manual uploads -->
          <requestLimits maxAllowedContentLength="104857600" />
        </requestFiltering>
      </security>
    </system.webServer>
  </location>
</configuration>
```

#### IIS Permissions & Application Pool Identity
- The IIS Application Pool identity (`IIS AppPool\FileOrganizerPool` or `NETWORK SERVICE`) must be granted **Read & Write** NTFS permissions on:
  1. `organizer.db`, `organizer.db-wal`, and `organizer.db-shm`
  2. The database parent directory (SQLite requires directory write permissions to create temporary rollback files and locks)
  3. The `areas/` physical vault directory for batch uploads and PDF storage.

---

### 5.4 Windows Service Deployment via `sc.exe`
For headless server operation without IIS, `FileOrganizer.exe` can be registered as a native Windows Service that boots automatically on machine startup:

#### 1. Code Configuration (`Program.cs`)
```csharp
var builder = WebApplication.CreateBuilder(args);
builder.Host.UseWindowsService(); // Enables Windows Service lifecycle integration
```

#### 2. Service Creation (`sc.exe`)
```cmd
:: 1. Create the Windows Service
sc.exe create "FileOrganizerService" binPath= "C:\Apps\FileOrganizer\FileOrganizer.exe --service" start= auto DisplayName= "File Organizer Web Server"

:: 2. Configure Automatic Recovery on Crash
sc.exe failure "FileOrganizerService" reset= 86400 actions= restart/5000/restart/10000/restart/30000

:: 3. Start the Service
sc.exe start "FileOrganizerService"
```

#### 3. URL ACL Configuration (for non-admin accounts)
```cmd
netsh http add urlacl url=http://+:5000/ user="NT AUTHORITY\NetworkService"
netsh advfirewall firewall add rule name="FileOrganizer Web" dir=in action=allow protocol=TCP localport=5000
```

---

## 6. Concrete C# Reference Architecture & Code Patterns

### 6.1 `SqliteConnectionFactory.cs`
Ensures that all connections created by Dapper enforce the required SQLite PRAGMAs.

```csharp
using System.Data;
using Microsoft.Data.Sqlite;

namespace FileOrganizer.Web.Data;

public interface IDbConnectionFactory
{
    IDbConnection CreateConnection();
}

public class SqliteConnectionFactory : IDbConnectionFactory
{
    private readonly string _connectionString;

    public SqliteConnectionFactory(IConfiguration configuration)
    {
        var dbPath = configuration["ORGANIZER_DB_PATH"] ?? "organizer.db";
        var builder = new SqliteConnectionStringBuilder
        {
            DataSource = dbPath,
            Mode = SqliteOpenMode.ReadWriteCreate,
            Cache = SqliteCacheMode.Default,
            Pooling = true
        };
        _connectionString = builder.ToString();
    }

    public IDbConnection CreateConnection()
    {
        var conn = new SqliteConnection(_connectionString);
        conn.Open();

        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"
            PRAGMA foreign_keys = ON;
            PRAGMA journal_mode = WAL;
            PRAGMA synchronous = NORMAL;
            PRAGMA busy_timeout = 5000;
            PRAGMA temp_store = MEMORY;
            PRAGMA cache_size = -20000;
        ";
        cmd.ExecuteNonQuery();

        return conn;
    }
}
```

### 6.2 Dapper Repository Implementation Pattern
```csharp
using System.Data;
using Dapper;
using FileOrganizer.Web.Models;

namespace FileOrganizer.Web.Data;

public class SqliteRepository : IRepository
{
    private readonly IDbConnectionFactory _factory;

    public SqliteRepository(IDbConnectionFactory factory)
    {
        _factory = factory;
    }

    public async Task<IEnumerable<HouseResponse>> ListHousesAsync()
    {
        using var conn = _factory.CreateConnection();
        const string sql = "SELECT id AS Id, id AS Name FROM houses ORDER BY id;";
        return await conn.QueryAsync<HouseResponse>(sql);
    }

    public async Task<IEnumerable<TimelineGroupResponse>> GetTimelineAsync(string houseId, string cleanHouseId)
    {
        using var conn = _factory.CreateConnection();
        const string sql = @"
            SELECT d.vault_id AS VaultId,
                   COALESCE(t.name, '') AS PrimaryTenant,
                   d.tenant_id AS TenantId,
                   d.primary_date AS PrimaryDateStr,
                   COALESCE(d.arabic_title, '') AS BriefArabicTitle,
                   COALESCE(d.category, '') AS Category,
                   COALESCE(d.is_manual, 0) AS IsManual,
                   d.notes AS Notes
            FROM documents d
            LEFT JOIN tenants t ON d.tenant_id = t.id
            WHERE d.house_id = @HouseId OR d.house_id = @CleanHouseId
            ORDER BY d.primary_date DESC;";

        var rows = await conn.QueryAsync(sql, new { HouseId = houseId, CleanHouseId = cleanHouseId });
        return rows.Select(r => new TimelineGroupResponse(
            VaultId: r.VaultId,
            PrimaryTenant: r.PrimaryTenant,
            TenantId: (int?)r.TenantId,
            Dates: string.IsNullOrEmpty(r.PrimaryDateStr) ? new List<string>() : new List<string> { (string)r.PrimaryDateStr },
            BriefArabicTitle: r.BriefArabicTitle,
            Category: r.Category,
            IsManual: (int)r.IsManual,
            Notes: r.Notes
        ));
    }
}
```

### 6.3 Minimal API Registration (`Program.cs`)
```csharp
using FileOrganizer.Web.Data;
using FileOrganizer.Web.Endpoints;

var builder = WebApplication.CreateBuilder(args);

// Add Windows Service Support
builder.Host.UseWindowsService();

// Register Data Services
builder.Services.AddSingleton<IDbConnectionFactory, SqliteConnectionFactory>();
builder.Services.AddScoped<IRepository, SqliteRepository>();

// Configure CORS for local development
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy => policy.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader());
});

var app = builder.Build();

app.UseCors();
app.UseDefaultFiles();
app.UseStaticFiles();

// Register API Route Groups
app.MapHierarchyEndpoints();
app.MapHouseEndpoints();
app.MapDocumentEndpoints();
app.MapSearchEndpoints();
app.MapPdfEndpoints();
app.MapIngestEndpoints();
app.MapDatabaseEndpoints();

app.Run();
```

---

## 7. Roadmap & Phase Execution Sequence (v13.0)

| Phase | Title | Core Deliverables | Success Gate |
|---|---|---|---|
| **Phase 101** | **Architecture & Monorepo Restructuring Research** *(Current)* | Architectural deep dive, monorepo directory layout, SQLite WAL bridge research, API contract mapping, Windows/IIS deployment plan. | Architecture blueprint approved; planning files updated. |
| **Phase 102** | **ASP.NET Core Data Layer & Repository (Dapper + SQLite WAL)** | Project scaffolding in `web-net/`, `SqliteConnectionFactory`, Dapper entity mappings, repository implementations for houses, tenants, categories, documents, and search. | All repository methods unit tested with SQLite in-memory and disk WAL databases; query execution < 10ms. |
| **Phase 103** | **ASP.NET Core Minimal API Endpoints & Static Serving** | Minimal API routes for all 11 endpoints, zero-AI manual ingest endpoint (`POST /api/ingest`), static file serving from `wwwroot/` with build-time asset sync, PDF streaming with byte-range support. | Full web dashboard loads and functions with 100% UI and API parity served entirely by .NET. |
| **Phase 104** | **Parity Verification, Windows Single-File Build & Milestone Audit** | Automated API parity test suite comparing Python and .NET backends, Windows self-contained single-file publish verification (`FileOrganizer.exe`), milestone audit against ARCH-01, NET-01 to NET-04, and VER-05 to VER-06. | 100% parity test pass rate; single-file executable runs standalone with zero external dependencies. |

---

## 8. Conclusion
The **Decoupled Monorepo Architecture (Option C)** provides the ideal long-term technical foundation for the File Organizer repository. By maintaining the Python AI batch pipeline in `src/` while delivering a high-performance, single-file, zero-dependency ASP.NET Core 8.0 server in `web-net/`, the system achieves:
1. **Uncompromised Web Performance:** Instant page loads, sub-5ms queries, and minimal resource utilization.
2. **Simplified Corporate Deployment:** Frictionless deployment on restricted Windows environments via a standalone `.exe`, Windows Service, or IIS in-process hosting.
3. **Rock-Solid Data Integrity:** SQLite WAL mode guarantees seamless, non-blocking concurrent reads and writes across both runtimes.
