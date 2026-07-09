# Phase 10: Chunk State Management - Validation

This document serves as the ground truth for the success of Phase 10. Every requirement must be mapped to a passing automated test.

## Requirement Mapping

| Req ID | Requirement Description | Test Case / Verification Method | Status |
|--------|-------------------------|---------------------------------|--------|
| **GRP-01** | Dynamic Chunking [5, 3, 2] | `test_shrink_logic`: Mock LLMC to fail full rotation, verify `chunk_size_index` increments and size changes 5 $ightarrow$ 3 $ightarrow$ 2. | [ ] |
| **GRP-02** | Reset index on success | `test_reset_logic`: Trigger shrink to size 3, then process a successful chunk, verify `chunk_size_index` returns to 0 (size 5). | [ ] |
| **GRP-03** | Graceful Halt at size 2 | `test_graceful_halt`: Simulate rotation failure at chunk size 2, verify `GracefulHaltException` is raised and state is saved. | [ ] |
| **GRP-04** | LLM-validated Anchor Merging | `test_anchor_merge`: Mock LLM groups to simulate continuation vs. split at the overlap page, verify `merge_chunks` result. | [ ] |

## Resilience & Persistence Verification

| Capability | Verification Method | Status |
|------------|---------------------|--------|
| **Atomic State Save** | `test_grouping_state_persistence`: Verify state is saved to JSON and survives process termination. | [ ] |
| **Hard Halt Recovery** | `test_resume_from_state`: Start grouping $ightarrow$ Force Exit $ightarrow$ Restart $ightarrow$ Verify `current_page_index` and `failure_count` are recovered. | [ ] |
| **Pydantic Validation** | `test_state_schema_validation`: Provide malformed JSON state file, verify system handles it gracefully (e.g., resets to default). | [ ] |

## Final Sign-off
- [ ] All `tests/test_grouping.py` pass.
- [ ] `VALIDATION.md` requirements are all marked [x].
- [ ] `GroupingStateManager` is verified atomic.
