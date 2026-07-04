# Phase 03: Pass 2 — Grouping & Routing - Validation Architecture

## Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already installed, used across 15+ test files) |
| Config file | None explicit — pytest auto-discovers `tests/` directory |
| Quick run command | `python -m pytest tests/test_pipeline.py -x -q` |
| Full suite command | `python -m pytest tests/ -x -q` |

## Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GRP-01 | Category pre-split produces boundaries at every category change | unit | `python -m pytest tests/test_grouping.py::test_category_presplit -x` | ✅ Exists |
| GRP-02 | Overlapping chunks generated correctly (1-10, 10-20, etc.) | unit | `python -m pytest tests/test_grouping.py::test_chunk_generator_overlap -x` | ✅ Exists |
| GRP-03 | LLM prompt enforces subject-only boundaries (mock LLM) | unit | `python -m pytest tests/test_grouping.py::test_boundary_signals -x` | ✅ Exists |
| GRP-04 | LLM response includes reasoning field | unit | `python -m pytest tests/test_grouping.py::test_response_has_reasoning -x` | ✅ Exists |
| GRP-05 | LLM response validates against GroupingResponse schema | unit | `python -m pytest tests/test_grouping.py::test_schema_validation -x` | ✅ Exists |
| GRP-06 | Verification catches gaps, overlaps, invented pages | unit | `python -m pytest tests/test_grouping.py::test_verification_logic -x` | ✅ Exists |
| GRP-07 | Overlap merge joins groups sharing overlap page | unit | `python -m pytest tests/test_grouping.py::test_overlap_merge -x` | ✅ Exists |
| GRP-08 | Routing dict maps categories to correct folders | unit | `python -m pytest tests/test_routing.py::test_routing_dict -x` | ✅ Exists |
| GRP-09 | Single-match categories route without LLM | unit | `python -m pytest tests/test_routing.py::test_single_match_direct -x` | ✅ Exists |
| GRP-10 | Multi-match categories use LLM with retry/fallback | unit | `python -m pytest tests/test_routing.py::test_multi_match_llm -x` | ✅ Exists |
| GRP-11 | PDF split produces correct page ranges | integration | `python -m pytest tests/test_split.py -x` | ✅ Exists |
| GRP-12 | Filename follows `YYYY-MM-DD - عنوان.pdf` format | unit | `python -m pytest tests/test_routing.py::test_filename_format -x` | ✅ Exists |
| GRP-13 | Dateless documents use inferred date | unit | `python -m pytest tests/test_routing.py::test_dateless_filename -x` | ✅ Exists |

## Sampling Rate
- **Per task commit:** `python -m pytest tests/test_grouping.py tests/test_routing.py -x -q`
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

## Validation Audit 2026-07-04
| Metric | Count |
|--------|-------|
| Gaps found | 6 |
| Resolved | 6 |
| Escalated | 0 |

## Validation Audit 2026-07-04 (Follow-up)
| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

## Validation Audit 2026-07-04 (Final)
| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
