# Plan: Trailing Omission

## Objective
Implement the "Trailing Omission" feature for filename parsing in `src/inbox/parser.py`, allowing users to drop trailing `U`s.

## Steps
1. Remove `if len(tokens) < 5: raise ValueError(...)` in `src/inbox/parser.py`.
2. Update the group index parsing logic to fallback safely if no valid group token is found, setting remaining fields to default values ('U' or empty strings).
3. Update unit tests in `test_parser.py` to:
   - Remove assertions that expect errors on few tokens.
   - Add new assertions for trailing omitted tokens.
   - Update invalid group token test to assert fallback behavior instead of an error.
4. Run all tests to ensure correctness.
5. Create summary and update state.
