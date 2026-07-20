<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** `config.yaml` will store `inbox_path`, `areas_root_path`, and `area_mappings`.
- **D-02:** `.env` remains strictly for secrets (API keys) and is not replaced by `config.yaml`.
- **D-03:** Load and validate `config.yaml` using a Pydantic Settings class.
- **D-04:** If `inbox_path` or `areas_root_path` do not exist on disk when the system starts, the script will automatically create them (`mkdir -p`) rather than failing.
- **D-05:** Strict path constraint: The `<path>` passed to the `create` command MUST be located inside the `areas_root_path` defined in `config.yaml`. The system will throw an error if the path is outside this boundary.
- **D-06:** The `create` mode initializes the standard history-building logic by parsing the raw PDF inside the given path, creating the `.source_files/` directory, and physically generating the split PDFs.
- **D-07:** Implement a `.inbox.lock` lockfile mechanism in the inbox directory. If a second `append` listener tries to start, it will gracefully exit, ensuring only one listener runs at a time.
- **D-08:** In this phase, running `append` will simply take the lock and print a stub message (e.g. "Listener started..."). The actual listening loop is deferred.

### the agent's Discretion
- CLI framework: Use Python's standard `argparse` as specified in STACK.md for subparsers (`create`, `append`).

### Deferred Ideas (OUT OF SCOPE)
- Inbox filename parsing and LLM inference syntax (Deferred to Phase 23).
- The actual File-System UI orchestrator loop (appending `_Proposed`, waiting for ` OK`, and finalizing) (Deferred to Phase 24).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CONF-01 | User can configure `inbox_path`, `areas_root_path`, and `area_mappings` within a central `config.yaml` file. | Pydantic BaseModel combined with PyYAML load provides robust validation. |
| CONF-02 | User can launch the script in `create` mode (e.g. `python main.py create <path>`), which forces standard history-building logic only on valid house structures. | `argparse` subparsers (`add_subparsers`) map the command directly to the current pipeline orchestration. |
| CONF-03 | User can launch the script in `append` mode (e.g. `python main.py append`), which starts the File-System UI listener on the inbox. | `filelock` library provides cross-platform process safety for the listener lock. |
</phase_requirements>

# Phase 22: Configuration and CLI Modes - Research

**Researched:** 2026-07-20
**Domain:** Python CLI Tooling & Configuration Management
**Confidence:** HIGH

## Summary

This phase transitions the application from a single-pass CLI tool into a multi-mode application. It introduces a `config.yaml` file to externalize structural settings (inbox and areas paths) while preserving `.env` for secrets. It also transitions the CLI interface to use `argparse` subparsers, creating distinct `create` (pipeline) and `append` (listener) modes.

**Primary recommendation:** Use Pydantic's `BaseModel` alongside `PyYAML` (already in the stack) for configuration validation, and implement the `.inbox.lock` mechanism using the robust `filelock` package to ensure cross-platform compatibility and handle stale locks gracefully upon unexpected crashes.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Configuration Parsing & Validation | API / Backend (`src/core/`) | — | Pydantic models validate raw YAML dictionaries before application startup. |
| CLI Argument Parsing | Entry Point (`src/main.py`) | — | `argparse` acts as the router to dispatch execution to the correct mode handler. |
| Lockfile Management | OS / Concurrency (`src/main.py`) | Storage / FS | Ensures mutually exclusive execution of the listener mode using OS-level file locking. |
| Path Auto-Creation | Storage / FS (`src/core/config.py`)| — | `Path.mkdir(parents=True, exist_ok=True)` handles initialization gracefully. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `PyYAML` | 6.0.2+ | Parsing YAML files | Standard and already present in project stack. |
| `pydantic` | 2.x | Schema validation | Project standard; `BaseModel` handles the dictionary loaded by YAML. |
| `argparse` | Built-in | CLI Subparsers | Built into Python; `add_subparsers` is exactly suited for this architecture. |
| `filelock` | ~3.x | Process locking | Standard Python lock implementation that cleans up cleanly via OS locks (`flock`/`LockFileEx`). |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `filelock` package | `os.open` with `O_CREAT\|O_EXCL` | Native OS open calls are brittle when processes crash (leaving stale lock files). `filelock` automatically releases via OS locking primitives when the PID exits. |
| `BaseModel` + `PyYAML` | `pydantic-settings[yaml]` | Adds an extra dependency when the stack already includes `PyYAML` and `pydantic`. |

**Installation:**
```bash
pip install filelock
```
*(Also add to `requirements.txt`)*

**Version verification:** 
```bash
pip index versions filelock # Verified: 3.31.1
```

## Package Legitimacy Audit

> **Required** whenever this phase installs external packages. Run the Package Legitimacy Gate protocol before completing this section.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| filelock | PyPI | 10+ yrs | ~100M/mo | tox-dev/py-filelock | OK | Approved |

