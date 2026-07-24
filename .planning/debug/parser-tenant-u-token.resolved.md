# Debug Session: Parser Misidentifying Tenant 'U' as Group 'U'

## Status
Resolved

## Symptoms
When a user provides a filename containing `U` as a tenant placeholder (e.g., `SAFC 1273 U G 2026-06-25`), the parser misidentifies the first `U` it encounters as the Group token instead of the Tenant token. 
This causes a misalignment in the extracted tokens, causing the actual Group token (e.g. `G` or `7`) to be skipped or misidentified as the Date/Title, and skipping the appropriate routing logic.

## Context & Root Cause
In `src/inbox/parser.py`, the `parse_filename_syntax` function scans the tokens sequentially from left to right. It checks if a token is a valid Group token (which includes `1-13`, `G`, and `U`). Because `U` is a valid value for both Tenant and Group, the greedy left-to-right scanning immediately claims the first `U` it sees as the Group token, rather than recognizing it as the Tenant. 

A previous attempt to fix this with look-ahead logic caused regressions because it incorrectly enforced that any valid group MUST be immediately followed by a valid Date token. When filenames lacked a valid date token (e.g. they only had a Title string), the parser rejected valid group tokens entirely and threw a `ValueError`.

## Resolution
The fragile date-validation look-ahead was removed. A simpler, structurally sound logic was implemented:
- When scanning, if the parser encounters a `U` that is the **very first token** after the house number, it looks at the **next** token.
- If the next token is *also* a valid group (like `G`, `5`, or another `U`), it skips the first `U` (allocating it as the Tenant placeholder) and correctly identifies the next one as the Group.
- This accurately resolves the ambiguous `U` scenario without making assumptions about how the Date or Title tokens are formatted.

Tests were added to `tests/test_parser.py` (`test_parse_filename_syntax_ambiguous_u`) to guarantee this logic does not regress in the future.
