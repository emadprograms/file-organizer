<!-- GSD:project-start source:PROJECT.md -->

## Project

**File Organizer Post-Processor**

A CLI-based post-processing tool that takes pre-categorized housing PDFs and their corresponding JSON reports, resolves tenant identities, groups pages into logical multi-page documents, and organizes them into a structured directory hierarchy: House → Tenant (with timeline) → 13 Topic Folders. Built for the Kingdom of Bahrain Ministry of Interior housing document workflow.

**Core Value:** Automatically transform a flat, pre-categorized PDF into a perfectly organized folder structure per tenant, with zero manual sorting — driven entirely by the JSON report data, LLM intelligence, and configurable YAML routing rules.

### Constraints

- **Model**: Gemma 4 26B A4B IT — all LLM calls use this model
- **Rate Limit**: Minimum 7 seconds between LLM requests, enforced centrally
- **Single Processing**: No batch mode — one house directory per invocation
- **Compatibility**: Must consume the JSON report format from the existing categorizer without modification
- **Language**: Output filenames and LLM summaries in Arabic

<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->

## Technology Stack

## Recommended Stack

### Core Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| `pymupdf` | ≥1.28.0 | PDF splitting by page ranges, rendering pages as images for LLM vision |
| `google-genai` | ≥2.10.0 | Unified SDK for Gemini/Gemma model calls (replaces legacy `google-generativeai`) |
| `pydantic` | ≥2.13.4 | Config validation, LLM response schemas, data models |
| `pydantic-settings` | ≥2.x | YAML config loading with env-var overrides via custom settings source |
| `pyyaml` | ≥6.0 | YAML parsing (used by pydantic-settings under the hood) |
| `tenacity` | ≥9.1.4 | Retry logic with exponential backoff for LLM API calls |
| `rapidfuzz` | ≥3.14.5 | Fuzzy string matching for Arabic name canonicalization |
| `python-dotenv` | ≥1.2.2 | Load API keys and secrets from `.env` files |
| `rich` | ≥15.0.0 | Beautiful terminal output: progress bars, tables, colored logs |

### Standard Library (No Install)

| Module | Purpose |
|--------|---------|
| `argparse` | CLI argument parsing (simple enough — no subcommands needed) |
| `logging` | Structured logging with file + console handlers |
| `pathlib` | Cross-platform path manipulation |
| `json` | JSON report parsing |
| `re` | Arabic text normalization regex |
| `unicodedata` | Unicode normalization for Arabic text (NFC/NFKC) |

### Python Version

- **Python 3.10+** (required by PyMuPDF wheels and for `match` statements, union type hints `X | Y`)

## Rationale

### PDF Manipulation — PyMuPDF (`pymupdf`)

- **Why**: The project needs page-level PDF splitting by ranges, which PyMuPDF handles with near-native speed via its C-based MuPDF engine. It can also render pages as images for LLM vision calls.
- **Fit**: PROJECT.md explicitly requires "PyMuPDF for PDF splitting by page ranges" — this is a confirmed constraint.
- **AGPL note**: Licensed AGPL-3.0. Since this is an internal tool (not distributed), AGPL is not a concern. If distribution becomes necessary, a commercial license would be needed.

### LLM Client — `google-genai`

- **Why**: The unified, official Google SDK for both Gemini Developer API and Vertex AI. Replaces the legacy `google-generativeai` package. Supports the Gemma 4 model family used by this project.
- **Usage pattern**: `client.models.generate_content(model="gemma-4-26b-a4b-it", contents=...)` with structured JSON output via Pydantic schemas.
- **Critical**: Do NOT use the old `google-generativeai` package — it is deprecated and no longer receives feature updates.

### YAML Parsing — PyYAML

- **Why**: The project only *reads* YAML configs (no round-trip editing needed). PyYAML is the industry standard with the fastest performance via LibYAML C bindings (`CSafeLoader`).
- **Integration**: Used under the hood by `pydantic-settings`'s `YamlConfigSettingsSource`.
- **Security**: Always use `yaml.safe_load()` — never `yaml.load()`.

### Config Validation — Pydantic v2 + pydantic-settings

- **Why**: PROJECT.md requires "Pydantic validation of `sample-config.yaml` format on startup before any processing". Pydantic v2 is the standard for typed config validation in Python.
- **Pattern**: Define the config as a `BaseSettings` model with `YamlConfigSettingsSource`, then env vars can override YAML values (e.g., `GEMINI_API_KEY`).
- **Best practice**: Use `model_config = SettingsConfigDict(extra="forbid")` to catch typos in YAML.

### CLI Framework — `argparse` (stdlib)

- **Why**: The CLI is simple — takes a single directory path argument (`python organize.py ./pdfs/1273`). No subcommands, no interactive prompts. `argparse` is zero-dependency and sufficient.
- **If complexity grows**: Migrate to `typer` (type-hint driven, built on Click) — but avoid premature abstraction.

### Retry & Rate Limiting — Tenacity

