# Architecture

**Focus:** arch
**Date:** 2026-07-01

## System Pattern & Layers
The system follows a pipeline processing architecture (a linear sequence of data transformations):

1. **Ingestion Layer (`src/ingest.py`)**: Responsible for reading the input PDF and extracting pages as images.
2. **Extraction Layer (`src/extractors.py`, `src/llm.py`)**: Uses local/heuristic methods alongside LLM (Google GenAI) to classify pages and extract structured metadata (categories, residents, dates).
3. **Orchestration Layer (`src/pipeline.py`)**: Coordinates the multi-pass logic:
   - *Pass 1*: Page-by-page vision extraction.
   - *Pass 1.5*: Global interpolation (date holes) and semantic name clustering.
   - *Pass 2*: Timeline-based logical grouping of pages.
4. **Organization Layer (`src/organizer.py`)**: Takes logical document groups, splits the original PDF (`src/split.py`), and writes them into a structured output directory hierarchy.

## Data Flow
1. **Input**: A single, potentially large PDF document.
2. **Images**: Extracted page by page and passed to Vision Extractors.
3. **Classifications**: Raw page metadata is stored (temporarily cached in `SimpleCache` using JSON).
4. **Cleaned Classifications**: Dates are interpolated, and aliases are mapped across all pages.
5. **Document Groups**: Continuous sequences of pages are merged into `DocumentGroup` objects based on Category and Primary Tenant constraints.
6. **Output PDFs**: Sliced from the original PDF and saved to `./output/{HouseNumber}/{ResidentName}/`.

## Abstractions
- `PageClassification`: Data schema representing a single page's metadata (category, date, residents).
- `DocumentGroup`: Data schema representing a contiguous sequence of pages logically belonging together.
- `LLMClient`: Wrapper around LLM APIs to isolate the core logic from specific provider implementations.
