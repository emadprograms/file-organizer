# Requirements: Milestone v12.0 Unified Document Ingestion System

## Milestone v12.0 Goals

Provide a unified document ingestion system enabling instant manual ingestion (zero-AI), AI-assisted single-document preview & auto-fill, and multi-document auto-split batch ingestion, fully integrated with FastAPI endpoints and a modern Ingest Station web UI.

## Requirements

### Ingestion Engine Core

- [x] **ING-03**: Manual ingest pipeline in Python (`src/ingest/manual_ingest.py`). Uses PyMuPDF for page count, performs local text extraction, requires zero LLM API calls, copies files into `{house}/batches/` and writes documents directly to `{house}/vault/` with `is_manual=1`.
- [x] **ING-04**: Relational page inheritance for manual documents in SQLite `pages` table, linking batch pages to the newly created document.

### FastAPI Ingest Endpoints

- [ ] **API-04**: `POST /api/ingest` endpoint supporting multipart form uploads with modes:
  - `manual`: Direct ingest bypassing LLM vision/classification.
  - `assisted`: User-confirmed metadata ingest with optional AI pre-population.
  - `auto_split`: Batch split and classification pipeline.
- [ ] **API-05**: `POST /api/ingest/preview-ai` endpoint for single-document preview analysis, returning suggested metadata (category, subfolder, dates, tenant) without writing to disk or database.

### Modern Web UI (Ingest Station)

- [ ] **UI-01**: Top navbar `+ Ingest` button with keyboard shortcut (`⌘I` / `Ctrl+I`) and global contextual drag-and-drop dropzone with visual drag-over feedback.
- [ ] **UI-02**: 'Ingest Station' slide-over drawer / modal featuring:
  - Live PDF page preview.
  - Mode switcher (`Manual`, `AI-Assisted`, `Auto-Split`).
  - Target selection metadata form (Area, House, Tenant, Category/Folder, Year, Notes).
  - Quick action buttons: `✨ Auto-Fill with AI` and `⚡ Ingest Directly`.
  - Seamless real-time UI refresh of house/tenant document lists upon completion.

### Comprehensive Testing & Verification

- [ ] **VER-03**: Backend pytest test suite covering `POST /api/ingest`, `POST /api/ingest/preview-ai`, manual ingest pipeline, and page inheritance.
- [ ] **VER-04**: Frontend Vitest test suite covering Ingest Station drawer open/close, drag-and-drop dropzone, mode switching, form validation, and API submission flow.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ING-03 | Phase 97 | Completed |
| ING-04 | Phase 97 | Completed |
| API-04 | Phase 98 | Pending |
| API-05 | Phase 98 | Pending |
| UI-01 | Phase 99 | Pending |
| UI-02 | Phase 99 | Pending |
| VER-03 | Phase 100 | Pending |
| VER-04 | Phase 100 | Pending |
