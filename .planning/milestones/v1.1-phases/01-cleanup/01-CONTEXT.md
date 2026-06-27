# Phase 01 Context: Cleanup

## Domain
Phase 1 removes local model support and unused legacy code paths from the codebase to streamline it for the cloud-only approach.

## Decisions
- **Pruning aggressiveness**: Aggressive — Delete all unused helper functions, imports, and variables along with the local model code.
- **Configuration cleanup**: Completely remove all local model related environment variables from `.env` files, templates, and config schemas.
- **Code preservation**: Rely on Git history — Just delete the code from the main source, it's saved in the commit history if we ever need it.

## Canonical Refs
- [.planning/ROADMAP.md](../../ROADMAP.md)
- [.planning/REQUIREMENTS.md](../../REQUIREMENTS.md)
- [.planning/PROJECT.md](../../PROJECT.md)
