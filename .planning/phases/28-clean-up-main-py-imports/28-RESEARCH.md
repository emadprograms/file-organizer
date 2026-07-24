# Phase 28: Clean Up `main.py` Dead Imports - Research

**Date:** 2026-07-24
**Status:** Completed
**Domain:** Architectural Cleanup (ARCH-04)

## Executive Summary
Phase 28 removes the dead `fitz` and `json` imports from `src/main.py` left over after the runner extraction refactor.

## Audit Results
- Searched `src/main.py` for `fitz`: only the `import fitz` statement existed.
- Searched `src/main.py` for `json`: only the `import json` statement existed; all other uses of `json` were in variable names or string literals (e.g., `json_files`, `*_report*.json`).
- Removing these two lines leaves `src/main.py` functionally identical but cleaner.
