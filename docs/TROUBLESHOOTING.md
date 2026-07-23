<!-- generated-by: gsd-doc-writer -->
# Troubleshooting Guide

This guide covers common errors, diagnostic procedures, and resolution steps for `file-organizer`.

## Common Runtime Errors

### 1. `ConfigurationError: GEMINI_API_KEY is missing from the environment`
- **Cause**: The application failed to detect `GEMINI_API_KEY` in environment variables or `.env`.
- **Solution**: 
  1. Ensure `.env` exists in the repository root (`cp .env.example .env`).
  2. Populate `GEMINI_API_KEY=your_actual_key`.
  3. Verify that host shell environment variables are not overriding `.env` with empty values.

### 2. `ValidationError: No *_categorized.pdf found` or `No *_report.json found`
- **Cause**: Target directory does not contain required paired input files (`*_categorized*.pdf` and `*_report*.json`).
- **Solution**:
  1. Verify target directory path passed to `src/main.py`.
  2. Ensure source PDF is named with prefix matching report JSON (e.g. `house123_categorized.pdf` and `house123_report.json`).

### 3. `ModuleNotFoundError: No module named 'cv2'` or missing C++ runtime libraries
- **Cause**: Dependencies are not installed in active environment, or global Python is being invoked instead of virtualenv.
- **Solution**:
  1. Activate virtual environment: `.\venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/macOS).
  2. Run `pip install -r requirements.txt`.
  3. Execute pytest via virtualenv explicitly: `.\venv\Scripts\pytest`.

### 4. API Rate Limit Exceeded (`429 Too Many Requests`)
- **Cause**: Gemini API key rate limits reached during large document batch processing.
- **Solution**:
  1. Use key rotation wrapper `rotate_process.py` with multiple keys populated in `.env`.
  2. Retry processing after backoff interval; state checkpointing (`GroupingStateManager`, `RoutingStateManager`) saves mid-run progress automatically.

---

## Diagnostic Checklists

### Verbose Logging Output
To inspect exact internal execution steps, prompt outputs, and state transitions, run:
```bash
python src/main.py /path/to/target_directory --verbose
```
Log files are written to `.tracking/` or system log paths and displayed on standard console output.

### Dry Run Simulation
To verify directory structure and TOC generation without writing PDFs to disk:
```bash
python src/main.py /path/to/target_directory --dry-run
```
