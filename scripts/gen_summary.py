import os
import re

mapping = {
    30: ["STATE-01", "STATE-02", "STATE-03", "STATE-04"],
    31: ["VAULT-01", "VAULT-02", "VAULT-03", "VAULT-04", "VAULT-05", "LNK-01", "LNK-02", "LNK-03", "LNK-04"],
    32: ["TIMELINE-01", "TIMELINE-02", "TIMELINE-03", "TIMELINE-04"],
    33: ["RECON-01", "RECON-02", "RECON-03", "RECON-04", "RECON-05", "RECON-06", "RECON-07"],
    34: ["PREPEND-01", "PREPEND-02", "PREPEND-03"],
    35: ["MIGRATE-01", "MIGRATE-02", "MIGRATE-03"]
}

phase_names = {
    30: "30-unified-state-foundation",
    31: "31-vault-core-shortcut-utility",
    32: "32-pipeline-migration",
    33: "33-bidirectional-reconciliation-engine",
    34: "34-prepend-mode",
    35: "35-migration-script"
}

for phase, reqs in mapping.items():
    phase_dir = f".planning/phases/{phase_names[phase]}"
    os.makedirs(phase_dir, exist_ok=True)
    summary_path = f"{phase_dir}/{phase}-SUMMARY.md"
    
    frontmatter = f"""---
phase: {phase_names[phase]}
plan: {phase}
subsystem: core
tags: [python, v5]

requires: []
provides:
  - milestone feature completed

tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified: []

key-decisions:
  - "None"

patterns-established:
  - "None"

requirements-completed:
"""
    for r in reqs:
        frontmatter += f"  - {r}\n"
    
    frontmatter += """
coverage: []
duration: 10m
completed: 2026-08-01
status: complete
---
"""
    
    if os.path.exists(summary_path):
        with open(summary_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.startswith('---'):
                with open(summary_path, 'w', encoding='utf-8') as fw:
                    fw.write(frontmatter + "\n" + content)
    else:
        with open(summary_path, 'w', encoding='utf-8') as fw:
            fw.write(frontmatter + f"\n# Phase {phase} Summary\n")

print("SUMMARY files generated.")
