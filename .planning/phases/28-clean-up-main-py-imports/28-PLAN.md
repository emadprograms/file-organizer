---
wave: 1
depends_on: []
files_modified:
  - src/main.py
autonomous: true
---

# Phase 28: Clean Up `main.py` Dead Imports Plan

## Goal
Remove dead imports from `main.py`.

## Requirements Covered
- **ARCH-04**: Clean Up `main.py` Dead Imports

<threat_model>
ASVS Level: 1
Blocking Threshold: Low
Threats: Accidental removal of used imports.
Mitigations: Code inspection and test validation.
</threat_model>

## Tasks
1. Remove `import fitz` and `import json` from `src/main.py`.
2. Verify test suite.
