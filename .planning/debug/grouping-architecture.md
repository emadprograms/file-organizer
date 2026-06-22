# Debug Session: Family-Aware Grouping Architecture

## Issue Description
The 1-pass sequential architecture (the "sliding window") is fundamentally flawed for grouping family members. When evaluating Page 17, the LLM only knows about Page 16. If Page 16 is for "Mohammed" and Page 17 is for his wife "Amina", the LLM sees a different name and decides it is a NEW document, rather than recognizing that both pages belong to the same family unit's "Basic Details" dossier. 

## Proposed Solution: The Two-Pass Architecture
The user proposed a global-context approach: "first go through all pages and identify who were tenants... then group based on who it belongs to."

We can implement this efficiently without adding any extra time to the pipeline:

### Pass 1: Vision Extraction (The "Slow" Pass)
- We process all 150 pages sequentially through Gemma Vision, just like we do now, but we **stop asking it to group things** (`is_continuation`). 
- We strictly ask it to extract the raw facts per page: `house_number`, `resident`, and `category`. 
- We store this in a flat array: `[ {page: 0, resident: "X", category: "Y"}, ... ]`.

### Pass 2: Global Family Grouping (The "Fast" Text-Only Pass)
- Once all pages are extracted, we take the entire array of 150 results and send it to Gemma as **text only**. 
- Text-only processing is incredibly fast (takes ~5 seconds for the whole document).
- We give Gemma a new System Prompt:
  > "Here is the page-by-page extraction of a housing file. First, identify the primary family unit (e.g., father, mother, kids) from the names. 
  > Then, group consecutive pages into logical documents. If consecutive 'basic_details' or 'personal_details' pages belong to different members of the SAME family, merge them into a single Document Group under the primary tenant's name. Amar Takhsees can be independent."
- Gemma returns the perfectly clustered `DocumentGroup` boundaries with full global context.

## Benefits
- **Zero speed penalty**: We still only process the images once. 
- **Perfect Global Context**: The LLM gets to "see" the entire list of tenants before making a single grouping decision, exactly as the user requested.
