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

### Frontend Web UI & Interaction Architecture
The web client provides a unified interface across both Desktop PC and Tablet devices ("وضع الكمبيوتر" / "وضع التابلت"), implemented in vanilla JavaScript with Tailwind CSS styling:
- `src/api/static/js/doc-manager.js`: Handles document state, desktop HTML5 drag & drop (`dragstart`, `dragover`, `drop`, `dragend`), selection management (`selectedDocIds`), and document moves (single move PATCH or multi-document batch move `POST /api/areas/{area}/houses/{house}/documents/batch-move`).
- `src/api/static/js/categories-view.js`: Handles category grouping, folder cards, and tablet touch gestures (press-and-hold >=280ms touch drag-and-drop with floating avatar and dynamic target folder detection).
- **Multi-Select Drag & Drop Workflow**:
  1. **Selection**: Documents are selected via checkboxes (`toggleDocSelection`, tracking `selectedDocIds`).
  2. **Initiation**:
     - *Desktop (Computers)*: Dragging any selected document sets `isMulti = true`, populates `vault_ids`, and dims all selected cards (`opacity-40 ring-2 ring-blue-400`).
     - *Tablet (Tabs)*: Press-and-hold (>=280ms) on any selected document initiates touch dragging, creates a floating `#touch-drag-avatar` with a count badge pill (`.touch-drag-count-badge`), and dims all selected cards in DOM.
  3. **Target Drop**:
     - Dropping onto a category folder card triggers `POST /api/areas/{area}/houses/{house}/documents/batch-move` for multiple documents (or single PATCH for one document).
     - Dropping onto a sidebar tenant tree node reassigns all dragged documents to the target resident.
  4. **DOM Synchronization & Cleanup**:
     - Each document card is moved to its target category container via `moveDocInDom` and count badges update smoothly.
     - `deselectAllDocs()` clears selection checkboxes and state.
     - All dimming styles and touch avatars are cleaned up reliably in `finally` handlers.
- **Asset Mirroring**: Web assets are strictly mirrored across three locations: `src/api/static/js/`, `web-net/wwwroot/js/`, and `dist/win-x64/wwwroot/js/`.

### Dark Mode Design System & Tablet Responsive Architecture
The application features a dedicated, semantic dark mode design system engineered specifically for high-DPI displays (such as iPad Liquid Retina and OLED screens) and desktop environments:

1. **Multi-Tier Surface Elevation Hierarchy**:
   - **Level 0 (Canvas Base)**: `#080c14` (deep midnight navy-slate).
   - **Level 1 (Sidebars & Navbars)**: `#0b0f19` / `rgba(12, 16, 28, 0.88)` with `backdrop-filter: blur(12px)` and crisp border `#172033`.
   - **Level 2 (Cards & Panels)**: `#111827` surface with `#1e293b` borders and subtle rim lighting (`box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.04)`).
   - **Level 3 (Elevated Modals & Popovers)**: `#111827` surface with `1px solid rgba(255, 255, 255, 0.1)`, 3D drop shadow (`box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.85)`), and backdrop blur (`rgba(2, 6, 17, 0.8)` with `backdrop-filter: blur(8px)`).

2. **Harmonized Status Badges & Semantic Tenure Themes**:
   - Replaced naive pastel overrides with dark-tinted badge pills and vibrant indicators:
     - **Emerald (< 5y / Active / Success)**: Text `#34d399`, background `rgba(16, 185, 129, 0.1)`, border `rgba(16, 185, 129, 0.28)`.
     - **Amber (5–10y / Medium / Pinned / Sticky Notes)**: Text `#fbbf24`, background `rgba(245, 158, 11, 0.1)`, border `rgba(245, 158, 11, 0.28)`.
     - **Rose (> 10y / Long / Vacated / Danger)**: Text `#fb7185`, background `rgba(244, 63, 94, 0.1)`, border `rgba(244, 63, 94, 0.28)`.
     - **Purple (Applicants)**: Text `#c084fc`, background `rgba(168, 85, 247, 0.1)`, border `rgba(168, 85, 247, 0.28)`.
     - **Blue (Counts / Folders / Stats)**: Text `#60a5fa`, background `rgba(59, 130, 246, 0.12)`, border `rgba(59, 130, 246, 0.3)`.
     - **Slate (Neutral Dates / Counts)**: Text `#94a3b8`, background `#172033`, border `#27354f`.

3. **Segmented Tab Control & Interactive States**:
   - The segmented tabs track (`Folders` / `Timeline`) sits on a dark capsule base (`#0c101d`).
   - Active tab elevates with surface `#1e293b`, glowing blue label `#60a5fa`, and inset border lighting.
   - Hover states across buttons, list items, and cards use refined dark tints (`#17223b`, `rgba(59, 130, 246, 0.18)`), eliminating bright or pastel flashes on mouseover/touch.

4. **Database Inspector & PDF Canvas Optimization**:
   - Database tables use alternating zebra rows (`#111827` / `#0c111e`), refined cell borders (`#172033`), dark headers (`#0b0f19`), and soft blue hover rows.
   - The inline PDF canvas sits against an eye-friendly `#080c14` backdrop with softened dark bezel wrappers (`box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.7)`), preventing harsh glare during reading sessions.

5. **Tablet & Touchscreen Responsive Architecture (768px – 1024px)**:
   - Dedicated tablet media queries dynamically adapt top navbar action triggers so search and shortcut buttons scale fluidly without clipping.
   - Area overview cards automatically arrange in a balanced 2-column grid on tablets with enhanced card rim lighting.
   - Interactive elements feature subtle touch compression feedback (`transform: scale(0.985)`) and hardware-accelerated momentum scrolling (`overscroll-behavior-y: contain`).

