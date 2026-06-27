# Phase 02 Context: Key Mgmt

## Domain
Simplify API key loading, tracking, and fallback configuration to establish a unified and strictly validated environment.

## Decisions
- **Key Management**: Use a single `GEMINI_API_KEY`. Create a tracking directory with a permanent file to log the timestamp of every successful call. Limit: 1500 calls per 24 hours. At startup, calculate and display the remaining quota.
- **Rate Limiting & Retries**: Process pages sequentially. Enforce a strict minimum of 7 seconds per call (sleep if finished faster). On a `429` error, wait 65 seconds before retrying. On a `500` or `503` error, wait 15 seconds.
- **Environment Configuration**: Centralize key loading and validation into a new `config.py` module, which loads at startup.
- **Missing Keys Behavior**: Fail fast. `config.py` must require ALL keys (`GEMINI_API_KEY`, `OPENROUTER_API_KEY`, `GROQ_API_KEY`) to be present at startup. If any are missing, the application halts immediately to ensure clean downstream logic (no `None` checks needed).

## Canonical Refs
- [.planning/ROADMAP.md](../../ROADMAP.md)
- [.planning/REQUIREMENTS.md](../../REQUIREMENTS.md)
- [.planning/PROJECT.md](../../PROJECT.md)
