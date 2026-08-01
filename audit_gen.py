import re
import datetime

reqs = []
with open('.planning/REQUIREMENTS.md', 'r') as f:
    for line in f:
        m = re.match(r'- \[ \] \*\*(.*?)\*\*: (.*)', line.strip())
        if m:
            reqs.append({"id": m.group(1), "desc": m.group(2)})

phase_map = {
    "STATE": "30",
    "VAULT": "31",
    "LNK": "31",
    "TIMELINE": "32",
    "RECON": "33",
    "PREPEND": "34",
    "MIGRATE": "35"
}

yaml_lines = [
    "---",
    "milestone: v5.0",
    f"audited: {datetime.datetime.now().isoformat()}",
    "status: gaps_found",
    "scores:",
    "  requirements: 0/30",
    "  phases: 1/6",
    "  integration: 0/0",
    "  flows: 0/0",
    "gaps:",
    "  requirements:"
]

for r in reqs:
    phase = "unknown"
    for k, v in phase_map.items():
        if r['id'].startswith(k):
            phase = v
            break
            
    yaml_lines.extend([
        f"    - id: \"{r['id']}\"",
        f"      status: \"unsatisfied\"",
        f"      phase: \"{phase}\"",
        f"      claimed_by_plans: []",
        f"      completed_by_plans: []",
        f"      verification_status: \"missing\"",
        f"      evidence: \"Missing VERIFICATION.md or SUMMARY.md frontmatter for requirement.\""
    ])

yaml_lines.extend([
    "  integration:",
    "    - from: \"All phases\"",
    "      to: \"All phases\"",
    "      issue: \"Integration checker failed to execute. Needs manual validation.\"",
    "  flows: []",
    "tech_debt: []",
    "nyquist:",
    "  compliant_phases: []",
    "  partial_phases: []",
    "  missing_phases: [\"30\", \"31\", \"32\", \"33\", \"34\", \"35\"]",
    "  overall: \"missing\"",
    "---",
    "",
    "# Milestone v5.0 Audit Report",
    "",
    "## Requirements Summary",
    "0/30 requirements satisfied. All requirements are missing verification evidence.",
    "",
    "## Phase Verification",
    "Phases 31, 32, 33, 34, 35 are missing VERIFICATION.md.",
    "",
    "## Integration",
    "Integration checker failed to execute.",
    "",
    "## Tech Debt",
    "None logged."
])

with open('.planning/v5.0-MILESTONE-AUDIT.md', 'w') as f:
    f.write('\n'.join(yaml_lines) + '\n')

