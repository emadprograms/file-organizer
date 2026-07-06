# File Organizer Post-Processor

A high-precision document processing pipeline designed to ingest pre-categorized housing PDFs and their corresponding JSON reports, resolve tenant identities, group pages into logical multi-page documents, and organize them into a structured directory hierarchy.

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

2. **Run the Post-Processor**:
   ```bash
   python src/organize.py path/to/house_directory
   ```

3. **View Results**: Processed PDFs will be organized into the directory hierarchy defined by the post-processing logic.

## Usage Examples

**Basic processing:**
```bash
python src/organize.py ./pdfs/1273
```

## Key Features

- **Tenant Resolution**: Automatically resolves tenant identities across multi-page documents using LLM intelligence.
- **Logical Grouping**: Groups disparate pages into coherent documents based on content and identity.
- **Structured Routing**: Organizes files into a precise hierarchy: House → Tenant → Topic Folder.
- **Automated PDF Segmentation**: Splits a single large PDF into smaller, topic-specific files named and grouped logically.

## License
No license specified.
