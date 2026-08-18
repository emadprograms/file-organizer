# File Organizer Codebase Structure

## Directory Structure Overview

```
file-organizer/
├── .planning/                  # Project roadmap, milestones, requirements, and audits
│   └── codebase/               # Architectural and codebase documentation
├── config.yaml                 # Core configuration (inbox path, areas root, area mappings)
├── config.sample.yaml          # Template configuration
├── requirements.txt            # Python dependencies (fitz, opencv, pydantic, rapidfuzz, pylnk3, etc.)
├── README.md                   # Project overview and CLI user guide
├── src/                        # Main source code
│   ├── __init__.py
│   ├── main.py                 # CLI entry point and top-level orchestrator
│   ├── categorization/         # Base and fine-grained document classification
│   │   ├── __init__.py
│   │   ├── categorization.py   # Vision-based OCR and field extraction
│   │   └── fine_categorization.py # CoT reasoning for 13 target categories
│   ├── core/                   # Shared foundational data models, configuration, and verification
│   │   ├── __init__.py
│   │   ├── categories.yaml     # Base classification rules and extraction schemas
│   │   ├── config.py           # AppConfig, API quota tracking, model constants
│   │   ├── exceptions.py       # Custom exception hierarchy
│   │   ├── indexing.py         # 0-based/1-based indexing and bounds checking
│   │   ├── models.py           # PageData, TenantTimeline domain models
│   │   ├── schemas.py          # Pydantic schemas (DocumentGroup, ParsedCommand, etc.)
│   │   ├── state.py            # State manager for unified state.json
│   │   ├── utils.py            # Arabic string cleaning, normalization, sanitization
│   │   └── verification.py     # Deep verification and integrity engine
│   ├── grouping/               # Multi-page boundary detection and name resolution
│   │   ├── __init__.py
│   │   ├── config.py           # Boundary detection prompts
│   │   ├── core.py             # Sliding-window grouping logic (process_with_shrink)
│   │   ├── name_matcher.py     # RapidFuzz name clustering and LLM canonicalization
│   │   ├── state.py            # Grouping midway state manager
│   │   └── utils.py            # Chunk merging and group validation
│   ├── inbox/                  # Space-separated filename parsing and inference
│   │   ├── __init__.py
│   │   ├── parser.py           # Syntax parser for inbox drop files
│   │   └── resolver.py         # House, tenant, and area resolution helpers
│   ├── llm/                    # LLM client, rate limiting, and provider abstraction
│   │   ├── __init__.py
│   │   ├── llm.py              # LLMClient orchestrator
│   │   ├── mock.py             # Mock LLM provider for unit testing
│   │   └── providers.py        # GeminiProvider and base LLMProvider
│   ├── migration/              # Architecture migration scripts
│   │   ├── __init__.py
│   │   └── v5_migration.py     # Migrates legacy v4 checkpoints to v5 vault structure
│   ├── pdf/                    # PDF manipulation, compression, and image preprocessing
│   │   ├── __init__.py
│   │   ├── compress.py         # Image downscaling and JPEG recompression
│   │   ├── extract.py          # Sub-PDF segment extraction via PyMuPDF
│   │   └── image_processing.py # Auto-deskew, levels, diacritic boost
│   ├── pipeline/               # Multi-pass pipeline execution and undo
│   │   ├── __init__.py
│   │   ├── pipeline.py         # Core Pipeline class
│   │   ├── runner.py           # Pass orchestration runners
│   │   ├── undo.py             # Pipeline reversal and PDF reconstruction
│   │   └── visualizer.py       # Rich terminal tree renderer for dry runs
│   ├── presentation/           # User interface and logging output helpers
│   │   ├── __init__.py
│   │   └── ui.py               # Rich console wrapper and verbosity manager
│   ├── reconcile/              # Bidirectional synchronization engine
│   │   ├── __init__.py
│   │   └── core.py             # Ghost adoption, deletions, renames, raw PDF ingest
│   ├── routing/                # Category-to-folder destination mapping
│   │   ├── __init__.py
│   │   ├── config.py           # 13 category definitions, prefixes, direct mappings
│   │   ├── router.py           # Deterministic and LLM-assisted routing
│   │   └── state.py            # Routing midway state manager
│   ├── tenant_config/          # Tenant YAML configuration loaders
│   │   ├── __init__.py
│   │   ├── tenants.py          # Tenant metadata utilities
│   │   └── yaml_loader.py      # <house_id>_tenants.yaml loader
│   ├── timeline/               # Organization, folder structure, and timeline view
│   │   ├── __init__.py
│   │   ├── core.py             # FileOrganizer class (extracts PDFs, creates shortcuts)
│   │   ├── dates.py            # Date extraction and sorting utilities
│   │   ├── page_integrity.py   # Page count assertion and manifest builder
│   │   ├── phase.py            # Cleaning phase and tenant assignment
│   │   └── timeline_builder.py # Chronological shortcut builder
│   ├── utils/                  # Cross-cutting filesystem, logging, and OS helpers
│   │   ├── __init__.py
│   │   ├── fs.py               # Atomic write, Windows shortcut wrapper (PowerShell)
│   │   ├── logger.py           # Plain-text & JSONL dual logging setup
│   │   └── windows_shortcut.ps1 # PowerShell script for WScript.Shell shortcut operations
│   └── watcher/                # Inbox filesystem polling and listener
│       ├── __init__.py
│       ├── lock.py             # File-based process lock mechanism
│       └── orchestrator.py     # FSUIOrchestrator for inbox proposal loop
└── tests/                      # Pytest suite covering all modules and end-to-end flows
```

