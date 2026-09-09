# Phase 102 Summary: ASP.NET Core Data Layer & Repository (Dapper + SQLite WAL)

## Overview
Phase 102 implements the native data access layer in ASP.NET Core 8.0, satisfying requirement **NET-01**. The solution utilizes `Microsoft.Data.Sqlite` in WAL (Write-Ahead Logging) mode and `Dapper` for high-throughput, microsecond-latency relational query deserialization.

The C# project is scaffolded in `web-net/` alongside an automated build-time static asset synchronization target and a comprehensive xUnit test suite in `web-net/FileOrganizer.Tests/`.

---

## Key Components Implemented

### 1. Project Scaffolding & Build Automation (`web-net/FileOrganizer.Web.csproj`)
- **Target Framework:** `net8.0`.
- **NuGet Packages:**
  - `Microsoft.Data.Sqlite` (8.0.8)
  - `Dapper` (2.1.35)
- **Zero-Drift Asset Synchronization:**
  Configured MSBuild build target `CopyFrontendFiles` which mirrors all assets from `src/api/static/**` into `web-net/wwwroot/` before build and publish, ensuring zero frontend duplicate code and zero frontend rewrite.

### 2. Domain Models & Parity DTOs (`web-net/Models/`)
- **Relational Domain Models:**
  - `Area.cs`: Matches `areas` table (`Id`, `Code`).
  - `House.cs`: Matches `houses` table (`Id`, `AreaId`).
  - `Tenant.cs`: Matches `tenants` table (`Id`, `HouseId`, `Name`, `StartDate`, `EndDate`).
  - `Document.cs`: Matches `documents` table (`VaultId`, `HouseId`, `TenantId`, `BatchId`, `PrimaryDate`, `ArabicTitle`, `Category`, `PageCount`, `IsManual`, `Notes`, `CreatedAt`).
  - `Batch.cs`: Matches `batches` table (`Id`, `HouseId`, `Filename`, `FilePath`, `PageCount`, `Status`, `CreatedAt`).
  - `Page.cs`: Matches `pages` table (`Id`, `BatchId`, `PageNumber`, `HouseId`, `Category`, `ContentExplanation`, `ExpectedTenantName`, `Subject`, `IsContinuation`, `TenantId`, `ResolvedDate`, `FineCategory`, `FineCategoryReason`, `VaultId`).
- **Strongly Typed DTOs (`DTOs.cs`):**
  - `TreeAreaDto`, `TreeHouseDto`, `TreeTenantDto` matching `/api/tree` JSON structure.
  - `HouseCardDto` with tenure calculation and color coding (`<5y` green, `5-10y` yellow, `>10y` red).
  - `HouseProfileDto`, `HouseTenantProfileDto`, `HouseArchiveProfileDto`, `CategoryBreakdownItemDto` matching `/api/areas/{a}/houses/{h}/profile`.
  - `TimelineItemDto` matching `/api/areas/{a}/houses/{h}/timeline`.
  - `CategoryFolderDto`, `VaultFileDto` matching `/api/areas/{a}/houses/{h}/categories`.
  - `SearchResultDto` matching `/api/search` across houses, tenants, documents, and pages.
  - `TenantDto` matching `/api/areas/{a}/houses/{h}/tenants`.
  - `DocumentDetailsDto`, `PageItemDto` matching single document inspection and physical path calculation.
  - `IngestRequestDto`, `IngestResponseDto`, `DocumentActionResponseDto`.

### 3. Data Access Layer & WAL Connection Management (`web-net/Data/`)
- **`SqliteDbConnectionFactory.cs` (`ISqliteDbConnectionFactory`):**
  - Enforces connection pooling: `Data Source={dbPath};Mode={mode};Cache=Default;Pooling=True;`
  - Executes required SQLite pragmas on connection initialization:
    - `PRAGMA journal_mode = WAL;` (Write-Ahead Logging for multi-process concurrency)
    - `PRAGMA busy_timeout = 5000;` (Wait up to 5s on write contention)
    - `PRAGMA foreign_keys = ON;` (Relational integrity enforcement)
    - `PRAGMA synchronous = NORMAL;` (Crash resilience with max write performance)
- **`DatabaseInitializer.cs`:**
  - Automated SQLite schema migration and table/index creation.
