# Phase 24: FS-UI Orchestration - Pattern Map

**Mapped:** 2026-07-20
**Files analyzed:** 5
**Analogs found:** 3 / 5

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/main.py` | controller | request-response | `src/main.py` | exact |
| `src/fs_ui/orchestrator.py` | controller | event-driven | `src/pipeline/pipeline.py` | partial |
| `src/fs_ui/lock.py` | utility | file-I/O | none | no-analog |
| `src/fs_ui/__init__.py` | config | - | none | no-analog |
| `tests/test_fs_ui_orchestrator.py` | test | - | `tests/test_core_config_parsing.py` | exact |

## Pattern Assignments

### `src/main.py` (controller, request-response)

**Analog:** `src/main.py` (existing file)

**Controller loop pattern** (lines 98-135 of `src/main.py`):
```python
        with lock:
            logger.info("Listener started...")
            inbox_dir = Path(config.inbox_path)
            while True:
                for pdf_path in inbox_dir.glob("*.pdf"):
                    # Process files...
                time.sleep(2)
```

### `src/fs_ui/orchestrator.py` (controller, event-driven)

**Analog:** `src/pipeline/pipeline.py`

**Class encapsulation pattern** (lines 26-42 of `src/pipeline/pipeline.py`):
```python
class Pipeline:
    """Orchestrator for the document processing workflow."""
    
    def __init__(self, api_key: str, delay_between_pages: float = 1.0, routing_model: str | None = None) -> None:
        """Initialize the pipeline with necessary clients and extractors.
        
        Args:
            api_key (str): The primary API key for the LLM.
            ...
```

### `tests/test_fs_ui_orchestrator.py` (test, -)

**Analog:** `tests/test_core_config_parsing.py`

**Test structure pattern** (lines 12-18 of `test_core_config_parsing.py`):
```python
def test_record_successful_call_creates_dir_and_file(tmp_path, monkeypatch) -> None:
    """
    Test record successful call creates dir and file.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
```

## Shared Patterns

### Stateless Filesystem Loop
**Source:** `24-RESEARCH.md`
**Apply to:** `src/fs_ui/orchestrator.py`
```python
def process_inbox(self):
    for filepath in self.inbox_path.glob("*.pdf"):
        name = filepath.stem
        if name.endswith(" OK"):
            self.finalize(filepath)
        elif name.endswith("_Proposed") or name.endswith("_Failed") or name.endswith("_Error"):
            continue # Waiting for user
        else:
            self.propose(filepath)
```

## No Analog Found

Files with no close match in the codebase (planner should use RESEARCH.md patterns instead):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `src/fs_ui/lock.py` | utility | file-I/O | No explicit PID lockfile utilities exist yet. Will implement `os.kill(pid, 0)` based on POSIX patterns in RESEARCH.md. |
| `src/fs_ui/__init__.py` | config | - | Standard python package init. |

## Metadata

**Analog search scope:** `src/`, `tests/`
**Files scanned:** 72
**Pattern extraction date:** 2026-07-20
