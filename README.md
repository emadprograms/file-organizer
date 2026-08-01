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

## Testing

The project uses `pytest` for its test suite. To run all tests, simply execute:
```bash
pytest
```
