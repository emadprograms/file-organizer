<!-- refreshed: 2026-07-07 -->
# Architecture

**Analysis Date:** 2026-07-07

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                      CLI Entry Point                        │
│                     `src/organize.py`                       │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Processing Pipeline                      │
│                    `src/processing/`                        │
├──────────────────┬──────────────────┬───────────────────────┤
│    Cleaning      │    Grouping      │      Routing          │
│  `src/cleaning.py`│ `src/processing/grouping.py` │ `src/processing/routing.py` │
└────────┬─────────┴────────┬─────────┴──────────┬────────────┘
         │                  │                     │
         ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                     LLM Orchestration                       │
│                      `src/llm/llm.py`                       │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  [File System / PDF Output / Checkpoints]                    │
│  `src/fs_utils.py` / `PyMuPDF`                               │
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| CLI Controller | Validates environment and coordinates the multi-pass pipeline | `src/organize.py` |
| Pipeline | Manages the flow from cleaning $ightarrow$ grouping $ightarrow$ routing | `src/processing/pipeline.py` |
| Cleaning Phase | Standardizes extracted data and resolves tenants | `src/cleaning.py` |
| Grouping Logic | Uses LLM to find boundaries between different documents | `src/processing/grouping.py` |
| Routing Logic | Assigns final folder paths to grouped documents | `src/processing/routing.py` |
| LLM Client | Orchestrates requests across Gemini, OpenRouter, and Groq with failover | `src/llm/llm.py` |
| Schemas | Defines Pydantic models for structured LLM I/O | `src/core/schemas.py` |
| Cache | Prevents redundant LLM calls using local JSON storage | `src/core/cache.py` |

## Pattern Overview

**Overall:** Sequential Pipeline with Failover LLM Orchestration.

**Key Characteristics:**
- **Multi-Pass Architecture:** Separates individual page classification (Pass 1) from document boundary detection (Pass 2).
- **Robust LLM Routing:** Implements a provider sequence with automatic failover and rate-limit cooldowns.
- **Structured I/O:** Heavily relies on Pydantic schemas to ensure LLM responses match expected data formats.
- **Checkpointing:** Saves intermediate results (`_cleaned.json`, `_grouped.json`) to allow resumption after failure.

## Layers

**Core Layer:**
- Purpose: Shared utilities, configuration, and data models.
- Location: `src/core/`
- Contains: `schemas.py`, `config.py`, `cache.py`, `utils.py`.
- Depends on: Pydantic.
- Used by: All other layers.

**LLM Layer:**
- Purpose: Abstracting LLM provider details and providing resilient API access.
- Location: `src/llm/`
- Contains: `llm.py`, `providers.py`.
- Depends on: `google-genai`, `openai`.
- Used by: `src/processing/` and `src/cleaning.py`.

**Processing Layer:**
- Purpose: Implementing the domain logic for document organization.
- Location: `src/processing/`
- Contains: `pipeline.py`, `grouping.py`, `routing.py`, `organizer.py`.
- Depends on: `src/llm/`, `src/core/`.
- Used by: `src/organize.py`.

## Data Flow

### Primary Request Path

1. **Entry Point** (`src/organize.py`): Validates target directory and loads environment.
2. **Cleaning** (`src/cleaning.py`): Takes raw JSON report, resolves canonical tenants via LLM, and produces `_cleaned.json`.
3. **Grouping** (`src/processing/pipeline.py` $ightarrow$ `src/processing/grouping.py`): Groups consecutive pages of the same category/tenant into segments using LLM boundary detection. Produces `_grouped.json`.
4. **Routing** (`src/processing/routing.py`): Assigns a folder path to each document group based on its content.
5. **Physical Organization** (`src/processing/organizer.py`): Uses PyMuPDF to split the original PDF into smaller files and move them to the routed folders.

## Key Abstractions

**LLMClient:**
- Purpose: A high-level wrapper for multiple LLM providers that handles retries, failovers, and structured output.
- Examples: `src/llm/llm.py`
- Pattern: Strategy Pattern (via `LLMProvider` subclasses).

**DocumentGroup:**
- Purpose: Represents a cohesive set of pages that form a single document.
- Examples: `src/core/schemas.py`
- Pattern: Data Transfer Object (DTO).

## Entry Points

**CLI Command:**
- Location: `src/organize.py`
- Triggers: Manual execution via `python src/organize.py [target_dir]`.
- Responsibilities: Environment validation, pipeline coordination, and final PDF generation.

## Architectural Constraints

- **API Rate Limits:** The pipeline is throttled by LLM API limits, necessitating the `delay_between_pages` and cooldown logic in `src/llm/llm.py`.
- **Sequential Processing:** Most stages are sequential, though some LLM calls use `ThreadPoolExecutor` for concurrency.
- **Local State:** The application is stateless between runs except for the local JSON checkpoints and cache.

## Error Handling

**Strategy:** Fail-fast on configuration errors; resilient retry/failover for API errors.

**Patterns:**
- **Provider Failover:** If Gemini fails, it tries OpenRouter, then Groq.
- **Atomic Writes:** Uses a temporary file pattern to prevent corrupting checkpoints (`src/fs_utils.py`).
- **Global Error Limit:** Aborts the pipeline if too many consecutive 500 errors occur.

## Cross-Cutting Concerns

**Logging:** Centralized logging via `src/logger.py` with dual output to console and file.
**Validation:** Pydantic models used at every LLM boundary to ensure data integrity.
**Authentication:** Managed via environment variables and `.env` files.

---

*Architecture analysis: 2026-07-07*