---

## Key Modules & Component Responsibilities

### 1. Main & Entry Points

| File | Primary Functions / Classes | Responsibilities |
|---|---|---|
| [`src/main.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/main.py) | `main()`, `get_parser()`, `validate_environment()`, `validate_target_directory()`, `validate_report_json()`, `run_prepend_mode()` | Central CLI supporting `create`, `reconcile`, `verify`, `prepend`, `migrate`, and `undo` commands. Coordinates config loading, logging initialization, and pass orchestration. |

---

### 2. Core Domain & Verification (`src/core/`)

| File | Primary Functions / Classes | Responsibilities |
|---|---|---|
| [`src/core/models.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/core/models.py) | [`PageData`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/core/models.py#L7-L52), [`TenantTimeline`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/core/models.py#L54-L65) | Domain data models for individual page metadata (dates, canonical tenant, fine category, continuation flags) and tenant date spans. |
| [`src/core/schemas.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/core/schemas.py) | [`DocumentGroup`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/core/schemas.py#L33-L47), [`GroupEntry`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/core/schemas.py#L48-L57), [`GroupingResponse`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/core/schemas.py#L58-L64), [`ParsedCommand`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/core/schemas.py#L10-L32), [`CategorizationResult`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/core/schemas.py#L65-L79) | Pydantic validation schemas for LLM responses, boundary detection chunks, and FS-UI space-separated commands. |
| [`src/core/state.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/core/state.py) | [`State`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/core/state.py#L9-L58) | Encapsulates the unified `<house_id>_state.json` file. Provides atomic save and load methods with schema backward compatibility. |
| [`src/core/verification.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/core/verification.py) | [`run_verification()`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/core/verification.py#L35-L320), `VerificationError` | Deep integrity checker: asserts 0 orphan PDFs, 0 broken shortcuts, 0 rogue PDFs outside the vault, valid PDF byte streams, and strict immutable page count equality. |
| [`src/core/config.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/core/config.py) | [`AppConfig`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/core/config.py#L35-L80), `record_successful_call()` | Application configuration loaded from `config.yaml`, API quota logging in `.tracking/api_calls.log`. |
| [`src/core/indexing.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/core/indexing.py) | `to_0_based()`, `validate_bounds()` | Boundary enforcement and index conversions between 0-based and 1-based representations. |
| [`src/core/exceptions.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/core/exceptions.py) | `FileOrganizerError`, `ValidationError`, `ConfigurationError`, `PipelineHaltError`, `ProviderRotationExhaustedError` | Domain exception hierarchy used across all packages. |
| [`src/core/categories.yaml`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/core/categories.yaml) | YAML configuration | Definitions and extraction prompts for base categories: `forms`, `id_cards`, `pictures`, `letters`, `utility_bills`, `contract`, `others`. |

---

### 3. Pipeline & Orchestration (`src/pipeline/`)

| File | Primary Functions / Classes | Responsibilities |
|---|---|---|
| [`src/pipeline/runner.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/pipeline/runner.py) | `run_cleaning_pass()`, `run_fine_categorization_pass()`, `run_grouping_pass()`, `run_routing_pass()`, `run_generation_pass()` | Sequentially executes pipeline passes, manages state transitions, triggers PDF compression, and writes output manifests. |
| [`src/pipeline/pipeline.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/pipeline/pipeline.py) | [`Pipeline`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/pipeline/pipeline.py#L26-L227) | Orchestrator holding `LLMClient` and coordinating cleaning, run splitting, grouping chunks, and routing resumption. |
| [`src/pipeline/undo.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/pipeline/undo.py) | [`run_undo()`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/pipeline/undo.py#L9-L120) | Reconstructs the original consolidated PDF from vault document segments in page order, preserves YAML/raw dump artifacts, and cleans user-facing directories. |
| [`src/pipeline/visualizer.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/pipeline/visualizer.py) | `Visualizer` | Renders colorized tree and table views of proposed document placements during dry runs. |

---

### 4. Categorization (`src/categorization/`)

| File | Primary Functions / Classes | Responsibilities |
|---|---|---|
| [`src/categorization/categorization.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/categorization/categorization.py) | `process_unclassified_pdf()` | Converts PDF pages into images, uploads them to GenAI File API, performs two-step LLM extraction (classification + field extraction), and produces `.raw_dump.json`. |
| [`src/categorization/fine_categorization.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/categorization/fine_categorization.py) | `process_fine_categorization()`, `FineCategorizationResponse` | Executes second-pass fine-grained classification mapping pages to specific numbered destination folders (01 to 13) with chain-of-thought rationale. |

---

### 5. Grouping & Boundary Detection (`src/grouping/`)

| File | Primary Functions / Classes | Responsibilities |
|---|---|---|
| [`src/grouping/core.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/grouping/core.py) | `process_with_shrink()`, `_process_chunk()` | Segments page runs using LLM boundary prompts. Shrinks and expands sliding window chunks while maintaining state checkpoints. |
| [`src/grouping/name_matcher.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/grouping/name_matcher.py) | `normalize_arabic_text()`, `cluster_names_fuzzily()`, `canonicalize_with_llm()` | Normalizes Arabic text variants, performs fuzzy name clustering via RapidFuzz, and resolves family dependents to heads of household using LLM. |
| [`src/grouping/state.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/grouping/state.py) | `GroupingStateManager`, `GroupingState` | Checkpoints grouping progress to disk for pause/resume safety. |
| [`src/grouping/config.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/grouping/config.py) | `MAINTENANCE_PROMPT`, `STRICT_ADMIN_PROMPT`, `OTHER_PROMPT` | Specialized prompt templates for different document types. |

---

### 6. Routing (`src/routing/`)

| File | Primary Functions / Classes | Responsibilities |
|---|---|---|
| [`src/routing/router.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/routing/router.py) | `route_document()`, `double_check_others()`, `RoutingResponse` | Assigns document groups to folder names. Employs direct routing maps for deterministic categories and a two-phase confirmation step for miscellaneous categories. |
| [`src/routing/config.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/routing/config.py) | `FOLDER_ROUTING`, `FOLDER_PREFIXES`, `DIRECT_ROUTING_MAP`, `FORM_FOLDERS`, `LETTER_FOLDERS` | Standard 13-folder schema with 2-digit numeric prefixes and category mappings. |
| [`src/routing/state.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/routing/state.py) | `RoutingStateManager`, `RoutingState` | Tracks per-document routing decisions and hashes grouping checksums to detect pipeline invalidations. |

---

### 7. Timeline & Organization (`src/timeline/`)

| File | Primary Functions / Classes | Responsibilities |
|---|---|---|
| [`src/timeline/core.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/timeline/core.py) | [`FileOrganizer`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/timeline/core.py#L19-L431) | Calculates tenant folder spans with LRM date protection, ensures directory hierarchies, slices PDFs into the vault, and creates `.lnk` shortcuts in categories and `[Timeline View]`. |
| [`src/timeline/phase.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/timeline/phase.py) | `process_cleaning_phase()`, `assign_pages_to_tenants()` | Associates raw extracted pages with validated tenant timelines. |
| [`src/timeline/page_integrity.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/timeline/page_integrity.py) | `run_reconciliation()` | Generates per-page manifests in `state.json`, shifts indices during prepend operations, and verifies zero unaccounted pages. |
| [`src/timeline/dates.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/timeline/dates.py) | Date helper utilities | Extracts and parses standardized Gregorian date representations. |

---

### 8. Bidirectional Reconciler (`src/reconcile/`)

| File | Primary Functions / Classes | Responsibilities |
|---|---|---|
| [`src/reconcile/core.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/reconcile/core.py) | `run_reconcile_mode()` | Permanent synchronization engine. Ingests raw PDFs dropped into category folders, adopts ghost shortcuts, updates renamed/moved shortcuts, cleans orphaned vault files, and triggers auto-verification. |

---

### 9. Inbox & FS-UI Watcher (`src/inbox/`, `src/watcher/`)

| File | Primary Functions / Classes | Responsibilities |
|---|---|---|
| [`src/inbox/parser.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/inbox/parser.py) | `parse_filename_syntax()` | Tokenizes space-separated filenames (`[AREA] [HOUSE] [TENANT] [GROUP] [DATE] [TITLE]`). |
| [`src/inbox/resolver.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/inbox/resolver.py) | `infer_missing_data()`, `resolve_area()`, `resolve_tenant()` | Resolves `U` placeholders via majority voting over page extraction dumps and resolves target house folders in the filesystem. |
| [`src/watcher/orchestrator.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/watcher/orchestrator.py) | `FSUIOrchestrator` | Long-running inbox listener managing the file proposal loop (`_Proposed` $\rightarrow$ `OK` $\rightarrow$ final prepend ingestion). |
| [`src/watcher/lock.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/watcher/lock.py) | `acquire_lock()`, `release_lock()` | File-based mutex locking to prevent multiple listener instances on the same inbox path. |

---

### 10. PDF, LLM & Utilities (`src/pdf/`, `src/llm/`, `src/utils/`)

| File | Primary Functions / Classes | Responsibilities |
|---|---|---|
| [`src/pdf/image_processing.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/pdf/image_processing.py) | `process_pdf()`, `extract_and_clean_page()`, `auto_deskew()`, `adjust_levels()` | Renders 300 DPI page images with OpenCV-based deskewing, level balancing, and diacritic contrast boost. |
| [`src/pdf/compress.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/pdf/compress.py) | `compress_pdf()` | Downscales embedded PDF images exceeding $1500\text{px}$ dimension and recompresses to JPEG via PyMuPDF. |
| [`src/pdf/extract.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/pdf/extract.py) | `extract_pdf_segment()` | Slices inclusive page ranges from a source PDF and outputs compressed segments. |
| [`src/llm/llm.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/llm/llm.py) | `LLMClient` | Primary LLM wrapper managing rate limits, backoff cooldowns, File API uploads, and structured Pydantic decoding. |
| [`src/llm/providers.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/llm/providers.py) | `GeminiProvider`, `LLMProvider` | Provider interface and Google GenAI implementation. |
| [`src/utils/fs.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/utils/fs.py) | `atomic_write()`, `create_shortcut()`, `read_shortcut_target()`, `batch_create_shortcuts()`, `batch_read_shortcut_targets()`, `merge_and_remove_dir()` | Context manager for atomic file writes and high-performance batch Windows shortcut manipulation via PowerShell. |
| [`src/utils/logger.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/utils/logger.py) | `setup_logging()`, `LogContext`, `JSONLFormatter`, `log_decision_trace()` | Sets up isolated root loggers with simultaneous plain-text (`app.log`) and structured JSONL (`debug.log`) outputs in timestamped directories. |
| [`src/utils/windows_shortcut.ps1`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/utils/windows_shortcut.ps1) | PowerShell script | Interacts with Windows COM `WScript.Shell` for creating and resolving `.lnk` files in single and batch modes. |

---

## Data Schemas and State Representations

### 1. `state.json` Schema Structure
The file `<house_id>_state.json` is located in `.source_files/`:

```json
{
  "house_id": "703",
  "cleaned_pages": [
    {
      "category": "contract",
      "content_explanation": "عقد إيجار مسكن...",
      "expected_tenant_name": "خالد عبود هزاع",
      "expected_house_number": "703",
      "date": "1998-05-12",
      "canonical_tenant": "خالد عبود هزاع",
      "resolved_date": "1998-05-12",
      "original_index": 0,
      "user_locked": false,
      "fine_category": "05-عقود",
      "fine_category_reason": "Contains contractual terms...",
      "is_continuation": false
    }
  ],
  "grouped_documents": [
    {
      "start_page": 0,
      "end_page": 1,
      "primary_tenant": "خالد عبود هزاع",
      "category": "contract",
      "dates": ["1998-05-12", "1998-05-12"],
      "reason": "عقد إيجار رسمي مكون من صفحتين",
      "brief_arabic_title": "عقد إيجار",
      "folder_path": "عقود",
      "is_direct_routed": true,
      "vault_id": "9b1deb4d3b7d4bad9bdd2b0d7b3dcb6d",
      "shortcuts": [
        "خالد عبود هزاع ‎(1998 - 2012)‎/05_عقود/1998-05-12 - عقد إيجار.lnk"
      ],
      "user_locked": false
    }
  ],
  "routed_documents": [ ... ],
  "manifest": {
    "summary": {
      "house_id": "703",
      "total_input_pages": 42,
      "total_output_pages": 42,
      "output_file_count": 28,
      "unaccounted_pages": []
    },
    "per_page": [
      {
        "page_index": 0,
        "tenant": "خالد عبود هزاع",
        "date": "1998-05-12",
        "output_file": "703 - خالد عبود هزاع/خالد عبود هزاع ‎(1998 - 2012)‎/05_عقود/1998-05-12 - عقد إيجار.lnk",
        "page_in_output": 1,
        "target_folder": "خالد عبود هزاع ‎(1998 - 2012)‎/05_عقود",
        "vault_id": "9b1deb4d3b7d4bad9bdd2b0d7b3dcb6d"
      }
    ]
  }
}
```

---

## Standard 13-Folder Routing Hierarchy

| Prefix | Folder Name (Arabic) | Target Document Types | Direct Routing Source |
|---|---|---|---|
| `01` | `01_بيانات أساسية` | Official housing application forms, questionnaires, clearance certificates | Form evaluation |
| `02` | `02_بيانات شخصية` | National IDs (CPR), Passports, Driving Licenses, Marriage Certificates | `id_cards` |
| `03` | `03_أمر تخصيص` | Official housing allocation and ministerial transfer orders | Letter evaluation |
| `04` | `04_محضر تسليم مفتاح` | Official key handover forms and records | Form evaluation |
| `05` | `05_عقود` | Lease and tenancy agreements, formal binding contracts | `contract` |
| `06` | `06_كهرباء وماء` | EWA municipal utility bills, meter transfer correspondence | `utility_bills` |
| `07` | `07_استقطاع إيجار` | Salary deduction letters mentioning specific monetary amounts | Letter evaluation |
| `08` | `08_وقف استقطاع بدل` | Letters stopping housing allowance deductions | Letter evaluation |
| `09` | `09_إشعارات` | Administrative notices, warnings, and eviction notices | Letter evaluation |
| `10` | `10_صيانة` | Maintenance requests, inspection sheets, repair approvals | Letter / Form evaluation |
| `11` | `11_صور ومعاينات` | On-site photo inspections and visual reports | `pictures` |
| `12` | `12_تعديلات` | Physical house modification requests (garage, room extensions) | Letter / Form evaluation |
| `13` | `13_رسائل متنوعة` | Miscellaneous correspondence, multi-person rosters | Fallback / General Letters |
