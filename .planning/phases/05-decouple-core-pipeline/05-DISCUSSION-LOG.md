# Phase 5: decouple-core-pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-02T22:12:00+03:00
**Phase:** 05-decouple-core-pipeline
**Areas discussed:** Config Format, Legacy Logic Scripts, LLM Prompts

---

## Config Format

| Option | Description | Selected |
|--------|-------------|----------|
| Simple key-value mapping | Easiest for users, covers most cases | ✓ |
| Regex strings | More powerful, but harder to write and maintain | |
| Python expressions | Maximum power, but security risk and complex | |

**User's choice:** "what is the best according to the current method." -> "yes, fair enough."
**Notes:** User requested to match current method, which is simple key-value matching.

| Option | Description | Selected |
|--------|-------------|----------|
| Route to an "Uncategorized" folder | Safe fallback | ✓ |
| Drop/ignore the file | Risky, data loss | |
| Raise an error and stop the pipeline | Brittle | |

**User's choice:** "again, how does the current program do it?" -> "yes sir."
**Notes:** User confirmed using `fallback_folder` as the current program does.

| Option | Description | Selected |
|--------|-------------|----------|
| Max page limit and category sets | Easy to configure | ✓ |
| Python condition strings | More flexible, but harder to maintain | |
| We shouldn't make this configurable yet | Keep it hardcoded | |

**User's choice:** Max page limit and category sets

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, strict validation at startup | Catches errors early | ✓ |
| No, let the pipeline fail naturally | Frustrating for users | |
| Validate only routing paths | Partial validation | |

**User's choice:** Yes, strict validation at startup

---

## Legacy Logic Scripts

| Option | Description | Selected |
|--------|-------------|----------|
| In a dedicated 'scripts/' folder | Clearly separates core from custom | ✓ |
| As standalone modules inside 'src/' | Easier imports, but mixes core and custom logic | |
| Keep them in the original files | Messy | |

**User's choice:** In a dedicated 'scripts/' folder

| Option | Description | Selected |
|--------|-------------|----------|
| Pass the context to the script | Simple and functional | ✓ |
| The script modifies the pipeline state | More powerful, but can cause side effects | |
| Use a class-based plugin system | More structure, but over-engineered for now | |

**User's choice:** "why is a class based system overengineered." -> "keep it simple."
**Notes:** Decided on simple functional scripts matching current `organizer.py`.

| Option | Description | Selected |
|--------|-------------|----------|
| Catch exceptions, log them, use default | | ✓ |
| Let the pipeline crash with a traceback | | |
| Silently ignore and continue | | |

**User's choice:** Catch exceptions, log them, and use a safe default

| Option | Description | Selected |
|--------|-------------|----------|
| Use a built-in strict default | e.g., standard sequential grouping | ✓ |
| Skip that heuristic entirely | | |
| Require a script path in the config | fail to start | |

**User's choice:** Use a built-in strict default

---

## LLM Prompts

| Option | Description | Selected |
|--------|-------------|----------|
| Simple string formatting | Easiest to read and write | ✓ |
| Jinja2 templates | More powerful, but requires learning Jinja | |
| Keep prompts in a separate text/markdown file | Cleaner config file, but multiple files to manage | |

**User's choice:** "how does the current program does it?" -> "yes sir."
**Notes:** Chose simple f-strings.

| Option | Description | Selected |
|--------|-------------|----------|
| Define them as a list of fields with name, type, and description | Dynamically builds the schema | ✓ |
| Write the raw JSON schema in the config | More verbose and error-prone | |
| Hardcode the fields in the pipeline | Prevents changing what gets extracted | |

**User's choice:** Define them as a list of fields with name, type, and description

| Option | Description | Selected |
|--------|-------------|----------|
| Define the allowed string values in the config | Map them to internal representations dynamically | ✓ |
| Remove the internal Enum | Just use raw strings everywhere | |
| Keep the Enum hardcoded | Only map predefined strings | |

**User's choice:** Define the allowed string values in the config and map them to internal representations dynamically

| Option | Description | Selected |
|--------|-------------|----------|
| Externalize all prompts | Make the entire LLM layer fully configurable | ✓ |
| Only externalize the primary extraction prompt | Leave clustering hardcoded for now | |
| Keep all prompts hardcoded | Except for the categories list | |

**User's choice:** Externalize all prompts

---

## the agent's Discretion

None

## Deferred Ideas

None
