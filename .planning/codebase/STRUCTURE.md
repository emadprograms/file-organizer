# Codebase Directory Structure

**Date:** 2026-07-07

## Overview
The `file-organizer` codebase is organized around a core `src/` directory containing the main Python application, alongside standard development directories for tests, virtual environments, and planning artifacts.

## Directory Layout

```text
file-organizer/
├── .agents/                 # AI agent configurations and skills
├── .planning/               # Project management, AI architecture artifacts, and plans
│   └── codebase/            # Codebase mapping and architectural documentation
├── src/                     # Main source code directory
│   ├── core/                # Core utilities, configuration, and schemas
│   │   ├── config.py        # Environment variables and global settings
│   │   ├── indexing.py      # Utilities for PDF page indexing
│   │   ├── schemas.py       # Pydantic schemas (DocumentGroup, GroupEntry, etc.)
│   │   └── utils.py         # Miscellaneous utilities
│   ├── llm/                 # Large Language Model integrations
│   │   ├── llm.py           # LLMClient handling retries and structured output
│   │   └── providers.py     # Provider-specific implementations (e.g., Gemini)
│   ├── processing/          # The Pass 2 processing pipeline
│   │   ├── grouping.py      # LLM-based logical document boundary detection
│   │   ├── organizer.py     # End-to-end PDF organization and reconciliation
│   │   ├── pipeline.py      # Pipeline orchestrator
│   │   ├── routing.py       # LLM and rule-based folder routing
│   │   ├── split.py         # PDF splitting logic via PyMuPDF
│   │   └── visualizer.py    # Dry-run output visualization
│   ├── cleaning.py          # Pass 1: Date normalization and tenant clustering
│   ├── fs_utils.py          # File system utilities (atomic writes, etc.)
│   ├── logger.py            # Custom logging setup (rich console formatting)
│   └── main.py          # CLI entry point
├── tests/                   # Test suite for unit and integration testing
├── logs/                    # Execution logs
├── pdfs/                    # Output or sample PDF directory
├── .env                     # Environment variables (API keys)
└── requirements.txt         # Python dependencies
```

## Naming Conventions
- **Modules (`.py` files):** Use `snake_case`. Descriptive names reflecting their primary responsibility (e.g., `grouping.py`, `routing.py`).
- **Classes:** Use `PascalCase`. Usually represent services (`LLMClient`, `Pipeline`, `FileOrganizer`) or data models (`DocumentGroup`, `PageData`, `TenantTimeline`).
- **Functions:** Use `snake_case`. Prefix private internal functions with an underscore (e.g., `_group_and_route_documents`).
- **Data Models:** Reside in `src/core/schemas.py` and extensively use Pydantic for validation.

## Key Locations

- **Entry Point:** `src/main.py` is the main script that orchestrates the workflow.
- **Pass 1 Logic:** `src/cleaning.py` handles parsing and canonicalization.
- **Pass 2 Logic:** `src/processing/pipeline.py` orchestrates boundary detection and routing.
- **Core Abstractions:** `src/core/schemas.py` defines the fundamental data types.
