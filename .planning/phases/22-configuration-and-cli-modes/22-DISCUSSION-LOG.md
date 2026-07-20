# Phase 22: Configuration and CLI Modes - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-20T11:38:00+03:00
**Phase:** 22-configuration-and-cli-modes
**Areas discussed:** Configuration Structure, Directory Auto-creation, Create Boundaries, Append Concurrency

---

## Configuration Management & Precedence

| Option | Description | Selected |
|--------|-------------|----------|
| Replace .env | `config.yaml` fully replaces `.env` | |
| Path/Mappings Only | `config.yaml` manages paths/mappings, `.env` for API keys | ✓ |

**User's choice:** config.yaml doesn't replace .env. the .env is for the api keys. config.yaml handles all the paths and the mappings.
**Notes:** 

---

## Handling Missing Directories

| Option | Description | Selected |
|--------|-------------|----------|
| Fail fast | Error out and require manual directory creation | |
| Auto-create | Automatically `mkdir -p` the paths specified in config | ✓ |

**User's choice:** create the folders.
**Notes:** 

---

## `create <path>` Execution Boundaries

| Option | Description | Selected |
|--------|-------------|----------|
| Allow anywhere | `create` can run on any directory containing a PDF | |
| Strict Boundary | `create` `<path>` must be inside `areas_root_path` | ✓ |

**User's choice:** you need to be strict with the path. the user shouldn't be able to run it for any file whatsoever. it should be properly defined.
**Notes:** User clarified that `create` takes a raw PDF and generates the `.source_files/` directory, correcting an initial misunderstanding of the workflow.

---

## `append` Mode Concurrency

| Option | Description | Selected |
|--------|-------------|----------|
| Lock file | Use a `.inbox.lock` file to prevent multiple listeners | ✓ |
| No lock | Assume the user only runs one listener | |

**User's choice:** use the lock conditiion like you talked about.
**Notes:** 

---

## the agent's Discretion

CLI framework (argparse subcommands) and Pydantic configuration class structure were implicitly agreed upon based on codebase patterns.

## Deferred Ideas

- Actual FS-UI filename parsing and logic belongs to Phases 23 and 24.
