# Phase 22: Configuration and CLI Modes - Pattern Map

**Mapped:** 2026-07-20
**Files analyzed:** 7
**Analogs found:** 4 / 7

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `config.yaml` | config | file-I/O | `src/core/categories.yaml` | role-match |
| `src/core/config.py` | config | file-I/O | `src/tenant_config/yaml_loader.py` | exact |
| `src/ui/listener.py` | service | event-driven | none | no-analog |
| `src/main.py` | controller | request-response | `src/main.py` | exact |
| `tests/test_core_config.py` | test | - | `tests/test_tenant_config_yaml_loader.py` | exact |
| `tests/test_main_cli.py` | test | - | `tests/test_main_cli.py` | exact |
| `tests/test_listener_lock.py` | test | - | none | no-analog |

## Pattern Assignments

### `src/core/config.py` (config, file-I/O)

**Analog:** `src/tenant_config/yaml_loader.py` and `src/core/schemas.py`

**Imports pattern** (lines 1-8 of `yaml_loader.py`, 5-6 of `schemas.py`):
```python
import yaml
from pathlib import Path
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(f"file_organizer.{__name__}")
from src.core.exceptions import ConfigurationError
```

**Core loading pattern** (lines 32-36 of `yaml_loader.py`):
```python
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or []
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Malformed YAML in {yaml_path}: {e}") from e
```

**Pydantic BaseModel pattern** (lines 10-20 of `schemas.py`):
```python
class DocumentGroup(BaseModel):
    """A group of consecutive pages belonging to the same document segment."""
    start_page: int
    end_page: int
    primary_tenant: str
    category: str
    dates: list[str]
    reason: str | None = None
    brief_arabic_title: str | None = None
    folder_path: str | None = None
    is_direct_routed: bool = False
```

---

### `src/main.py` (controller, request-response)

**Analog:** `src/main.py` (existing file)

**CLI Parser pattern** (lines 80-101 of `src/main.py`):
```python
def get_parser() -> argparse.ArgumentParser:
    """Create and configure the command-line argument parser.
    
    Returns:
        argparse.ArgumentParser: The configured parser object.
    """
    parser = argparse.ArgumentParser(description="File Organizer Post-Processor")
    parser.add_argument("target_dir", type=Path, help="Path to the target directory containing the categorized PDF and report JSON")
    parser.add_argument(
        "--model", 
        type=str, 
        default="gemma-4-31b-it", 
        choices=["gemma-4-31b-it", "gemma-4-26b-a4b-it", "gemini-2.5-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite"],
        help="LLM model to use for the main tasks"
    )
```

**Error Handling pattern** (lines 468-473 of `src/main.py`):
```python
    except FileOrganizerError as e:
        logger.exception(f"File Organizer failed: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1
```

---

### `tests/test_core_config.py` (test, -)

**Analog:** `tests/test_tenant_config_yaml_loader.py`

**Testing loading success** (lines 9-30 of `test_tenant_config_yaml_loader.py`):
```python
def test_load_tenant_config_success(tmp_path: Path) -> None:
    """
    Test load tenant config success.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    target_dir = tmp_path / "pdfs" / "123"
    source_files_dir = target_dir / ".source_files"
    source_files_dir.mkdir(parents=True, exist_ok=True)
    yaml_file = source_files_dir / "123_tenants.yaml"
    
    config_data = [
        {"name": "Tenant A", "start_date": "2023-01-01", "end_date": "2023-12-31"},
        {"name": "Tenant B", "start_date": "2024-01-01", "end_date": "present"}
    ]
    with open(yaml_file, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)
        
    tenants = load_tenant_config(target_dir, "123")
    assert tenants == config_data
```

**Testing missing/malformed** (lines 49-67 of `test_tenant_config_yaml_loader.py`):
```python
def test_load_tenant_config_malformed_yaml(tmp_path: Path) -> None:
    """
    Test load tenant config malformed yaml.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    target_dir = tmp_path / "pdfs" / "123"
    source_files_dir = target_dir / ".source_files"
    source_files_dir.mkdir(parents=True, exist_ok=True)
    yaml_file = source_files_dir / "123_tenants.yaml"
    
    # Write invalid yaml
    with open(yaml_file, "w", encoding="utf-8") as f:
        f.write("[unclosed list\n")
        
    with pytest.raises(ConfigurationError, match="Malformed YAML"):
        load_tenant_config(target_dir, "123")
```

---

### `tests/test_main_cli.py` (test, -)

**Analog:** `tests/test_main_cli.py` (existing file)

**CLI Parser Tests** (lines 14-25 of `test_main_cli.py`):
```python
def test_parser_default_model() -> None:
    """
    Test parser default model.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    parser = get_parser()
    args = parser.parse_args(["./pdfs/1273"])
    assert args.target_dir == Path("./pdfs/1273")
    assert args.model == "gemma-4-31b-it"
```

## Shared Patterns

### YAML Loading and Error Handling
**Source:** `src/tenant_config/yaml_loader.py`
**Apply to:** `src/core/config.py`
```python
import yaml
from src.core.exceptions import ConfigurationError

try:
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
except yaml.YAMLError as e:
    raise ConfigurationError(f"Malformed YAML: {e}") from e
```

## No Analog Found

Files with no close match in the codebase (planner should use RESEARCH.md patterns instead):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `config.yaml` | config | file-I/O | Simple YAML configuration file. |
| `src/ui/listener.py` | service | event-driven | No event-driven services or lockfile management exist yet. Use `filelock` pattern from RESEARCH.md. |
| `tests/test_listener_lock.py` | test | - | No file locking tests exist yet. |

## Metadata

**Analog search scope:** `src/`, `tests/`
**Files scanned:** 72
**Pattern extraction date:** 2026-07-20
