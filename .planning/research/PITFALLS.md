# Pitfalls Research: Document Processing & Organization Pipeline

> Research conducted 2026-07-03. Specific to: Arabic housing PDF post-processor with LLM (Gemma 4 26B A4B IT), PyMuPDF, Pydantic, YAML config, Windows deployment.

---

## Critical Pitfalls

### 1. LLM Hallucination in Document Boundary Detection

**Risk: HIGH — Silent data corruption**

The overlapping-chunk boundary detection (pages 1-10, 10-20, 20-30) asks the LLM to decide where one document ends and another begins. This is the most hallucination-prone operation in the pipeline.

| Failure Mode | Description | Impact |
|:---|:---|:---|
| **Phantom boundaries** | LLM invents a boundary mid-document because two consecutive pages have different formatting | One letter split into two PDFs |
| **Missed boundaries** | Two unrelated single-page documents merged because they share topic keywords | Wrong document in wrong tenant folder |
| **Overlap-merge conflicts** | Page 10 appears in both chunks with different groupings | Page duplicated or dropped |
| **Positional bias** | LLMs perform worse in the middle of long context windows | Boundaries missed in chunk interior |
| **Reasoning hallucination** | LLM provides confident reasoning that contradicts the actual rules (e.g., "date changed" as a boundary) | False sense of verification |

**Specific to this project:** The rule that "date changes and sender/receiver changes are NOT boundaries" directly contradicts LLM intuition. The prompt must aggressively suppress this.

### 2. Arabic Text & RTL Handling in Filenames and Paths

**Risk: HIGH — Platform-specific silent failures**

Output filenames are Arabic (`2026-04-03 - ملخص قصير بالعربية.pdf`). This creates multiple failure vectors on Windows:

| Failure Mode | Description | Impact |
|:---|:---|:---|
| **BiDi rendering in mixed content** | Mixed LTR (date, extension) and RTL (Arabic) segments render unpredictably | Confusing but functional |
| **Unicode normalization mismatches** | Arabic text in NFC vs NFD forms; two filenames look identical but differ at byte level | File-not-found errors on valid files |
| **Encoding in subprocess/logging** | Python's `print()` to Windows console may throw `UnicodeEncodeError` | Crashes in logging |
| **Invisible directional characters** | LLM-generated Arabic may include zero-width joiners, right-to-left marks | Filenames that look identical but differ |

### 3. Entity Resolution Failures (Tenant Name Canonicalization)

**Risk: HIGH — Cascading data misrouting**

| Failure Mode | Description | Impact |
|:---|:---|:---|
| **False merge (Type I)** | Two different people with similar names merged into one tenant | Documents from person A in person B's folder |
| **False split (Type II)** | Same person's Arabic and English names treated as two tenants | Same tenant gets two folders |
| **OCR-induced variations** | Garbled names from Arabic cursive script segmentation errors | Names map to wrong anchor |
| **Anchor contamination** | Multi-name pages (like forms with 10+ names) flood the anchor system | Incidental names promoted to tenants |
| **Relationship suffix confusion** | Names with (زوجة) not normalized correctly | Wife split into separate entity |
| **Hamza/Alif variations** | أحمد vs احمد vs إحمد — same name, different bytes | Silent mismatch in string comparison |

### 4. PDF Manipulation Edge Cases (PyMuPDF)

**Risk: MEDIUM — Data loss on edge cases**

| Failure Mode | Description | Impact |
|:---|:---|:---|
| **Scanned vs digital mix** | Single PDF with both digital and scanned pages | Inconsistent extraction quality |
| **Page rotation** | Scanned landscape pages with rotation metadata | Page rendered incorrectly if rotation stripped |
| **Corrupted page streams** | PyMuPDF warns to stderr instead of raising exceptions | Silent data corruption |
| **Zero-byte pages** | Blank separator pages in the scan batch | LLM hallucinates content for blank pages |

### 5. Rate Limiting Race Conditions

**Risk: MEDIUM — Intermittent production failures**

| Failure Mode | Description | Impact |
|:---|:---|:---|
| **Timer drift** | `time.sleep(7)` doesn't account for request duration | Wasted throughput |
| **Retry-after timing interaction** | 429 wait (65s) or 500 wait (15s) should reset the 7s timer, not compound | Unnecessarily long waits |
| **Consecutive-error counter not resetting** | Counter must reset on ANY success, not just same call type | One call type's errors poison global counter |

### 6. Chunk Boundary Edge Cases (Overlapping Page Logic)

**Risk: HIGH — Data integrity**

| Failure Mode | Description | Impact |
|:---|:---|:---|
| **Last chunk runt** | Final chunk has fewer pages, LLM behavior may differ | Inconsistent grouping quality |
| **Single-page overlap insufficient** | Multi-page document spanning chunks 9-12 with only page 10 overlapping | Not enough context to merge |
| **Overlap page group conflict** | Page 10 in different groups across chunks — merge must produce correct result | Incorrect merge |
| **Category pre-split interaction** | Category change at overlap page — must respect category boundary | Category boundaries overridden by grouping |

### 7. YAML Config Validation Gaps

**Risk: MEDIUM — Fail-late bugs**

| Failure Mode | Description | Impact |
|:---|:---|:---|
| **Category ID mismatch** | Config uses different format than JSON report | Documents routed to fallback folder |
| **Routing rule completeness** | Not all categories mapped to folders | Some categories never find their folder |
| **Prompt template injection** | YAML special characters in prompts | Silently corrupted prompts |

### 8. Logging and Auditability Gaps

**Risk: HIGH — Debugging impossible in production**

