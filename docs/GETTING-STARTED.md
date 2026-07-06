<!-- generated-by: gsd-doc-writer -->
# Getting Started

## Prerequisites
- **Python**: >= 3.10
- **Environment**: A valid `.env` file containing a `GEMINI_API_KEY`.
- **Input**: A directory containing pre-categorized PDFs and their corresponding JSON reports.

## Installation Steps
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/emadprograms/file-organizer.git
   cd file-organizer
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
The fastest way to see the project in action is to run the organizer script on a house directory:

```bash
python src/organize.py path/to/house_directory
```

The processed documents will be organized in the directory hierarchy defined by the post-processing logic.

## Common Setup Issues
- **Missing API Key**: If you see a `FATAL ERROR: Missing required API keys`, ensure your `.env` file is in the project root and contains `GEMINI_API_KEY=your_key`.
- **PDF Read Errors**: Ensure the PDF is not password protected and is accessible at the provided path.
- **API Rate Limits**: If the process slows down or fails, check your Gemini API quota. The system logs remaining quota in the console on startup.
- **Catastrophic LLM Failure**: If the pipeline aborts with a `LLMFailureError`, it means the LLM providers are experiencing persistent 500 errors. The system aborts automatically after 5 consecutive global failures to prevent generating degraded or 'Unassigned' output.


## Next Steps
- To understand the internal logic, see [ARCHITECTURE.md](ARCHITECTURE.md).
- To contribute or modify the code, see [DEVELOPMENT.md](DEVELOPMENT.md).
- To run the test suite, see [TESTING.md](TESTING.md).
