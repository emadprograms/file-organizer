# Quick Task: Separate Ingest Station into Three Intuitive Sections (1-to-1, 1-to-Many, Many-to-1)

## Context & Motivation
The user requested a cleaner, more intuitive architecture for the Ingest Station instead of a monolithic batch screen:
> "I don't think it should be like this. I think that even batch we should have different sections. so something like single document. one to many documents (one document that goes into multiple houses), many to one (many different documents for the same house). I think ust these two are good enough. otherwise it'll get confusing. it won't be intuitive. is there an intuitive way of adding something? add that too. but I think these all should be separate sections."

By explicitly separating the modal into 3 distinct, purpose-built workflows, the user never has to decipher confusing configurations:
1. **Single File (1 Document → 1 House)**: Standard direct filing with live PDF preview, target house, latest tenant, category, and date.
2. **Broadcast Notice (1 Document → Multiple Houses)**: Ideal for circulars, building rules, or utility notices. Upload 1 PDF (with preview), pick shared category & date, and check off multiple target houses from a clean, searchable checklist. Each house automatically assigns its latest tenant.
3. **House Batch (Multiple Documents → 1 House)**: Ideal for filing a stack of papers/bills for a specific house. Select the Target Area and Target House upfront. Upload multiple PDFs. Each file gets an editable clean title and date, defaulting to that house and its latest tenant.

## Proposed Implementation

### 1. Mode Switcher (`src/api/static/index.html`)
Replace the binary radio toggle with a clean 3-tab segmented navigation bar:
- `[ 📄 Single File (1 → 1) ]`
- `[ 📢 Broadcast (1 Doc → Many Houses) ]`
- `[ 📁 House Batch (Many Docs → 1 House) ]`

### 2. Dedicated Section Containers
- **Section 1: `#ingest-mode-single-section` (1 → 1)**
  - Left: Dropzone, file info banner, live PDF preview.
  - Right: Target Area & House selects, Assigned Tenant (auto latest, with new tenant toggle), Category, Title, Date, Notes.
- **Section 2: `#ingest-mode-broadcast-section` (1 → Many)**
  - Left: 1 PDF dropzone + live PDF preview, Category select, Document Title, Primary Date.
  - Right: Target Area select, "Select All / Deselect All" toggle, searchable House checklist where each item displays `House {id}` and `Tenant: {latest_tenant}`.
  - Action button: `⚡ Broadcast to {N} Houses`.
- **Section 3: `#ingest-mode-housebatch-section` (Many → 1)**
  - Top: Target Area & Target House select upfront, Assigned Tenant (auto latest).
  - Middle: Multi-file dropzone + file queue list. Each row displays the file name, auto-cleaned editable title, category select (defaulting to e.g. utility bills or contracts), and date.
  - Action button: `⚡ File {N} Documents into House {house}`.

### 3. Logic & State Management (`src/api/static/js/ingest-station.js`)
- Tab switcher wiring with instant UI transitions.
- Context inheritance: active area and house populate into each mode seamlessly.
- Sequential ingestion execution for both Broadcast and House Batch modes with animated progress bar.
- Syncing frontend changes to `web-net/wwwroot/` upon build.

### 4. Verification & Testing
- Vitest unit tests in `tests/frontend/components/ingest_station.test.js` covering:
  - Tab switching across all 3 sections.
  - Broadcast mode house selection, tenant resolution, and execution.
  - House Batch mode multi-file queue and execution.
- Playwright E2E tests in `tests/frontend/test_ingest_batch_playwright.py` covering:
  - Switching between the 3 sections in real headless browser.
  - Filing a 1-to-many broadcast document.
  - Filing a many-to-1 house batch.
- Run full Vitest, Pytest, and .NET test suites.
