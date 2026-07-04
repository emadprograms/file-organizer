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
| GRP-01 | Category pre-split produces boundaries at every category change | unit | `python -m pytest tests/test_grouping.py::test_category_presplit -x` | ❌ Wave 0 |
| GRP-02 | Overlapping chunks generated correctly (1-10, 10-20, etc.) | unit | `python -m pytest tests/test_grouping.py::test_chunk_generator_overlap -x` | ❌ Wave 0 |
| GRP-03 | LLM prompt enforces subject-only boundaries (mock LLM) | unit | `python -m pytest tests/test_grouping.py::test_boundary_signals -x` | ❌ Wave 0 |
| GRP-04 | LLM response includes reasoning field | unit | `python -m pytest tests/test_grouping.py::test_response_has_reasoning -x` | ❌ Wave 0 |
| GRP-05 | LLM response validates against GroupingResponse schema | unit | `python -m pytest tests/test_grouping.py::test_schema_validation -x` | ❌ Wave 0 |
| GRP-06 | Verification catches gaps, overlaps, invented pages | unit | `python -m pytest tests/test_grouping.py::test_verification_logic -x` | ❌ Wave 0 |
| GRP-07 | Overlap merge joins groups sharing overlap page | unit | `python -m pytest tests/test_grouping.py::test_overlap_merge -x` | ❌ Wave 0 |
| GRP-08 | Routing dict maps categories to correct folders | unit | `python -m pytest tests/test_routing.py::test_routing_dict -x` | ❌ Wave 0 |
| GRP-09 | Single-match categories route without LLM | unit | `python -m pytest tests/test_routing.py::test_single_match_direct -x` | ❌ Wave 0 |
| GRP-10 | Multi-match categories use LLM with retry/fallback | unit | `python -m pytest tests/test_routing.py::test_multi_match_llm -x` | ❌ Wave 0 |
| GRP-11 | PDF split produces correct page ranges | integration | `python -m pytest tests/test_split.py -x` | ✅ Exists |
| GRP-12 | Filename follows `YYYY-MM-DD - عنوان.pdf` format | unit | `python -m pytest tests/test_routing.py::test_filename_format -x` | ❌ Wave 0 |
| GRP-13 | Dateless documents use inferred date | unit | `python -m pytest tests/test_routing.py::test_dateless_filename -x` | ❌ Wave 0 |

## Sampling Rate
- **Per task commit:** `python -m pytest tests/test_grouping.py tests/test_routing.py -x -q`
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

## Wave 0 Gaps
- [ ] `tests/test_grouping.py` — covers GRP-01 through GRP-07 (chunk generation, verification, merge)
- [ ] `tests/test_routing.py` — covers GRP-08 through GRP-10, GRP-12, GRP-13 (routing, naming)
- [ ] Fixtures: mock `PageData` objects with category/date/tenant, mock `LLMClient` responses