- **`FileOrganizerRepository.cs` (`IFileOrganizerRepository`):**
  - `GetTreeAsync`: Hierarchical navigation tree matching `/api/tree` with tenure categorization and document counts.
  - `GetHousesAsync(string? areaId)`: Flat house list and card summaries with tenure duration, tenure color coding (<5y green, 5-10y yellow, >10y red), and document totals.
  - `GetHouseProfileAsync(string areaId, string houseId)`: Arabic Tenancy Register, active resident, duration string formatting, and digital archive metrics.
  - `GetTimelineAsync(string areaId, string houseId, string? tenantName)`: Chronological document timeline ordered descending by primary date.
  - `GetCategoriesAsync(string areaId, string houseId)`: Grouped folder views with 13 standard folders and custom folders.
  - `GetTenantsAsync(string houseId)`: Deduplicated tenant roster with active/latest precedence.
  - `SearchAsync(string query, int limit)`: Multi-table Spotlight search across houses, tenants, documents, and pages with phonetic Arabic normalization and Levenshtein similarity.
  - `GetDocumentByVaultIdAsync(string vaultId, string? areasRoot)`: Document metadata, page list, and resolved physical vault path.
  - `AddManualDocumentAsync(IngestRequestDto request)`: Zero-AI direct document ingestion, batch registration, document insertion with `is_manual=1`, and relational page inheritance across all pages 1..N.
  - `UpdateDocumentAsync(...)`: Document metadata update with synchronization to child page records.
  - `CopyDocumentAsync(...)`: Document duplication under a new vault ID with `is_manual=1` and optional disk file copy.

### 4. Arabic Utilities & Routing Constants (`web-net/Common/`)
- **`Constants.cs`:** Standard 13 Arabic folder definitions ("01 - بيانات أساسية" through "13 - رسائل متنوعة") and automatic 2-digit category prefix formatting.
- **`TextUtils.cs`:** Arabic duration calculations (`FormatArabicDuration`, `FormatArabicTimespan`), phonetic normalization (`PhoneticNormalize`), Levenshtein similarity ratio (`Similarity`), and house number extraction.

---

## Test Verification

The xUnit test project (`web-net/FileOrganizer.Tests/FileOrganizer.Tests.csproj`) executes comprehensive repository tests against real SQLite WAL databases:

- `GetTreeAsync_ReturnsHierarchicalTreeWithTenureMetrics`: Verifies tree structure, active tenant, and tenure duration category.
- `GetHousesAsync_ReturnsTenureColorCoding`: Verifies `<5y` green, `5-10y` yellow, and `>10y` red color coding.
- `GetHouseProfileAsync_ReturnsProfileTenancyRegisterAndArabicStrings`: Verifies profile metrics, archive stats, and Arabic duration strings.
- `GetTimelineAsync_ReturnsChronologicalDocuments`: Verifies descending date ordering and timeline item structure.
- `GetCategoriesAsync_ReturnsStandardAndCustomFolders`: Verifies prefixed category names and document grouping.
- `GetTenantsAsync_ReturnsDeduplicatedTenants`: Verifies deduplication and chronological ordering.
- `SearchAsync_SearchesHousesTenantsDocumentsAndPages`: Verifies multi-table search across houses, tenants, documents, and pages.
- `AddManualDocumentAsync_VerifiesIsManualAndPageInheritance`: Verifies `is_manual = 1`, batch registration, and relational page inheritance (Page 1 non-continuation with subject, Pages 2+ continuation).
- `UpdateDocumentAsync_UpdatesMetadataAndSyncsPages`: Verifies metadata updates and synchronization to page records.
- `CopyDocumentAsync_DuplicatesDocumentWithIsManualOne`: Verifies document record duplication with `is_manual = 1`.
- `GetDocumentByVaultIdAsync_ReturnsMetadataAndPages`: Verifies metadata inspection, page list, and physical path calculation.
- `Concurrency_MultipleReadersAndWriter_ExecuteWithoutLockErrorsInWalMode`: Verifies concurrent readers and writer executing without locking conflicts in SQLite WAL mode.

### Test Results
```text
Starting test execution, please wait...
A total of 1 test files matched the specified pattern.

Passed!  - Failed:     0, Passed:    12, Skipped:     0, Total:    12, Duration: 85 ms - FileOrganizer.Tests.dll (net8.0)
```

---

## Requirements Traceability

| Requirement | Description | Status | Verification |
|---|---|---|---|
| **NET-01** | ASP.NET Core 8.0 project with Dapper and `Microsoft.Data.Sqlite` in WAL mode | **Complete** | 12/12 xUnit repository tests passing; WAL connection factory and Dapper repository fully verified |

---

## Next Steps
Proceed to **Phase 103: ASP.NET Core Minimal API Endpoints & Static Serving**:
- Implement Minimal API route mappings in `web-net/Endpoints/` matching FastAPI routes with 100% JSON parity.
- Configure static asset serving from `wwwroot/`.
- Implement `POST /api/ingest` multipart endpoint and PDF streaming with byte-range support.
