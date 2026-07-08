---
wave: 1
depends_on: []
files_modified:
  - src/core/exceptions.py
  - src/organize.py
  - src/logger.py
  - src/processing/split.py
autonomous: true
---

# Plan: Exceptions and sys.exit Refactoring

## Requirements
- REF-03

## Context
Remove deep `sys.exit` calls and swallowed bare exceptions to improve error propagation and logging.

## Tasks

<task>
<read_first>
- src/organize.py
- src/logger.py
- src/processing/split.py
</read_first>
<action>
Create a new file `src/core/exceptions.py`. Define a base custom exception `FileOrganizerError` that inherits from `Exception`. Define subclasses `ConfigurationError` and `ValidationError`.
</action>
<acceptance_criteria>
- `src/core/exceptions.py` exists and contains `FileOrganizerError`, `ConfigurationError`, and `ValidationError`.
</acceptance_criteria>
</task>

<task>
<read_first>
- src/organize.py
- src/core/exceptions.py
</read_first>
<action>
Modify `src/organize.py`. Update `validate_environment()` to raise `ConfigurationError` instead of calling `sys.exit(1)`. Update `validate_target_directory()` to raise `ValidationError` instead of calling `sys.exit(1)`. In `main()`, wrap the execution in a try/except block that catches `FileOrganizerError` (which must inherit from `Exception`) and `Exception`. When caught, log the error using `logger.error` while preserving the checkpoint state (do not delete or overwrite checkpoint files on failure), and return a non-zero exit code.
</action>
<acceptance_criteria>
- `src/organize.py` no longer contains any `sys.exit(1)` inside the validation functions.
- `main()` handles the exceptions gracefully.
- The top-level try/except logs the error and ensures checkpoint files are preserved if a failure occurs mid-pipeline.
</acceptance_criteria>
</task>

<task>
<read_first>
- src/logger.py
- src/processing/split.py
</read_first>
<action>
Fix swallowed exceptions:
1. In `src/logger.py`, change `except Exception:` near `sys.stdout.reconfigure` to `except (AttributeError, OSError) as e:` and optionally log it at DEBUG level.
2. In `src/processing/split.py`, change the bare `except:` in the `compress_pdf` cleanup block to `except OSError:` or similar, and remove any `except Exception:` that just passes silently without logging the error.
</action>
<acceptance_criteria>
- No `except Exception:` with `pass` exists in `src/logger.py` or `src/processing/split.py`.
- No bare `except:` exists in `src/processing/split.py`.
</acceptance_criteria>
</task>

## Artifacts this phase produces
- `src/core/exceptions.py` file
- `FileOrganizerError` exception class
- `ConfigurationError` exception class
- `ValidationError` exception class

## Must Haves
### truths
- D-03: Implement a custom exception hierarchy to replace deep sys.exit calls and swallowed exceptions.
- Validation functions in `src/organize.py` raise exceptions rather than exiting the process directly.
- The pipeline handles errors gracefully at the top level.

### prohibitions
- No bare `except:` blocks are allowed in `src/processing/split.py`.
- No `sys.exit(1)` is allowed outside the `main` block.
