# Project Research Summary

> Synthesized 2026-07-03 from STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md

## Key Findings

### Stack
- **Core**: Python 3.10+, PyMuPDF, `google-genai` (NOT legacy `google-generativeai`), Pydantic v2, PyYAML, Tenacity, RapidFuzz, Rich
- **CLI**: `argparse` (stdlib) — no framework needed for single-command tool
- **Critical**: Avoid async (7s rate limit makes it pointless), avoid LangChain (overkill), avoid pandas (native Python + Pydantic sufficient)
- **Arabic prep**: `unicodedata.normalize('NFKC')` + custom regex for Hamza/Alef/Tashkeel normalization before any fuzzy matching

### Table Stakes Features
- Fail-fast input validation (Pydantic config + file existence)
- Deterministic YAML-driven routing (single-match = dict lookup, multi-match = LLM)
- Structured audit logging (JSON lines, UTF-8, full LLM request/response capture)
- ISO 8601 date-based filenames
- PDF splitting with page count reconciliation (pages in = pages out)
- Tenacity-style retry with error categorization

### Architecture
- **Two-pass pipeline**: Pass 1 (Cleaning) guarantees every page has tenant + date → Pass 2 (Grouping) operates on clean data
- **Centralized LLM client**: Singleton with 7s rate limit, tiered error handling (400/404 fail fast, 500 retry 15s, 429 retry 65s)
- **Stage-specific Pydantic models**: `PageData` → `CleanedPage` → `DocumentGroup` → `RoutedGroup` → `OutputFile`
- **Module structure**: `src/cleaning/` (6 modules) + `src/grouping/` (7 modules) + shared infra (`llm.py`, `config.py`, `schemas.py`, `logger.py`)
- **Build order**: Schemas → Config → Logger → LLM Client → Report Parser → Pass 1 modules → Pass 2 modules → Output → CLI

### Critical Pitfalls
1. **Entity resolution is #1 risk**: Arabic OCR produces 7+ variants of one name. Anchor-based resolution + LLM canonicalization + 5-doc threshold mitigates this.
2. **Boundary detection hallucination is #2**: "Date changes are NOT boundaries" contradicts LLM intuition — prompt must aggressively suppress this. Programmatic verification catches invented pages.
3. **Windows filesystem is #3**: Arabic filenames + nested folders easily breach MAX_PATH 260. Must sanitize filenames (strip reserved chars, truncate to 200), use atomic writes, enforce UTF-8 everywhere.
4. **Overlap merge edge cases**: Category pre-split must happen BEFORE boundary detection to prevent category boundaries being overridden by grouping merge.
5. **Rate limiting shapes everything**: 7s minimum = 100-page PDF takes 70+ seconds just for boundary detection. Minimize LLM calls — single-match routing should never touch the LLM.

## Implications for Roadmap

### Phase Ordering
1. **Foundation first** (schemas, config, logger, LLM client) — everything depends on these
2. **Pass 1 before Pass 2** — Pass 2 assumes clean data; building it first would require mock data
3. **Pure logic modules before LLM-dependent** — anchors, tenants, timeline, presplit, merge are fast to build/test; canonicalize, boundaries, router are slower
4. **Output + CLI last** — thin wiring that only makes sense once both passes exist

### Risk Mitigations to Build Early
- Arabic filename sanitization utility (cross-cutting, needed by Pass 2)
- LLM response Pydantic validation (every LLM call needs this)
- Page count reconciliation check (catch data loss immediately)
- UTF-8 enforcement in all file/logging handlers

### LLM Call Budget
| Call Type | Frequency | Cost Driver |
|-----------|-----------|-------------|
| Name canonicalization | 1 per house | Cheap |
| Boundary detection | ~pages/10 chunks | Dominant cost |
| Folder routing (multi-match) | Per ambiguous group | Medium |
| Arabic filename summary | Per output document | Medium |

**Optimization**: Batch folder routing + filename generation into a single LLM call per document group where possible.

## Sources

- [STACK.md](file:///C:/Users/Emad/Documents/GitHub/file-organizer/.planning/research/STACK.md)
- [FEATURES.md](file:///C:/Users/Emad/Documents/GitHub/file-organizer/.planning/research/FEATURES.md)
- [ARCHITECTURE.md](file:///C:/Users/Emad/Documents/GitHub/file-organizer/.planning/research/ARCHITECTURE.md)
- [PITFALLS.md](file:///C:/Users/Emad/Documents/GitHub/file-organizer/.planning/research/PITFALLS.md)
