<!-- generated-by: gsd-doc-writer -->
# File Organizer

File Organizer is a post-processor utility that organizes categorized PDFs into structured house folders by using LLMs to clean, group, and route documents. It takes a categorized PDF and its corresponding report JSON, processes the pages, and generates a finalized, structured PDF with a Table of Contents.

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd file-organizer
```

2. Set up a Python virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
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

2. Run the main processing script against a target directory containing a `*_categorized.pdf` and a `*_report.json`:
```bash
python src/main.py /path/to/target_directory
```

## Usage Examples

**Previewing Output (Dry Run)**
You can preview the pipeline output without making any physical file changes or writing PDFs:
```bash
python src/main.py /path/to/target_directory --dry-run
```

**Using a Specific LLM Model**
By default, the script uses `gemma-4-31b-it`. You can specify another model using the `--model` flag:
```bash
python src/main.py /path/to/target_directory --model gemini-2.5-flash
```

**Running with Verbose Logging**
For detailed logs and debugging information, use the `--verbose` flag:
```bash
python src/main.py /path/to/target_directory --verbose
```

**Batch Processing with Rotating API Keys**
If you have multiple folders and need to rotate through multiple API keys to avoid rate limits, you can configure the target directory in `rotate_process.py` and run:
```bash
python rotate_process.py
```

## Testing

The project uses `pytest` for its test suite. To run all tests, simply execute:
```bash
pytest
```
