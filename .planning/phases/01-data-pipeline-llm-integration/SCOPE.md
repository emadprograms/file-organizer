# Phase 2.5: Tenant-Aware Grouping & Timeline

## Scope

Refactor the pipeline from a single-pass sequential classifier into a two-pass architecture that first extracts per-page facts (category, name, date) and then groups documents based on tenant identity and chronological timeline.

## Why This Phase Exists

Phase 2 proved that Gemma 4 Vision accurately classifies document topics (13 categories). However, the single-pass sliding window approach fundamentally cannot solve:
- **Family fragmentation:** Consecutive personal_details pages for family members (father, wife, son) get split because the LLM sees different names
- **Tenant overlap:** When tenants change, documents from the outgoing and incoming tenant interleave chronologically — grouping by category alone incorrectly merges them
- **Date-wise filing:** Housing files are organized chronologically, not by person. The system needs to understand the timeline to correctly assign documents

## Key Deliverables

1. **Two-Pass Architecture**
   - Pass 1 (Vision): Extract category, resident name, house number, and document date from each page
   - Pass 2 (Code): Deterministic grouping based on tenant identity and timeline

2. **Date Extraction**
   - Extract document dates (Gregorian and/or Hijri) from each page during Pass 1
   - Handle missing dates gracefully

3. **Tenant Timeline Construction**
   - Identify primary tenants from frequency analysis of names
   - Build occupancy timeline: who lived in the house during which period
   - Assign every document to the correct tenant based on date + tenant period

4. **Correct Grouping Rules**
   - personal_details: inherit primary tenant from the preceding section (family members belong to the same tenant)
   - amar_takhsees: independent — can belong to someone who doesn't live there
   - All other categories: assigned to the tenant whose occupancy period matches the document date

5. **Classification Fix**
   - Update system prompt to clarify: basic_details = one-page form per person; personal_details = ID cards, civil records, family details

6. **Timeline Visualization** (stretch)
   - Visual output showing tenant occupancy periods and document distribution

## Dependencies

- Phase 2 (complete): Gemma 4 Vision integration, 13-category classification, PDF ingestion
