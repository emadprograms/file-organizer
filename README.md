<!-- generated-by: gsd-doc-writer -->
# File Categorizer

A high-precision document processing pipeline designed to ingest large housing-related PDF files, classify individual pages using LLMs, and organize them into a structured, resident-centric directory hierarchy.

## Installation

This project requires Python 3.10+. Install the dependencies using pip:

```bash
pip install -r requirements.txt
```

## Quick Start

1. **Configure Environment**: Create a `.env` file in the root directory and add your API key:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

2. **Run the Categorizer**:
   ```bash
   python src/main.py path/to/your/document.pdf
   ```

3. **View Results**: Processed PDFs will be organized in the `./output` directory by house number and resident.

## Usage Examples

**Basic processing with default output directory:**
```bash
python src/main.py input_housing_docs.pdf
```

**Processing with a custom output path:**
```bash
python src/main.py input_housing_docs.pdf -o ./my_categorized_files
```

## Key Features

- **Multi-Pass Classification**: Uses a vision-first approach to identify document categories, residents, and dates.
- **Date Intelligence**: Automatically detects date outliers and interpolates missing dates to maintain chronological integrity.
- **Semantic Resident Mapping**: Clusters name variations (aliases) using LLMs to ensure all documents for a single resident are grouped together.
- **Timeline-Based Grouping**: Implements "Tenant Walls" to separate consecutive residents based on residency timelines.
- **Automated PDF Segmentation**: Splits a single large PDF into smaller, category-specific files named by date and type.

## License
No license specified.