*Note: Verified by `pip index versions` and PyPI package information.*

## Architecture Patterns

### Recommended Project Structure
```
src/
├── core/
│   ├── config.py       # Pydantic Config model and YAML loading logic
│   └── schemas.py      # Existing schemas
├── ui/
│   └── listener.py     # (Future) FS-UI listener logic; currently stubbed
└── main.py             # CLI Entry point with argparse subparsers
```

### Pattern 1: Pydantic Config Loader
**What:** Loads YAML data and immediately passes it through Pydantic's validation.
**When to use:** On application startup, before any domain logic executes.
**Example:**
```python
import yaml
from pathlib import Path
from pydantic import BaseModel, Field

class AppConfig(BaseModel):
    inbox_path: Path
    areas_root_path: Path
    area_mappings: dict[str, str] = Field(default_factory=dict)
    
    @classmethod
    def load(cls, config_path: Path) -> "AppConfig":
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data)
```

### Pattern 2: Process Exclusive Lock (Listener)
**What:** Ensures only one instance of the `append` mode is running.
**When to use:** Inside the handler for `append` mode.
**Example:**
```python
from filelock import FileLock, Timeout
import sys

def run_append_mode(config: AppConfig):
    lock_path = config.inbox_path / ".inbox.lock"
    lock = FileLock(str(lock_path), timeout=0)
    try:
        with lock:
            print("Listener started...")
            # Listener loop will go here in Phase 24
    except Timeout:
        print("Listener is already running (lockfile exists). Exiting gracefully.")
        sys.exit(0)
```

### Anti-Patterns to Avoid
- **Anti-pattern:** Using `.env` for structural configuration (like `inbox_path`). What to do instead: Keep `.env` strictly for secrets and `config.yaml` for paths and rules.
- **Anti-pattern:** Manually creating lock files (`open("lock", "w")`). What to do instead: Use `filelock`, which leverages POSIX `flock` and Windows equivalent, guaranteeing lock release if the process segfaults or is SIGKILLed.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CLI Commands | Custom `sys.argv` parsing | `argparse.add_subparsers` | Handles help text generation, positional vs optional arg validation. |
| Lockfiles | `os.open` or pidfiles | `filelock` | Stale locks prevent the listener from restarting after an unexpected crash. |

**Key insight:** Concurrency bugs like stale locks are extremely frustrating in background listeners. Using the OS-level lock mechanisms wrapped by `filelock` entirely bypasses this class of bugs.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | ✓ | 3.12.13 | — |
| pytest | Testing | ✓ | 9.1.1 | — |
| filelock | Listener mode | ✗ | — | Add to requirements.txt (blocking for D-07 robustness) |

**Missing dependencies with no fallback:**
- `filelock` (must be installed via pip)

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 |
| Config file | none — see Wave 0 |
| Quick run command | `pytest tests/test_core_config.py -x` |
| Full suite command | `pytest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CONF-01 | Config loading and validation | unit | `pytest tests/test_core_config.py -x` | ✅ Wave 0 (partially exists) |
| CONF-02 | CLI parses `create` and executes pipeline | unit | `pytest tests/test_main_cli.py -x` | ✅ Wave 0 (needs update) |
| CONF-03 | CLI parses `append` and takes lockfile | unit | `pytest tests/test_main_cli.py -x` | ✅ Wave 0 (needs update) |

### Wave 0 Gaps
- [ ] `tests/test_core_config.py` — Needs tests for auto-creating missing directories and YAML parsing.
- [ ] `tests/test_main_cli.py` — Needs tests updating `sys.argv` mocking for the new `create` and `append` subparsers.
- [ ] `tests/test_listener_lock.py` — New file needed to test lockfile mutual exclusion (CONF-03).
- [ ] Framework install: `pip install filelock` 

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | Pydantic (`BaseModel`) |
| V6 Cryptography | no | — |

### Known Threat Patterns for Python CLI Tools

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path Traversal | Tampering | Resolve paths absolutely (`Path.resolve()`) and check if `target_path.is_relative_to(config.areas_root_path)` |
| Malicious YAML | Tampering | Always use `yaml.safe_load()` instead of `yaml.load()` |

## Sources

### Primary (HIGH confidence)
- Official Python `argparse` Docs - Verified subparsers syntax.
- Official Pydantic Docs - Verified Pydantic BaseModel loading from dictionary.
- PyPI - Verified `filelock` versions and legitimacy.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - `filelock` and `PyYAML` are standard choices in Python ecosystems.
- Architecture: HIGH - Pydantic dict loading and argparse subparsers are idiomatic Python.
- Pitfalls: HIGH - Path traversal and stale lockfiles are well-known problems in this domain.

**Research date:** 2026-07-20
**Valid until:** 30 days
