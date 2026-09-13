# Phase 109: Pure .NET Core Architecture & Python Elimination - Context

**Gathered:** 2026-09-13
**Status:** Ready for planning
**Mode:** Autonomous / User Directed

<domain>
## Phase Boundary

Completely remove all legacy Python source files (`src/` Python files, `.venv/`, `requirements.txt`, `patch_index.py`, and Python pytest files in `tests/`). Reorganize the ASP.NET Core 8.0 project from `web-net/` into an idiomatic .NET solution: `src/HousingApplication.Web/` (with `Common/`, `Data/`, `Models/`, `wwwroot/`, `Program.cs`, `HousingApplication.Web.csproj`) and create `HousingApplication.sln`. Consolidate tests under `tests/` (`tests/HousingApplication.Tests/` for xUnit and `tests/frontend/` for Vitest). Update Vitest test imports to load directly from `src/HousingApplication.Web/wwwroot/js/`. Update `run-mac.sh` and `package.json`. Verify 100% test pass rate across backend and frontend with zero Python runtime.

</domain>

<decisions>
## Implementation Decisions

### Project Structure & Naming
- Rename root project from `FileOrganizer` to `HousingApplication`.
- Place the web server in `src/HousingApplication.Web/` and rename `.csproj` to `HousingApplication.Web.csproj`.
- Place backend tests in `tests/HousingApplication.Tests/` and rename `.csproj` to `HousingApplication.Tests.csproj`.
- Create a root `HousingApplication.sln` linking both projects.
- Keep frontend Vitest tests in `tests/frontend/`.

### Python Removal
- Delete legacy Python `src/` directory after moving static assets into `src/HousingApplication.Web/wwwroot/`.
- Delete `.venv/`, `.pytest_cache/`, `requirements.txt`, `patch_index.py`, and Python test files in `tests/`.
- Remove pytest scripts from `package.json`.

### Static Asset & Test Import Cutover
- Search-and-replace all test file references from `src/api/static/` to `src/HousingApplication.Web/wwwroot/`.
- Ensure all 277 Vitest frontend tests pass using the real web root.
- Ensure all 148 C# xUnit tests pass under the new project structure.

### Startup Script
- Update `run-mac.sh` to target `src/HousingApplication.Web/HousingApplication.Web.csproj`.

</decisions>

<code_context>
## Existing Code Insights
- `web-net/` is already 100% self-contained pure C# and passes all 148 tests.
- `web-net/wwwroot/` already has the full suite of frontend files (HTML, CSS, JS, PDF.js).
- Vitest tests only used `src/api/static/` as a historical mirror path.

</code_context>

<specifics>
## Specific Ideas
- All project assembly and namespace references should be clean and consistent.
- `dotnet build` and `dotnet test` must succeed with zero warnings or errors.
- `npm run test:frontend` must succeed with zero failures.

</specifics>
