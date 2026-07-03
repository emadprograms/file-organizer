# Feature Landscape: Document Organization & Processing Tools

> Research conducted 2026-07-03 for the File Organizer Post-Processor project.
> Covers document boundary detection, entity resolution, configurable routing, audit logging, error recovery, timeline organization, and anti-features.

---

## Table Stakes

These are features that any document processing/organization pipeline is expected to have. Missing any of these would be a serious gap.

### 1. Fail-Fast Input Validation
- Validate all inputs (PDF existence, JSON report format, config schema) before any processing begins
- Pydantic or JSON Schema validation of configuration on startup
- Clear, actionable error messages — never raw stack traces
- **Industry norm**: Every mature pipeline validates inputs at the gate; processing garbage wastes LLM tokens and time

### 2. Deterministic Routing Rules (Rules Engine)
- Category-to-folder mapping via external configuration (YAML/JSON), not hardcoded
- Single-match categories route directly without LLM involvement (fast path)
- Multi-match categories use LLM as tiebreaker (slow path)
- Fallback/default folder for unroutable documents
- **Industry norm**: Decoupling business rules from code is foundational — every enterprise IDP system separates routing logic from pipeline code

### 3. Structured Audit Logging
- Every processing decision logged with the "Five Ws": Who (which tenant), What (action taken), When (timestamp), Where (source page → destination file), Why (reasoning/confidence)
- Structured format (JSON lines) for machine parseability
- Append-only log files per run with unique run identifiers
- **Industry norm**: Compliance-grade systems require end-to-end chain of custody; this project's government context makes it critical

### 4. ISO 8601 Date-Based File Naming
- Output files named with `YYYY-MM-DD` prefix for natural filesystem sort order
- Consistent separator conventions (hyphens, not mixed formats)
- Handles missing dates gracefully (inferred dates, explicit "undated" markers)
- **Industry norm**: This is the universal gold standard for chronological file organization

### 5. PDF Splitting Without Data Loss
- Page-level integrity verification: total pages in = total pages out
- No gaps, no overlaps, no invented pages in the output
- PyMuPDF or equivalent for lossless page extraction
- **Industry norm**: Page loss during splitting is a catastrophic failure — every tool must guarantee conservation

### 6. Graceful Error Handling with Retry Logic
- Transient errors (429, 500, 503): exponential backoff with configurable retry limits
- Structural errors (malformed PDF pages): skip and log, don't halt the entire pipeline
- Fatal errors (missing API key, invalid config): fail fast with clear message
- **Industry norm**: Tenacity-style retry with error categorization is standard in any API-dependent pipeline

### 7. Category-Based Pre-Splitting
- Use category metadata as an automatic, free boundary signal before LLM-driven detection
- Category change = guaranteed document boundary (no LLM needed)
- **Industry norm**: Using available structural signals before expensive AI is a basic optimization

---

## Differentiators

These features go beyond table stakes and represent meaningful competitive advantages or architectural sophistication.

### 1. Overlapping-Chunk Boundary Detection with Programmatic Merge
- **Approach**: Process pages in overlapping windows (e.g., pages 1–10, 10–20, 20–30) and merge on the overlap page using set intersection
- **Why it's differentiating**: Most tools use either naive fixed splits or expensive full-document LLM passes. The overlapping window approach balances cost (bounded LLM context) with accuracy (overlap validates boundaries)
- **Key risk**: Overlap merge logic must handle disagreements between chunks

### 2. Anchor-Based Tenant Resolution
- **Approach**: Only extract tenant names from high-signal document types (contracts, forms, ID cards), not every page
- **Why it's differentiating**: Most entity resolution systems treat all sources equally. Anchor-based resolution acknowledges that a maintenance worker's name on a work order is noise, not signal
- **5-document + 1-anchor threshold**: Filters incidental names without being overly aggressive

