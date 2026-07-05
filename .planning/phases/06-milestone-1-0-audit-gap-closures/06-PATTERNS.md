# Phase 06: Milestone 1.0 Audit Gap Closures - Pattern Map

**Mapped:** 2026-07-05
**Files analyzed:** 5
**Analogs found:** 5 / 5

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/processing/pipeline.py` | service | data-transform | `src/processing/pipeline.py` | exact |
| `src/processing/organizer.py` | service | file-I/O | `src/processing/organizer.py` | exact |
| `src/processing/routing.py` | utility | data-transform | `src/processing/routing.py` | exact |
| `src/processing/grouping.py` | config | N/A | `src/processing/grouping.py` | exact |
| `src/organize.py` | controller | file-I/O | `src/fs_utils.py` | role-match |

## Pattern Assignments

### `src/processing/pipeline.py` (service, data-transform)

**Analog:** `src/processing/pipeline.py`

**Core Pattern (Anchor Categories)** (line 298):
```python
        # Existing logic to be updated
        ANCHOR_CATEGORIES = {"Basic Details Form", "Housing Contract", "Rent Deduction Notice"}
```

---

### `src/processing/organizer.py` (service, file-I/O)

**Analog:** `src/processing/organizer.py`

**Core Pattern (Directory Creation)** (line 101):
```python
                os.makedirs(target_dir, exist_ok=True)
```

**Core Pattern (Unassigned Naming)** (lines 67, 73):
```python
                    tenant_folder_names[tenant] = f"غير محدد {min_year}-{max_year}"
# ...
                    tenant_folder_names[tenant] = "غير محدد"
```

**Core Pattern (Reconciliation Output)** (lines 150-164):
```python
def run_reconciliation(summary: dict, per_page: list, total_input_pages: int, house_id: str, output_dir: Path, dry_run: bool = False):
    """Write reconciliation manifest and assert page counts."""
```
*(Needs to integrate `rich.table.Table` before throwing the `RuntimeError`)*

---

### `src/processing/routing.py` (utility, data-transform)

**Analog:** `src/processing/routing.py`

**Core Pattern (Consecutive Failure Tracking)** (lines 37-60):
```python
def route_document(group: DocumentGroup, llm_client: Any) -> tuple[str, bool]:
    """Route a document group to the appropriate folder.
    ...
    category = group.category
    
    if category in SINGLE_MATCH:
        folder = CATEGORY_TO_FOLDERS[category][0]
        return folder, True
```
*(Needs module-level `consecutive_routing_failures` state management injected into `route_document`)*

---

### `src/processing/grouping.py` (config, N/A)

**Analog:** `src/processing/grouping.py`

**Core Pattern (Prompt Rules)** (lines 8-16):
```python
GROUPING_PROMPT = """You are an expert Arabic document analyst.
Your task is to identify logical multi-page document boundaries within a chunk of pages.

CRITICAL RULES:
1. Boundaries ONLY on subject/content shift. DO NOT split on date changes or sender changes.
2. Every page MUST be part of exactly one group. No gaps, no overlaps.
3. The first group must start at the first page of the chunk.
4. The last group must end at the last page of the chunk.
```
*(Needs explicit grouping reason rule added as Rule 5)*

---

### `src/organize.py` (controller, file-I/O)

**Analog:** `src/fs_utils.py`

**File Write Pattern (Atomic)** (`src/fs_utils.py` lines 31-40):
```python
@contextmanager
def atomic_write(filepath: str):
    """
    Yields a temporary file path, and atomically renames it to filepath
    upon successful completion.
    """
    tmp_filepath = filepath + f".{uuid.uuid4().hex}.tmp"
    try:
        yield tmp_filepath
        os.replace(tmp_filepath, filepath)
```
*(Apply this block in `src/organize.py` around lines 121 and 150, and `organizer.py` line 171)*

## Shared Patterns

### Atomic Writes
**Source:** `src/fs_utils.py`
**Apply to:** All manifest and checkpoint writes (`src/organize.py` and `src/processing/organizer.py`)

## Metadata

**Analog search scope:** `src/` and `src/processing/`
**Files scanned:** 5
**Pattern extraction date:** 2026-07-05