- **Why**: PROJECT.md specifies detailed retry behavior (400→fail, 500→wait 15s, 429→wait 65s). Tenacity's composable `retry_if_exception_type`, `wait_fixed`, and `stop_after_attempt` primitives map directly to these requirements.
- **Pattern**: Custom exception classes (`RateLimitError`, `ServerError`, `ClientError`) with separate `@retry` decorators or a centralized retry wrapper.
- **Critical**: The 7-second minimum between requests is a *rate limit* (use `time.sleep` or a token bucket), not a *retry* — don't conflate the two.

### Fuzzy Matching — RapidFuzz

- **Why**: The project needs LLM-driven name canonicalization, but also needs programmatic fuzzy matching for merging OCR spelling variations of Arabic names. RapidFuzz is 40%+ faster than thefuzz/fuzzywuzzy, actively maintained, and Unicode-aware.
- **Arabic-specific prep**: Before matching, normalize Arabic text: unify ى/ي, ه/ة, strip diacritics (tashkeel), normalize alef variants (أ/إ/آ→ا). Use `unicodedata.normalize('NFKC', text)` + custom regex.
- **Note**: RapidFuzz handles the *scoring*; Arabic normalization is a preprocessing step you must build.

### Logging — stdlib `logging`

- **Why**: PROJECT.md requires "logs directory at project root `./logs/[timestamp]/` with full audit trail". The stdlib `logging` module with `FileHandler` + `StreamHandler` covers this perfectly. No need for structlog or loguru for a single-user CLI tool.
- **Enhancement**: Use `rich.logging.RichHandler` as the console handler for colored, readable terminal output during development.
- **Pattern**: One logger per module (`logger = logging.getLogger(__name__)`), configured once at entry point.

### Terminal Output — Rich

- **Why**: Professional progress bars for multi-page PDF processing, colored status output, and pretty-printed tables for audit summaries. Pairs perfectly with stdlib logging via `RichHandler`.

### Environment Variables — python-dotenv

- **Why**: Already in the project (`.env` file exists with `GEMINI_API_KEY`). Simple, proven, no reason to change.

## Alternatives Considered

### PDF Libraries

| Library | Verdict | Why Not |
|---------|---------|---------|
| `pypdf` | ❌ Skip | Pure Python, significantly slower. Adequate for simple merge/split but PyMuPDF is already a project constraint and needed for image rendering. |
| `pymupdf4llm` | ⚠️ Optional | Useful if you need to extract structured Markdown from PDFs for LLM context. Not needed here since the categorizer already provides JSON reports. |
| `pdfplumber` | ❌ Skip | Good for table extraction but overkill here — no table parsing required. |

### LLM SDKs

| Library | Verdict | Why Not |
|---------|---------|---------|
| `google-generativeai` | ❌ Deprecated | Legacy SDK, replaced by `google-genai`. Will not receive new features. |
| `openai` | ❌ Skip | The project uses Google Gemma, not OpenAI models. |
| `litellm` | ⚠️ Overkill | Useful multi-provider wrapper, but adds complexity when you only use one provider. |
| `langchain` | ❌ Avoid | Massive dependency, abstraction overhead. Direct SDK calls are simpler and more predictable for this use case. |

### CLI Frameworks

| Library | Verdict | Why Not |
|---------|---------|---------|
| `typer` | ⚠️ Future option | Excellent DX with type hints, but adds Click as a transitive dependency. Justified only if subcommands are added later. |
| `click` | ❌ Skip | More boilerplate than typer, less modern. Only justified for complex CLI trees. |
| `fire` | ❌ Skip | Auto-generates CLI from functions/classes — too magical, poor help text control. |

### YAML Parsers

| Library | Verdict | Why Not |
|---------|---------|---------|
| `ruamel.yaml` | ❌ Skip | Designed for round-trip editing (preserving comments). Slower than PyYAML. This project only reads YAML. |
| `strictyaml` | ⚠️ Interesting | Type-safe YAML without implicit typing. But Pydantic already handles validation, so this is redundant. |

### Fuzzy Matching

| Library | Verdict | Why Not |
|---------|---------|---------|
| `fuzzywuzzy` | ❌ Deprecated | Unmaintained. RapidFuzz is a drop-in replacement with better performance. |
| `thefuzz` | ❌ Skip | Rebrand of fuzzywuzzy, still largely inactive. |
| `jellyfish` | ⚠️ Complement | Phonetic algorithms (Soundex, Metaphone) — could complement RapidFuzz for English transliterations of Arabic names, but not a primary tool. |

### Logging

| Library | Verdict | Why Not |
|---------|---------|---------|
| `structlog` | ❌ Overkill | Excellent for microservices with JSON log aggregation. Too much setup for a single-user CLI. |
| `loguru` | ⚠️ Nice-to-have | Zero-config colored logging with exception formatting. But Rich already covers the pretty-printing need, and stdlib logging is more standard. |

## What to Avoid

### ❌ `google-generativeai` (legacy SDK)

### ❌ `langchain` / `llama-index`

### ❌ `fuzzywuzzy` / `thefuzz`

### ❌ `yaml.load()` (unsafe)

### ❌ `pdfminer.six`

### ❌ Over-engineering the CLI

### ❌ Async for LLM calls

### ❌ `pandas` for data manipulation

### ❌ Database (SQLite, etc.)

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.agents/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
