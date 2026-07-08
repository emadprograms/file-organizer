# Phase 07: Anti-Hallucination Schema Enforcement - Context

## Domain
The goal of this phase is to eliminate "hallucinations" in the routing phase where the LLM suggests folder names that do not exist or are not allowed for the given document category.

## Canonical References
- .planning/ROADMAP.md
- .planning/REQUIREMENTS.md
- src/processing/routing/config.py (Source of truth for folder mappings)
- src/processing/routing/router.py (Current routing implementation)

## Decisions

### 1. Dynamic Literal Schema (Critical)
Instead of a static Pydantic model, the system will use `pydantic.create_model` to generate a **dynamic schema** for every routing request.
- The `selected_folder` field will be typed as a `Literal` containing only the folders allowed for the document's category.
- This ensures that validation happens at the parsing level; any response not matching the allowed list is rejected immediately by Pydantic.

### 2. Retry Loop with Feedback
The routing process will implement a strict 3-attempt limit:
- **Attempt 1**: Standard routing prompt.
- **Attempt 2 & 3**: If the previous attempt failed validation, the prompt will be updated to inform the LLM: *"This is a retry. Your previous response '[X]' was rejected because it was not in the allowed list. Please choose strictly from: [Allowed Folders]."*
- **Termination**: If the 3rd attempt also fails, the system will **throw a hard error and stop the pipeline**, preventing any mis-routed documents from being saved.

### 3. Single Source of Truth for Mappings
The dynamic `Literal` will be derived programmatically from the `FOLDER_ROUTING` dictionary in `src/processing/routing/config.py`. 

## Code Context
- **Reusable Assets**: The existing `FOLDER_ROUTING` and `CATEGORY_TO_FOLDERS` in `src/processing/routing/config.py` will be the primary inputs for the dynamic schema generation.
- **Patterns**: The retry loop will follow the resilience patterns established in `src/llm/llm.py` but with the added context-aware feedback for rejected responses.

## Deferred Ideas
- No deferred ideas for this phase.
