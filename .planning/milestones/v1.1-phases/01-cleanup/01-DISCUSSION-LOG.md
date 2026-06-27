# Phase 01 Discussion Log: Cleanup

## Area: Pruning aggressiveness
**Options presented:**
- Aggressive — Delete all unused helper functions, imports, and variables along with the local model code.
- Conservative — Only remove the main local model classes/functions and leave the helpers for now.

**Selected:** Aggressive — Delete all unused helper functions, imports, and variables along with the local model code.

## Area: Configuration cleanup
**Options presented:**
- Yes — Completely remove them from all environment files, templates, and config schemas.
- No — Keep them commented out or deprecated just in case.

**Selected:** Yes — Completely remove them from all environment files, templates, and config schemas.

## Area: Code preservation
**Options presented:**
- Rely on Git history — Just delete the code, it's saved in the commit history if we need it.
- Create an archive — Move the local model code to a temporary archive/scratch folder before deleting it from the main source.

**Selected:** Rely on Git history — Just delete the code, it's saved in the commit history if we need it.
