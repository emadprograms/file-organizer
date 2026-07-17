<!-- generated-by: gsd-doc-writer -->
## ARCHITECTURE.md

### System Overview
The File Organizer Post-Processor is a Python-based, sequential batch processing system that takes raw classified PDF pages and their metadata (from a pre-existing JSON report) and organizes them into cohesive, logical documents grouped by resident and category. Its primary inputs are a `*_categorized.pdf` file and a `*_report.json` file. It outputs segmented PDFs organized in a structured file system hierarchy, along with a finalized, compressed PDF containing a Table of Contents. The system relies on a multi-pass pipeline architecture utilizing an LLM (Gemini) for intelligent document boundary detection and routing.

### Component Diagram

```mermaid
graph TD
    A[main.py (Entry Point)] --> B[pipeline (Orchestrator)]
    B --> C[timeline / phase: Cleaning Pass]
    B --> D[grouping: Grouping Pass]
    B --> E[routing: Routing Pass]
    B --> F[timeline / FileOrganizer: Generation Pass]
    
    C --> G[core: Models/Schemas]
    D --> G
    E --> G
    F --> G
    
    C --> H[llm: LLMClient]
    D --> H
    E --> H
    
    C --> I[tenant_config: YAML Loader]
    F --> J[pdf: PDF Utilities]
    
    D --> K[grouping/state: GroupingStateManager]
    E --> L[routing/state: RoutingStateManager]
```

### Data Flow
1. **Initialization:** The script `src/main.py` validates the target directory to ensure it contains exactly one `*_categorized.pdf` and one `*_report.json`.
2. **Cleaning Pass:** `pipeline._clean_documents` parses the input JSON into `PageData` objects. It infers missing dates through proximity matching, clusters raw tenant names fuzzily, optionally utilizes LLM for canonicalization, and builds tenant timelines using YAML configuration (if available).
3. **Grouping Pass:** `pipeline._group_documents` logically groups contiguous `PageData` items into `DocumentGroup` objects. It pre-splits the pages by category and canonical tenant, then chunks them and calls the LLM to identify distinct document boundaries. Checkpoint state is managed iteratively.
4. **Routing Pass:** `pipeline._route_documents` assigns each `DocumentGroup` to a specific destination folder path using LLM context evaluation. State checkpoints protect against pipeline failures.
5. **Generation Pass:** `FileOrganizer.organize` reads the categorized PDF, extracts page segments corresponding to each `DocumentGroup`, and writes them to their physical folder locations. It then builds a finalized PDF with a complete Table of Contents, compresses it via `src.pdf.compress_pdf`, and cleans up intermediate files.

### Key Abstractions
- `PageData` (`src/core/models.py`) - Represents the metadata and state of a single PDF page.
- `DocumentGroup` (`src/core/schemas.py`) - Represents a logically grouped sequence of pages that form a cohesive document.
- `TenantTimeline` (`src/core/models.py`) - Tracks the start and end dates of a resident's tenancy for date-based assignments.
- `Pipeline` (`src/pipeline/pipeline.py`) - Orchestrates the multipass execution (cleaning, grouping, routing).
- `LLMClient` (`src/llm/llm.py`) - A centralized wrapper for Gemini API interactions handling retries and rate limits.
- `FileOrganizer` (`src/timeline/core.py`) - Handles the physical translation of document groups into filesystem structures and PDF segments.
- `GroupingStateManager` (`src/grouping/state.py`) - Manages midway checkpoints during the grouping pass.
- `RoutingStateManager` (`src/routing/state.py`) - Manages midway checkpoints during the routing pass.

### Directory Structure Rationale
The application uses a modular, domain-driven directory structure under `src/`:
- `core/`: Contains fundamental domain models, schemas, global exceptions, and configuration.
- `grouping/`: Encapsulates logic for the grouping pass, including LLM prompts and state management.
- `llm/`: Centralizes the LLM API interactions.
- `pdf/`: Contains utility functions for physical PDF manipulation (extraction, TOC generation, compression).
- `pipeline/`: Orchestrates the high-level passes and sequence of the overall pipeline.
- `routing/`: Encapsulates logic for determining final directory paths for grouped documents.
- `tenant_config/`: Loads and parses optional tenant definitions from YAML.
- `timeline/`: Manages date-based tenant timelines, date inference, and physical file organization.
- `utils/`: Common utilities such as logging and safe file system operations.
