<!-- generated-by: gsd-doc-writer -->
# Getting Started

This guide will help you set up the File Organizer project on your local machine and run it for the first time.

## Prerequisites

Before you begin, ensure you have the following installed on your system:
- Python >= 3.8
- `git`
- Windows OS (Required for `.lnk` shortcut creation)

## Installation Steps

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd file-organizer
   ```

2. **Set up a Python virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## First Run

1. **Set up your environment variables:**
   Copy the example environment file and open it in your preferred editor.
   ```bash
   cp .env.example .env
   ```
   Add your `GEMINI_API_KEY` (and any other optional keys) to the newly created `.env` file.

2. **Run the processor:**
   The main script (`src/main.py`) processes a directory containing categorized PDF and JSON reports. Point the CLI's `create` command to a valid directory:
   ```bash
   python src/main.py create /path/to/target_directory
   ```
   *(Note: You can also use the `--dry-run` flag to preview changes without modifying any files).*

## After Processing

Once the `create` command completes:
- All physical PDF segments are stored safely in `.source_files/vault/`.
- A unified single-source-of-truth is saved at `.source_files/state.json`.
- Your category folders and the `[Timeline View]` folder will be populated with lightweight `.lnk` shortcuts pointing to the vault.

If you manually move shortcuts around between tenant folders, you can run the reconciler to sync those changes back to `state.json`:
```bash
python src/main.py reconcile --tenants
```

## Common Setup Issues

- **Missing `GEMINI_API_KEY`**
  If you forget to configure your environment variables, the application will fail immediately with a `ConfigurationError: GEMINI_API_KEY is missing from the environment.` Ensure you have copied `.env.example` to `.env` and populated the key.
- **Missing or Multiple Source Files**
  The provided target directory must contain exactly one `*_categorized*.pdf` file and exactly one `*_report*.json` file. If the files are missing or if multiple matching files exist, the script will abort with a `ValidationError`.

## Next Steps

Now that you have the application running, you may want to check out:
- [Configuration Guide](CONFIGURATION.md) - Learn about all available environment variables and model settings.
- [Architecture Overview](ARCHITECTURE.md) - Understand how the data flows through the LLM pipeline phases and the Vault architecture.
