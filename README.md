<!-- generated-by: gsd-doc-writer -->
# File Categorizer

A high-precision, configuration-driven document processing pipeline designed to ingest large PDF files, classify individual pages using LLMs, and organize them into a structured directory hierarchy according to user-defined rules. 

Originally built for housing records, the tool has been generalized so users can define their own document categories, AI extraction prompts, grouping strategies, and routing rules via a YAML/JSON configuration file.

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

2. **Define Your Rules**: Create a configuration file (e.g., `config.yaml`) detailing your categories and extraction logic. (See `sample-config.yaml` for a housing-related example).

3. **Run the Categorizer**:
   ```bash
   python src/main.py path/to/your/document.pdf -c config.yaml
   ```

4. **View Results**: Processed PDFs will be organized in the default `./output` directory or your specified output path.

## Usage Examples

**Basic processing with a custom config:**
```bash
python src/main.py input_docs.pdf -c my-config.yaml
```

**Processing with a custom output path:**
```bash
python src/main.py input_docs.pdf -c my-config.yaml -o ./categorized_files
```

## Key Features

- **Configuration-Driven**: Define your own document categories, extraction instructions, and destination routing in a simple YAML/JSON file without altering the core pipeline.
- **Multi-Pass Classification**: Uses a vision-first approach to identify document categories and extract key metadata using LLMs.
- **Customizable Routing**: Output documents to dynamic folder paths specified in your config (e.g., `{primary_tenant}/{category}`).
- **Automated PDF Segmentation**: Splits a single large PDF into smaller, category-specific files named and grouped logically.

## License
No license specified.
