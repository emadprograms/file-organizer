<!-- generated-by: gsd-doc-writer -->
# File Organizer

File Organizer is a post-processor utility that organizes categorized PDFs into a structured **Vault** and dynamically creates categorized Windows Shortcuts (`.lnk`). By using LLMs, it cleans, groups, and routes documents. It creates a robust single-source-of-truth using a unified `state.json` and a bidirectional reconciler, ensuring your physical files and organized views are always mathematically synchronized.

## Architecture Highlights (v5.3)
- **Vault Architecture:** All physical PDFs are stored immutably in `.source_files/vault/`.
- **Shortcuts:** Categorized folders (e.g., `01_بيانات شخصية`) and `[Timeline View]` contain only lightweight Windows `.lnk` shortcuts pointing to the Vault.
- **Unified State:** A single `state.json` inside `.source_files/` tracks everything.
- **Reconciliation Engine:** Bidirectionally synchronizes `state.json` with physical shortcut moves on disk, auto-adopting ghost files and cleaning up orphans.
- **Strict Verification:** Proves mathematically that the shortcuts, vault, and JSON state are 100% synchronized and valid.

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Set up a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install the dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

1. Copy the environment template and configure your API keys:
```bash
cp .env.example .env
```
Make sure to add your `GEMINI_API_KEY` to the `.env` file, as it is required to run the pipeline.

2. Run the processor on a target directory:
```bash
python src/main.py create /path/to/target_directory
```

## CLI Commands

The main entry point `src/main.py` is a robust CLI supporting multiple operations:

**Create/Process a directory:**
```bash
python src/main.py create /path/to/target_directory --model gemini-2.5-flash
```
Use `--dry-run` to preview the pipeline output without making any physical file changes.

**Verify integrity:**
Ensure that your state and vault are perfectly in sync:
```bash
python src/main.py verify /path/to/house_directory
```

**Reconcile state:**
Synchronize the internal state based on manual user moves:
```bash
python src/main.py reconcile --tenants
```

**Prepend (Inbox listener):**
Run a listener in prepend mode on the inbox directory:
```bash
python src/main.py prepend
```

## Web Interface & Navigation Shortcuts

The modern web application (`http://localhost:5000`) offers a responsive, high-performance interface for archive navigation and document management:

- **Collapsible Sidebar**: Effortlessly collapse or expand the left areas navigation sidebar using the collapse button (`<<`) in the sidebar header or the sidebar toggle button in the top navigation bar.
- **Persistent Layout**: Custom sidebar width and collapsed/expanded state are automatically persisted in `localStorage` across reloads.
- **Google Translate Style In-Place Document Translation Overlay**:
  - **Top-Quarter Compact Scrollable Overlay**: Pinned to `max-height: 26%` at the top of the canvas, keeping ~75% of the scanned page unobstructed and visible, with an internal scrollable container (`overflow-y: auto`) to read full multi-paragraph translated documents.
  - **Full Page OCR & Document Content Translation**: Combines document metadata headers (Subject, From, To) with full-page OCR body extraction on canvas via local WebAssembly Tesseract.js (or digital text layer), translating the entire letter content into English without truncation.
  - **Enlarged Eye Icon Peek Scan**: Clean, enlarged Eye icon button (`18px × 18px`) without text labels; tap or click to toggle between English translation and original Arabic scan, with press-and-hold support on touchscreens.
  - **Natural Translation Engine**: Built-in comprehensive bilingual dictionary (500+ words, 150+ administrative phrases) translating legal contracts, eviction notices, utility bills, and correspondence into real, natural English words.
  - **Reversed Stream Detection**: Automatically identifies and un-reverses visual-order RTL text streams common in Middle Eastern PDF generators (e.g. `ةيلخادلا ةرازو` & `راجيإ دقع`).
  - **Spelling & Diacritic Normalization**: Normalizes diacritics/tashkeel, tatweel, and letter variations (`ة`/`ه`, `[إأآٱ]`/`ا`) with Unicode NFKC normalization supporting Arabic Presentation Forms (`\uFB50-\uFEFC`).
  - **100% Offline Client-Side OCR & WASM Static Assets**: Bundles local WebAssembly `Tesseract.js` v5 and fast LSTM Arabic/English trained models (`wwwroot/lib/tesseract/`) served natively with `.wasm`, `.gz`, and `.traineddata` MIME types, requiring zero cloud APIs and zero internet connectivity.
  - **Universal Support**: Works seamlessly on both indexed archive files and newly uploaded scans without prior AI processing or database entries.
  - User preference (`localStorage`) persists translation state seamlessly across documents and session reloads.
- **Document Merge & Page Editor Visual Canvas Zooming**:
  - Interactive card zoom scaling across Document Merge (`#merge-docs-modal`) and Edit & Split Pages (`#doc-page-editor-modal`) modals.
  - Header zoom buttons (`-`, `+`, and reset indicator) supporting 7 discrete scaling levels (`70%`, `85%`, `100%`, `120%`, `145%`, `175%`, `210%`).
  - Universal keyboard shortcuts: `Ctrl +` / `Ctrl =` (Zoom In), `Ctrl -` (Zoom Out), and `Ctrl 0` (Reset to 100%).
  - Mouse wheel zoom: `Ctrl + Scroll` (Wheel Up = Zoom In, Wheel Down = Zoom Out) with native browser zoom suppression (`e.preventDefault()`).
  - Dynamic 2-document flex canvas layout (`merge-flex-2doc`) maximizing card preview size (~430px) across wide displays with centered inline swap and reorder buttons.
  - Persistent zoom level preferences stored in `localStorage` across reloads and sessions.
- **Multi-Page Drag & Drop Reordering & Page Rotation (Edit Pages)**:
  - Drag single pages or multiple selected pages together as a cohesive group to any arbitrary target position in the document, completely bypassing tedious 1-step arrow buttons.
  - Real-time visual drop insertion indicators (`page-drop-before` / `page-drop-after`) and drag ghost styling.
  - 1-tap 90° clockwise rotation on individual page cards (`.btn-card-rotate`) and bulk "Rotate 90°" button in the sticky toolbar for all selected pages.
  - Instant client-side visual feedback via CSS rotation transforms combined with background persistence via `/api/documents/{vaultId}/rotate-pages` rewriting the physical PDF orientation.
  - Automatic cache-busting reload ensuring both the page editor grid and document viewer panel reflect the updated pages immediately.
- **Keyboard Shortcuts**:
  - `⌘B` / `Ctrl+B`: Toggle navigation sidebar collapse/expand.
  - `⌘K` / `Ctrl+K`: Open Global Spotlight Search.
  - `⌘I` / `Ctrl+I`: Open Ingest & Document Upload Station.
  - `Space`: Quick Look document preview inspector.
  - `Shift+D`: Toggle Dark / Light theme.
  - `Ctrl +` / `Ctrl -` / `Ctrl 0`: Zoom in, zoom out, or reset card size in Merge and Page Editor modals.
  - `?`: Open the interactive Keyboard Shortcuts guide modal.
  - `Esc`: Dismiss active modals, dropdowns, and previews.

## Testing

The project uses `vitest` for frontend unit/component tests, `pytest` for Python backend and Playwright E2E suites, and `dotnet test` for .NET tests:

```bash
# Frontend component tests
npx vitest run

# Backend and Playwright E2E tests
pytest

# .NET test suite
dotnet test
```
