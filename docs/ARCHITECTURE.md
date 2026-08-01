<!-- generated-by: gsd-doc-writer -->
## ARCHITECTURE.md

### System Overview (v5.3)
The File Organizer Post-Processor is a Python-based, sequential batch processing system that takes raw classified PDF pages and their metadata and organizes them into cohesive, logical documents grouped by resident and category. 

In version 5.3, the system introduces a **Vault Architecture**. Physical segmented PDFs are now stored immutably in a hidden `.source_files/vault/` directory. Categorized folders and the `[Timeline View]` contain lightweight Windows `.lnk` shortcuts pointing directly to these vaulted PDFs. 

A unified `state.json` serves as the single source of truth for the entire system, replacing multiple intermediate checkpoint files. A strict Verification engine and a robust Bidirectional Reconciler ensure that the JSON state, the physical vault, and the user-facing shortcuts remain 100% mathematically synchronized, auto-adopting ghost files and pruning orphans.

### Component Diagram

```mermaid
graph TD
    A[main.py (CLI Entry Point)] --> B[pipeline (Orchestrator)]
    B --> C[timeline / phase: Cleaning Pass]
    B --> D[grouping: Grouping Pass]
    B --> E[routing: Routing Pass]
    B --> F[timeline / FileOrganizer: Generation Pass (Vault & Shortcuts)]
    
    A --> R[reconcile: Reconciler Engine]
    A --> V[core / verification: State Verifier]
    
    C --> G[core: Models/Schemas/State]
    D --> G
    E --> G
    F --> G
    R --> G
    V --> G
    
    C --> H[llm: LLMClient]
    D --> H
    E --> H
    
    C --> I[tenant_config: YAML Loader]
    F --> J[pdf: PDF Utilities]
```

### Data Flow
1. **Initialization:** The CLI `src/main.py create` validates the target directory to ensure it contains exactly one `*_categorized.pdf` and one `*_report.json`.
2. **Cleaning Pass:** Parses the input JSON into `PageData` objects. It infers missing dates through proximity matching, clusters raw tenant names fuzzily, optionally utilizes LLM for canonicalization, and builds tenant timelines using YAML configuration (if available).
3. **Grouping Pass:** Logically groups contiguous `PageData` items into `DocumentGroup` objects. It pre-splits the pages by category and canonical tenant, then chunks them and calls the LLM to identify distinct document boundaries. Checkpoint state is managed iteratively in `state.json`.
4. **Routing Pass:** Assigns each `DocumentGroup` to a specific destination folder path using LLM context evaluation. State checkpoints protect against pipeline failures.
5. **Generation Pass:** `FileOrganizer.organize` extracts page segments and writes them directly into `.source_files/vault/`. It then creates `.lnk` shortcuts in their respective physical category folders and the `[Timeline View]` folder.
6. **Reconciliation & Verification:** Commands in the CLI allow running the `reconcile` engine to detect shortcut moves by the user and update `state.json` accordingly, and the `verify` engine to assert absolute structural parity.

### Key Abstractions
- `PageData` (`src/core/models.py`) - Represents the metadata and state of a single PDF page.
- `DocumentGroup` (`src/core/schemas.py`) - Represents a logically grouped sequence of pages that form a cohesive document.
- `State` (`src/core/state.py`) - The unified single-source-of-truth object that backs `state.json`.
- `Reconciler` (`src/reconcile/core.py`) - The bidirectional engine keeping shortcuts, the vault, and `state.json` in sync.
- `Verifier` (`src/core/verification.py`) - Mathematical assertions that the system state is sound.
- `Pipeline` (`src/pipeline/pipeline.py`) - Orchestrates the multipass execution (cleaning, grouping, routing).
- `LLMClient` (`src/llm/llm.py`) - A centralized wrapper for Gemini API interactions handling retries and rate limits.
- `FileOrganizer` (`src/timeline/core.py`) - Handles the physical translation of document groups into the vault and creates `.lnk` shortcuts.

### Directory Structure Rationale
The application uses a modular, domain-driven directory structure under `src/`:
- `core/`: Contains fundamental domain models, state management (`state.json`), strict verification logic, global exceptions, and configuration.
- `grouping/`: Encapsulates logic for the grouping pass, including LLM prompts.
- `reconcile/`: Holds the bidirectional synchronization engine to keep state matching the physical shortcuts on disk.
- `llm/`: Centralizes the LLM API interactions.
- `pdf/`: Contains utility functions for physical PDF manipulation (extraction, compression).
- `pipeline/`: Orchestrates the high-level passes and sequence of the overall pipeline.
- `routing/`: Encapsulates logic for determining final directory paths for grouped documents.
- `tenant_config/`: Loads and parses optional tenant definitions from YAML.
- `timeline/`: Manages date-based tenant timelines, date inference, vault saving, and shortcut linking.
- `utils/`: Common utilities such as logging and safe file system operations.
