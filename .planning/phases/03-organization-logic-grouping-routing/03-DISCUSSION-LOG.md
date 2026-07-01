# Phase 3: Organization Logic (Grouping & Routing) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-01
**Phase:** 03-Organization Logic (Grouping & Routing)
**Areas discussed:** Grouping Boundaries, Routing Strategy, Orphan/Unknown Handling

---

## Grouping Boundaries

| Option | Description | Selected |
|--------|-------------|----------|
| Both simple `group_by` fields AND an optional Python script | Recommended approach matching hybrid cleaning phase | ✓ |
| Simple `group_by` fields only | Keep it purely declarative | |
| Python script only | Maximum flexibility, no built-in field matching | |

**User's choice:** Both simple `group_by` fields AND an optional Python script
**Notes:** User initially asked how the current code did it, we explained the 'wall' and LLM semantic split, and then user chose the hybrid approach.

---

## Routing Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Template strings AND an optional Python script | Recommended hybrid approach | ✓ |
| Conditional routing blocks in YAML | Define if/else routing rules directly in config without Python | |
| Python script only | Maximum flexibility, no templates | |
| Template strings only | Keep it simple | |

**User's choice:** Template strings AND an optional Python script
**Notes:** User asked how the current code did it, we explained the complex conditionals, user then asked why not YAML conditionals, we explained the YAML programming language anti-pattern, and they chose the hybrid approach.

---

## Orphan/Unknown Handling

| Option | Description | Selected |
|--------|-------------|----------|
| `fallback_folder` path in the config | Recommended. Simple path for unmatched. | ✓ |
| `unmatched_strategy` enum | 'fallback_folder', 'drop', 'root' | |
| Hardcode "UNKNOWN" folder | Hardcode fallback path | |
| Drop them | If they don't match, drop them | |

**User's choice:** Let the user define a `fallback_folder` path in the config.
**Notes:** 

---

## the agent's Discretion

Schema implementation details.

## Deferred Ideas

None.
