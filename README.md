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
- **Keyboard Shortcuts**:
  - `⌘B` / `Ctrl+B`: Toggle navigation sidebar collapse/expand.
  - `⌘K` / `Ctrl+K`: Open Global Spotlight Search.
  - `⌘I` / `Ctrl+I`: Open Ingest & Document Upload Station.
  - `Space`: Quick Look document preview inspector.
  - `Shift+D`: Toggle Dark / Light theme.
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
