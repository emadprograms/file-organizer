<!-- generated-by: gsd-doc-writer -->
# Getting Started

## Prerequisites
- **Python**: >= 3.10
- **Environment**: A valid `.env` file containing a `GEMINI_API_KEY`.
- **Configuration**: A configuration file (e.g. `config.yaml`) detailing your categories and routing rules.
- **Input**: A PDF file containing documents.

## Installation Steps
1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd File-Categorizer
   ```
2. **Set Up Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## First Run
The fastest way to see the project in action is to run the main script with a sample PDF and a sample config:

```bash
python src/main.py samples/sample_docs.pdf -c sample-config.yaml
```

The processed documents will be organized in the `./output` directory, following the hierarchy defined in `sample-config.yaml`.

## Common Setup Issues
- **Missing API Key**: If you see a `FATAL ERROR: Missing required API keys`, ensure your `.env` file is in the project root and contains `GEMINI_API_KEY=your_key`.
- **Missing Config File**: The app requires a configuration file (`-c`). Ensure the file exists and is valid YAML/JSON.
- **PDF Read Errors**: Ensure the PDF is not password protected and is accessible at the provided path.
- **API Rate Limits**: If the process slows down or fails, check your Gemini API quota. The system logs remaining quota in the console on startup.

## Next Steps
- To understand the internal logic, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).
- To contribute or modify the code, see [DEVELOPMENT.md](docs/DEVELOPMENT.md).
- To run the test suite, see [TESTING.md](docs/TESTING.md).
