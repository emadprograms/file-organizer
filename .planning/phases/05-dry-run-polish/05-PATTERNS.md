# Phase 5: Dry Run & Polish - Patterns

This document maps the architectural patterns for the Dry Run & Polish phase. It guides the implementation of the `--dry-run` flag to preview pipeline output without modifying the filesystem.

## 1. CLI & Pipeline Entry (`src/organize.py`)

**Role**: CLI interface and overall process orchestration.
**Data Flow**: Parse `--dry-run`, conditionally skip writing checkpoints (but load them if they exist), and use `rich` for output visualization.

**Analog**: Existing flag parsing in `get_parser()`.

**Pattern Excerpts**:

```python
# In src/organize.py -> get_parser()
def get_parser():
    parser = argparse.ArgumentParser(description="File Organizer Post-Processor")
    # ... existing args ...
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the pipeline output without writing physical files or PDFs."
    )
    return parser
```

```python
# In src/organize.py -> main()
# Pattern for conditional checkpoint saving:
if not args.dry_run:
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump([p.model_dump() for p in cleaned_pages], f, ensure_ascii=False, indent=2)
else:
    logger.info("DRY RUN: Skipping save for cleaned.json")
```

```python
# In src/organize.py -> main() 
# Visualization Pattern (using rich):
from rich.console import Console
from rich.tree import Tree
from rich.table import Table

if args.dry_run:
    console = Console()
    
    # Summary Table
    table = Table(title="Dry Run: Processing Summary")
    table.add_column("File Name")
    table.add_column("Pages")
    table.add_column("Topic")
    # ... populate table from per_page or documents ...
    console.print(table)
    
    # Tree Output
    tree = Tree(f"[bold blue]{house_id}[/bold blue]")
    # ... populate tree with tenant and folder structure ...
    console.print(tree)
```

## 2. File Organizer (`src/processing/organizer.py`)

**Role**: Simulates directory and file logic without actually performing IO.
**Data Flow**: Accept `dry_run` as an argument. Keep path resolution and string mapping intact so `organize()` returns valid target files. Skip `os.makedirs` and `extract_pdf_segment`.

**Analog**: Conditional execution patterns.

**Pattern Excerpts**:

```python
# In src/processing/organizer.py -> FileOrganizer.organize()
def organize(self, documents: list[DocumentGroup], source_pdf: str, house_id: str, output_base_dir: Path, config: Any = None, dry_run: bool = False) -> list[dict]:
    # ...
    for doc in documents:
        # ... logic calculating target_dir and filename ...
        
        if not dry_run:
            os.makedirs(target_dir, exist_ok=True)
            
        # ...
        if not dry_run:
            extract_pdf_segment(str(source_pdf), doc.start_page, doc.end_page, str(target_path))
            logger.info(f"  → {filename} (pages {doc.start_page}-{doc.end_page})")
        else:
            logger.info(f"  [DRY RUN] → Would extract {filename} (pages {doc.start_page}-{doc.end_page}) to {target_dir}")
```

```python
# In src/processing/organizer.py -> run_reconciliation()
def run_reconciliation(summary: dict, per_page: list, total_input_pages: int, house_id: str, output_dir: Path, dry_run: bool = False):
    # ... manifest building ...
    if not dry_run:
        manifest_path = output_dir / f"{house_id}_manifest.json"
        tmp_path = manifest_path.with_suffix('.tmp')
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        tmp_path.replace(manifest_path)
    else:
        logger.info("[DRY RUN] Skipping reconciliation manifest write.")
```

## 3. End-to-End Tests (`tests/test_e2e.py`)

**Role**: Verifies that the complete pipeline respects the `--dry-run` flag.
**Data Flow**: Executes the pipeline and validates filesystem state (no writes) and terminal output.

**Pattern Excerpts**:

```python
import subprocess
import shutil
import os
from pathlib import Path

def test_dry_run_end_to_end(tmp_path):
    # Setup test fixture mimic-ing validation conditions
    target_dir = tmp_path / "1273"
    target_dir.mkdir()
    
    # (Mock copying sample files here...)
    # pdf_src = Path("pdfs/1273_categorized.pdf")
    # shutil.copy(pdf_src, target_dir / "1273_categorized.pdf")
    
    # Execute CLI
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf8"
    result = subprocess.run(
        ["python", "-m", "src.organize", str(target_dir), "--dry-run"],
        env=env,
        capture_output=True,
        text=True
    )
    
    # Assert successful execution
    assert result.returncode == 0
    
    # Assert no output was generated
    output_dir = target_dir / "output"
    assert not output_dir.exists() or len(list(output_dir.iterdir())) == 0
    
    # Assert tree/table visualization strings are in output
    assert "Dry Run:" in result.stdout
```
