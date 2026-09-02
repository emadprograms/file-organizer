---
status: investigating
trigger: "Why are maintenance documents all named 'siyana' (صيانة) and electricity ones named 'فاتورة خدمات'? Do these documents actually get a title that later gets discarded?"
created: 2026-09-02
updated: 2026-09-02
---

## Symptoms

- **Expected:** Maintenance and utility documents get unique AI-generated titles like other document categories
- **Actual:** All maintenance docs get the hardcoded Arabic title "صيانة" (siyana) and all utility bills get "فاتورة خدمات"
- **Key question:** Do these docs generate a title somewhere that later gets discarded?

## Current Focus

hypothesis: "Maintenance and utility documents bypass the LLM grouping entirely (deterministic path in `process_with_shrink`), so they NEVER generate a title. The `brief_arabic_title` is hardcoded at group creation time and no LLM title generation happens."
test: "Trace all code paths in `grouping/core.py` for block_type == 'maintenance' and block_type == 'utility'"
expecting: "No LLM call is made; the title field is set directly with a hardcoded string constant"
next_action: "Confirm diagnosis and decide: should these docs get LLM-generated titles or is a per-document naming strategy (e.g. combining date + type) sufficient?"

## Evidence

- timestamp: 2026-09-02T17:47:00
  note: "In `process_with_shrink` (grouping/core.py L165-204), when block_type is 'maintenance' or 'utility', the code creates DocumentGroup objects directly WITHOUT calling `_process_chunk` (which calls the LLM). For maintenance: `brief_arabic_title='صيانة'` is set on line 178. For utility: `brief_arabic_title='فاتورة خدمات'` set on line 203."

- timestamp: 2026-09-02T17:47:00
  note: "The LLM path (`_process_chunk`) is ONLY called for block_type == 'other' (lines 206+). This means: maintenance and utility docs never get an LLM-generated title. The title is assigned once, deterministically, and flows through the rest of the pipeline as-is."

- timestamp: 2026-09-02T17:47:00
  note: "Contrast: 'other' block types go through the full LLM grouping pipeline which returns `GroupEntry.brief_arabic_title` from the LLM (line 101: `brief_arabic_title=g.brief_arabic_title`). These get unique per-document titles."

- timestamp: 2026-09-02T17:47:00
  note: "The `brief_arabic_title` is used as the document display name in: routes.py (lines 122, 145, 193, 222, 471, 473), index.html (lines 379, 470), timeline/core.py (line 285), routing/router.py (lines 89, 115, 250, 286, 320), reconcile/core.py (line 863). It is never overwritten post-grouping."

## Eliminated

- hypothesis: "The title is generated but then discarded by a later pipeline step"
  reason: "No evidence of any overwrite. `brief_arabic_title` from grouping is used directly throughout the pipeline as the document's display name."

## Resolution

root_cause: "Maintenance and utility blocks are handled by a deterministic (non-LLM) fast path in `process_with_shrink`. This fast path hardcodes the `brief_arabic_title` to a fixed string ('صيانة' for maintenance, 'فاتورة خدمات' for utility) and NEVER invokes the LLM. This is by design — it was built for performance/reliability — but it means all maintenance/utility docs share the same generic name instead of getting a meaningful per-document title."
fix: "NOT YET DECIDED — options: (A) Add LLM title generation for maintenance/utility after deterministic grouping, (B) Construct a richer title from date + subcategory code, (C) Keep generic titles but add a document counter (صيانة 1, صيانة 2, etc.)"
verification: "pending"
files_changed: []