| Failure Mode | Description | Impact |
|:---|:---|:---|
| **No LLM request/response logging** | Can't see prompts and responses | Hours of debugging |
| **No page-level audit trail** | Can't trace why a page ended up where it did | User disputes unresolvable |
| **Lost intermediate state** | Pipeline crash mid-Pass-2 loses all grouping progress | Full re-run; wasted API calls |
| **Log file Arabic encoding** | Default logging handler may not write UTF-8 | Logs unreadable |
| **No diff between input and output** | Page loss undetectable without reconciliation report | Silent data loss |

### 9. File System Issues (Windows-Specific)

**Risk: HIGH — This is a Windows-deployed tool**

| Failure Mode | Description | Impact |
|:---|:---|:---|
| **MAX_PATH (260 chars)** | Nested Arabic folders + long filenames easily exceed 260 | `FileNotFoundError` on write |
| **Reserved characters in LLM output** | Arabic text may contain `:` (common after الموضوع:), `?`, `"`, `\|` | Windows rejects the filename |
| **Filename length limit** | NTFS 255 char limit; verbose Arabic summaries exceed this | Truncation or error |
| **File locking** | Explorer or antivirus has file locked | Intermittent write failures |
| **Atomic writes** | Crash mid-write produces corrupted PDF | Corrupted output PDFs |

---

## Prevention Strategies

### LLM Guardrails
1. **Constrained output schemas**: Every LLM call must return Pydantic-validated JSON. Reject and retry non-conforming responses.
2. **Boundary detection double-check**: Programmatically verify no page gaps, overlaps, or invented pages.
3. **Reasoning audit**: Log reasoning for every grouping. Flag reasoning that mentions "date changed" as a boundary.
4. **Consider 2-page overlap** instead of 1 to give merge logic more context for multi-page documents straddling chunk boundaries.

### Arabic/RTL Safety
1. **Unicode normalize all filenames**: `unicodedata.normalize('NFC', filename)` before any file operation.
2. **Strip invisible characters**: Remove U+200B-U+200F, U+FEFF, U+061C from LLM-generated text.
3. **Sanitize filenames explicitly**: Replace Windows-reserved characters from LLM-generated summaries.
4. **Truncate filenames to 200 chars**: Leave margin for path prefixes.
5. **Enforce UTF-8 everywhere**: All file handles, logging handlers must specify `encoding='utf-8'`.

### Entity Resolution Safety
1. **Arabic text normalization before comparison**: Normalize Hamza forms, Taa Marbuta, final Yaa, remove diacritics.
2. **Cross-language matching**: Canonicalization prompt must handle Arabic↔English name pairs.
3. **Anchor document filtering**: Only pages with exactly 1 name should be anchor sources. Multi-name pages excluded.
4. **Relationship suffix stripping**: Strip (زوجة), (ابن) before canonicalization.
5. **Deduplication audit log**: Output a mapping table showing every variant → canonical name.

### PDF Robustness
1. **Detect scanned vs digital**: Check `page.get_text()` length.
2. **Preserve rotation metadata**: Copy `page.rotation` to output.
3. **Blank page detection**: Skip pages with no text and minimal image content.
4. **Page count reconciliation**: Verify sum of output pages = input pages.

### Rate Limiting
1. **Timestamp last-response-received**: Measure 7s gap from response received, not request sent.
2. **Reset error counters on success**: Any success resets ALL consecutive error counters.
3. **Separate error counters per call type**: Boundary detection and other calls have different strategies.

### File System
1. **Write to temp, rename to final**: Atomic writes via `tempfile` + `os.replace()`.
2. **Path length check**: Before any write, check total path length. Truncate filename if > 240.
3. **Sanitize LLM filenames with allowlist**: Only Arabic letters, digits, spaces, hyphens, parentheses.

---

## Phase Mapping

| Phase | Pitfall Categories | Priority Mitigations |
|:---|:---|:---|
| **Startup & Config Validation** | YAML validation (#7), File system setup (#9) | Pydantic config validation, path length pre-check |
| **Pass 1 — Document Cleaning** | Entity resolution (#3), Arabic text (#2) | Arabic normalization, anchor filtering, canonicalization prompt, audit log |
| **Pass 1 — Timeline Building** | Entity resolution (#3) | Timeline overlap rule (earlier tenant wins), null date inference |
| **Pass 2 — Boundary Detection** | LLM hallucination (#1), Chunk boundaries (#6), Rate limiting (#5) | Overlap merge algorithm, programmatic verification, reasoning audit |
| **Pass 2 — Folder Routing** | YAML config (#7), LLM hallucination (#1) | Category→folder cross-reference, single-match bypass, constrained LLM choices |
| **Pass 2 — PDF Splitting** | PDF edge cases (#4), File system (#9) | Rotation preservation, page count reconciliation, atomic writes, filename sanitization |
| **Logging & Audit Trail** | Logging gaps (#8) | Structured JSON logs, LLM request/response capture, reconciliation manifest, UTF-8 |

### Cross-Cutting Concerns (All Phases)
- **UTF-8 encoding**: Must be enforced in every module that touches strings, files, or logging.
- **Windows path safety**: Every file operation must account for MAX_PATH.
- **LLM output validation**: Every LLM response must be Pydantic-validated before use.
- **Arabic text normalization**: Any string comparison involving Arabic text must normalize first.

---

*Sources: Web research on PyMuPDF edge cases, Arabic NLP entity resolution, Windows NTFS limitations, LLM hallucination in document processing, Pydantic YAML validation patterns, rate limiting architectures.*
