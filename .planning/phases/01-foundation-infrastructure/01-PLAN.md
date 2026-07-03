---
wave: 1
depends_on: []
files_modified:
  - "src/fs_utils.py"
  - "tests/test_fs_utils.py"
  - "src/logger.py"
  - "tests/test_logger.py"
autonomous: true
---

# Phase 01: Foundation & Infrastructure (Wave 1 - Utilities & Logging)

## Goal
Build the shared filesystem utilities and logging infrastructure that the File Organizer CLI will rely on.

## Requirements Covered
- LOG-01: Timestamped logs directory at project root `./logs/[YYYY-MM-DD_HHMMSS]/`
- LOG-02: Full audit trail (support text + JSONL format)
- LOG-03: All log file handlers use `encoding='utf-8'` for Arabic text
- FS-01: Sanitize Arabic filenames (strip Windows-reserved and invisible Unicode chars)
- FS-02: Truncate filenames to 200 characters
- FS-03: Unicode normalize all filenames with `NFC`
- FS-04: Atomic file writes via `.tmp` rename

## Artifacts this phase produces
- `src/fs_utils.py` (file)
- `src/fs_utils.py:sanitize_filename` (function)
- `src/fs_utils.py:atomic_write` (context manager)
- `src/logger.py` (file)
- `src/logger.py:setup_logging` (function)
- `src/logger.py:log_llm_api_call` (function)
- `tests/test_fs_utils.py` (file)
- `tests/test_logger.py` (file)

<threat_model>
ASVS Level: 1
Block On: high
Threats:
- T-01: Path traversal via un-sanitized filenames
  Mitigation: `sanitize_filename` strictly removes Windows-reserved characters and path separators.
- T-02: Denial of service via excessive filename lengths leading to `MAX_PATH` errors.
  Mitigation: `FS-02` enforces truncation to 200 characters.
</threat_model>

## Tasks

<task id="01-01" read_first="src/fs_utils.py">
  <action>Create `src/fs_utils.py` and implement `sanitize_filename(filename: str) -> str`. It must apply Unicode `NFC` normalization, strip Windows reserved characters (`<`, `>`, `:`, `"`, `/`, `\`, `|`, `?`, `*`), strip invisible Unicode control characters, and truncate the result to 200 characters.</action>
  <acceptance_criteria>
    - `pytest tests/test_fs_utils.py` passes
    - `sanitize_filename` correctly normalizes text, strips reserved chars, and truncates to 200 chars.
  </acceptance_criteria>
</task>

<task id="01-02" read_first="src/fs_utils.py">
  <action>Add an `atomic_write(filepath: str)` context manager to `src/fs_utils.py` that yields a temporary file path (`filepath + ".tmp"` in the same directory) and atomically renames it to `filepath` upon successful completion (D-02).</action>
  <acceptance_criteria>
    - `pytest tests/test_fs_utils.py` passes
    - Context manager ensures file is written to `.tmp` and renamed, or removed on failure.
  </acceptance_criteria>
</task>

<task id="01-03" read_first="src/logger.py">
  <action>Create `src/logger.py` and implement `setup_logging(run_id: str = None)`. This should provision a timestamped directory `./logs/[YYYY-MM-DD_HHMMSS]_[PID or random]/` (append a unique identifier to prevent collisions in the same second, or use `run_id` if provided), and configure standard logging with `FileHandler` and `StreamHandler` (both using UTF-8). Create `log_llm_api_call(request: dict, response: dict, run_id: str)` to append to a `llm_audit.jsonl` file in the same log directory (D-01).</action>
  <acceptance_criteria>
    - `pytest tests/test_logger.py` passes
    - Timestamped log folder is created with UTF-8 encoding and includes a uniqueness suffix to prevent collisions.
    - JSONL audit trail function writes valid JSON lines.
  </acceptance_criteria>
</task>

## Verification
<verify>
  `pytest tests/test_fs_utils.py tests/test_logger.py` passes successfully.
</verify>

## Must Haves
must_haves:
  truths:
    - Filesystem operations correctly normalize and sanitize strings.
    - Logs properly capture Arabic characters using UTF-8.
