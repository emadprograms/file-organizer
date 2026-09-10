# Requirements: Milestone v14.0 Power-User Operations & Portfolio Expansion

## Milestone v14.0 Goals

Equip the digital archive management system with power-user operational tools: one-click house archive ZIP export, multi-document batch operations (bulk move & bulk delete), portfolio expansion with UI-based house creation, an interactive keyboard shortcuts modal (`?`), and complete parity across both FastAPI and ASP.NET Core 8.0 backends with comprehensive test coverage.

## Requirements

### Archive Export
- [x] **EXP-01**: Backend ZIP export stream endpoint `GET /api/areas/{area}/houses/{house}/export-zip` in both FastAPI and ASP.NET Core. Packages all vault documents for the requested house into an in-memory or streamed ZIP archive with clean, collision-free Arabic filenames (`{folder_index}_{title}.pdf`), setting proper `Content-Disposition` attachment headers.
- [x] **EXP-02**: Modern UI Export Button on the House Profile header (`[ 📦 Export Archive ZIP ]`). Displays an active download spinner during generation, handles browser file download, and provides user feedback via toast notifications.

### Multi-Select Batch Document Operations
- [x] **BAT-01**: Multi-select checkbox UI in category folder document lists. Features per-card selection checkboxes, a "Select All / Deselect All" toggle, and a sleek floating bottom action bar displaying the count of selected documents and action buttons (`[ Move Selected ]`, `[ Delete Selected ]`, `[ Deselect ]`).
- [x] **BAT-02**: Batch Move and Batch Delete backend endpoints in both FastAPI and ASP.NET Core:
  - `POST /api/areas/{area}/houses/{house}/documents/batch-delete`: Cascade deletion of selected vault documents from SQLite database and filesystem storage.
  - `POST /api/areas/{area}/houses/{house}/documents/batch-move`: Move selected documents to a target category folder in a single atomic transaction.

### Portfolio Expansion
- [ ] **HSE-01**: House creation backend endpoint `POST /api/areas/{area}/houses` in both FastAPI and ASP.NET Core. Registers the house in SQLite, optionally creates the initial active tenant, and initializes the physical filesystem directory scaffold (`{area}/{house}/batches/` and `{area}/{house}/vault/`).
- [ ] **HSE-02**: "+ Add House" UI trigger and modal in the Area Grid. Allows property managers to select an Area, input House Number/Name, and optionally add an initial tenant. Dynamically refreshes the house grid upon creation without page reload.

### Keyboard Shortcuts & Verification
- [ ] **KBD-01**: Global Keyboard Shortcuts Helper Modal (`?`). Pressing `?` (Shift+/) opens a clean modal listing all available keyboard shortcuts (`⌘K` Search, `⌘I` Upload, `Space` Quick Look, `Esc` Close, `?` Shortcuts). Can be dismissed via `Esc`, close button, or backdrop click.
- [ ] **VER-07**: Comprehensive test suite covering all 4 new capabilities:
  - Backend tests in Pytest (`tests/test_v14_features.py`) and xUnit (`web-net/FileOrganizer.Tests/`).
  - Frontend Vitest component tests (`tests/frontend/components/`).
  - Playwright browser E2E tests (`tests/frontend/`).

## Traceability

| Requirement | Description | Phase | Status |
|---|---|---|---|
| EXP-01 | Backend ZIP export endpoint in FastAPI & ASP.NET Core | Phase 105 | Complete |
| EXP-02 | UI Export Archive ZIP button on House Profile | Phase 105 | Complete |
| BAT-01 | Multi-select checkboxes & floating action bar in Category View | Phase 106 | Complete |
| BAT-02 | Batch Move and Batch Delete backend endpoints | Phase 106 | Complete |
| HSE-01 | House creation backend endpoint and directory scaffold | Phase 107 | Pending |
| HSE-02 | "+ Add House" UI modal and live grid refresh | Phase 107 | Pending |
| KBD-01 | Global Keyboard Shortcuts Helper modal (`?`) | Phase 108 | Pending |
| VER-07 | Comprehensive automated testing suite (Pytest, Vitest, Playwright, xUnit) | Phase 108 | Pending |