### 3. LLM-Driven Arabic Name Canonicalization
- **Approach**: Use LLM to merge OCR spelling variations, Arabic/English transliterations, and name-with-relationship annotations
- **Why it's differentiating**: Arabic name resolution is genuinely harder than Latin-script equivalents:
  - No capitalization signal for entity detection
  - Hamza/Alef variants (أ, إ, آ, ا) are often interchanged
  - Diacritics (tashkeel) presence is inconsistent
  - OCR error patterns differ from Latin (connected script, ligatures)
  - Names span 4–5 parts with variable transliteration

### 4. Timeline-Based Document Ownership
- **Approach**: Build timelines from min/max dates per tenant, then assign documents to the tenant whose timeline covers the document date; overlaps → earlier tenant
- **Why it's differentiating**: Most systems assign documents by explicit metadata. Timeline-based ownership handles the common case where a document doesn't name its owner but falls within a known tenancy period

### 5. Subject/Content Shift as the ONLY Boundary Signal
- **Approach**: Date changes and sender/receiver changes are NOT boundaries — only topic/subject shifts count
- **Why it's differentiating**: This is a domain-specific insight. A back-and-forth exchange about the same maintenance issue is one logical document

### 6. LLM Reasoning Audit Trail
- **Approach**: Require the LLM to provide reasoning for every grouping decision, not just the output
- **Why it's differentiating**: Most pipelines log what the LLM decided but not why. Explicit reasoning enables post-hoc audit and prompt refinement

### 7. Null Tenant/Date Inference by Positional Proximity
- **Approach**: Unresolvable tenant/date → infer from nearest dated page by position in the PDF
- **Why it's differentiating**: Most tools would dump these into an "unknown" bucket. Positional inference leverages the physical ordering of scanned documents

### 8. Dry Run / Preview Mode
- Show exactly what the pipeline would do without writing any files
- **Why it's differentiating for this tool**: Government workflows need sign-off before execution

---

## Anti-Features

Things to deliberately NOT build for a single-house CLI tool with a specific government workflow.

### 1. ❌ GUI or Web Interface
- CLI only. A GUI adds maintenance burden with zero value for the target user.

### 2. ❌ Real-Time / Streaming Processing
- Batch tool. Event-driven architectures are massive over-engineering.

### 3. ❌ Plugin / Extension System
- The YAML config IS the extension mechanism. A generic plugin architecture adds abstraction layers that slow development.

### 4. ❌ Multi-User / Concurrent Access
- Single operator, single invocation, single house. No locking, sessions, or RBAC.

### 5. ❌ Custom ML Model Training
- The LLM (Gemma 4) handles the long tail of OCR noise better than any model trained on limited data.

### 6. ❌ Document Storage / DMS Features
- This tool organizes files into folders. It is NOT a Document Management System. No versioning, no search index.

### 7. ❌ Batch Processing Multiple Houses
- Explicitly out of scope. A simple shell loop handles batch needs.

### 8. ❌ Generic "Smart" AI-Only Organization
- Don't rely entirely on the LLM. Single-match category routing should be a dict lookup. Rule-based is faster, cheaper, and deterministic — LLM is the fallback.

---

## Complexity Notes

### Boundary Detection is the Hardest Problem
- Disagreement on overlap pages needs a deterministic tiebreaker
- Very short documents (1–2 pages) may be entirely within a single chunk
- LLM non-determinism: same pages, different runs → different groupings
- Chunk size tuning: 10 pages is arbitrary

### Arabic OCR Name Resolution is Genuinely Hard
- Transliteration ambiguity: "محمد" could be Muhammad, Mohamed, Mohammed, Mohd
- Relationship annotations: "آمنة (زوجة)" needs to resolve to the anchor tenant
- Name part count: Arabic names have 4–5 parts; OCR may capture 2–3

### Rate Limiting Shapes the Architecture
- 7-second minimum between LLM calls means a 100-page PDF = 70+ seconds just for rate limiting on boundary detection
- **Optimization imperative**: Minimize LLM calls. Every call you avoid saves 7+ seconds

### The "Unassigned" Folder is a Safety Valve
- Documents that can't be assigned never get silently dropped
- Unassigned folder size is a quality metric — smaller = better resolution

---

*Sources: Industry research on IDP pipelines, document processing tools, RAG chunking literature, Arabic NLP/OCR research, CLI design best practices.*
