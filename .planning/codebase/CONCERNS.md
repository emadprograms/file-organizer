# Codebase Concerns & Technical Debt
**Date**: 2026-07-07

This document outlines technical debt, known issues, security concerns, and performance bottlenecks identified in the codebase.

## 1. Technical Debt & Architecture

### 1.1 God Module (`src/cleaning.py`)
- **Issue**: `src/cleaning.py` violates the Single Responsibility Principle. It currently acts as a catch-all for disparate logic including date conversion (`_hijri_to_gregorian`), JSON parsing, Arabic text normalization, fuzzy matching (`cluster_names_fuzzily`), and complex LLM canonicalization.
- **Impact**: Makes the module very large (23.6 KB), difficult to unit test in isolation, and hard to maintain.
- **Recommendation**: Split into specialized modules (e.g., `src/core/dates.py`, `src/core/text.py`, `src/processing/canonicalization.py`).

### 1.2 In-Process Dependency Management (`src/processing/split.py`)
- **Issue**: If `PIL` fails to import, the code shells out to dynamically install it: `subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])`.
- **Impact**: Severe anti-pattern. This pollutes user/system environments, can fail in restricted environments (e.g., CI/CD, Docker without root), and causes unpredictable delays. `Pillow` is missing from `requirements.txt`.
- **Recommendation**: Remove the runtime `pip install`, add `Pillow` to `requirements.txt`, and let standard dependency management handle it.

### 1.3 Hardcoded Rate Limiting & Cooldowns (`src/llm/llm.py`)
- **Issue**: The LLM fallback logic uses pessimistic hardcoded sleep times (`time.sleep(65)` for 429s, and `time.sleep(7.0 - elapsed)` for standard calls). It ignores standard exponential backoff strategies despite `tenacity` being present in `requirements.txt`.
- **Impact**: Suboptimal performance. The forced 7-second wait between standard calls throttles pipeline throughput unnecessarily. 
- **Recommendation**: Refactor to use `tenacity` for backoff, and rely on HTTP 429 Retry-After headers when available.

### 1.4 Test/Mock Logic in Production Code (`src/llm/llm.py`)
- **Issue**: The `--skip-llm` flag triggers hardcoded string-matching and JSON-mocking logic directly inside the production `_route_llm_call` method (using brittle Regex to extract chunk ranges).
- **Impact**: Clutters production routing logic and makes the LLM client fragile if prompt schemas change.
- **Recommendation**: Implement a `MockLLMProvider` that conforms to the `LLMProvider` protocol instead of polluting the core client.

### 1.5 Deep `sys.exit()` Calls (`src/main.py`)
- **Issue**: Utility functions like `validate_environment` and `validate_target_directory` call `sys.exit(1)` directly on failure.
- **Impact**: Prevents these functions from being reused or properly tested without patching `sys.exit`. 
- **Recommendation**: Raise custom exceptions (e.g., `ConfigurationError`, `ValidationError`) and catch them in `main()` to exit gracefully.

## 2. Bugs & Fragility

### 2.1 Swallowed Exceptions
- **Issue**: There are instances of `except Exception:` and bare `except:` catching errors without logging or raising them.
  - `src/processing/split.py` (Line 131): Bare `except:` in cleanup logic.
  - `src/logger.py` and `src/llm/llm.py`: Multiple `except Exception:` blocks with simple `pass` or `log.debug`.
- **Impact**: Silent failures make production debugging extremely difficult.
- **Recommendation**: Catch specific exceptions and log failures at the `ERROR` or `WARNING` level.

### 2.2 Resource Leaks
- **Issue**: `fitz.open()` is used heavily (e.g., in `src/processing/split.py`), but the `doc.close()` calls are not guaranteed to run if an exception occurs mid-processing.
- **Impact**: File handles may leak, which can crash long-running batch jobs on Windows.
- **Recommendation**: Use `fitz.open()` as a context manager (`with fitz.open(...) as doc:`).

### 2.3 Implicit Circular Dependencies
- **Issue**: `src/llm/llm.py` dynamically imports `from src.logger import LOGS_DIR` deep inside a method rather than injecting the dependency or configuring it centrally.
- **Impact**: Causes hidden coupling and can break if initialization orders change.

## 3. Security Concerns

### 3.1 PII Logging
- **Issue**: In `verbose` mode, `src/llm/llm.py` logs full prompts and LLM responses to `debug.log`. 
- **Impact**: These prompts contain raw OCR data, names, and potentially sensitive tenant information, leading to PII leakage in log files.
- **Recommendation**: Sanitize logs or ensure strict access controls and retention policies for `debug.log`.

### 3.2 Dynamic Execution
- **Issue**: The runtime execution of `pip install` via `subprocess` introduces a minor execution risk if the environment is somehow poisoned.

## 4. Performance

### 4.1 In-Memory Image Processing
- **Issue**: Image compression in `compress_pdf` extracts bytes, resizes them via Pillow, and saves them back to a PDF. It writes intermediate PDFs to disk and does a size comparison, copying the original if the size increased.
- **Impact**: High disk I/O overhead per page.
- **Recommendation**: Perform compression checks entirely in-memory before replacing the image stream in the PyMuPDF document to avoid unnecessary disk writes.

---
*Note: This document is meant to guide future refactoring phases and sprint planning.*
