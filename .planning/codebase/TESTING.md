# Testing Strategy and Test Suite

This document describes the testing architecture, test organization, mocking strategies, and execution instructions for the `file-organizer` codebase.

---

## 1. Testing Philosophy & Overview

The test suite ensures reliability, determinism, and safety across all document processing operations:
- **349 Total Automated Tests**: Comprehensive coverage spanning unit logic, subsystem integrations, end-to-end flows, and compliance audits.
- **Hermetic Mocking**: External network services (Gemini/OpenRouter/Groq LLMs) and operating system dependencies (Windows COM shortcuts) are isolated and mocked to allow fully deterministic offline execution.
- **Architectural & Quality Compliance**: Automated tests enforce structural constraints, absence of legacy type hints, proper logger initialization, and prohibition of raw `print()` statements.
- **Fail-Safe Regression Verification**: Incremental phase regression test suites validate bug fixes and edge cases discovered during system migrations.

---

## 2. Test Framework & Configuration

- **Framework**: `pytest` (with `anyio`)
- **Root Fixtures**: [`tests/conftest.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/conftest.py) provides standard fixture definitions such as `mock_page_data_dict` and `mock_tenant_timeline_dict`.
- **Sandboxed IO**: Tests use pytest's built-in `tmp_path` fixture to dynamically generate isolated directories, state files, PDFs, and shortcut trees.
- **Live Test Skipping**: Tests requiring access to live external directories (`D:\Areas`) or active LLM credentials use `@pytest.mark.skipif` conditions (e.g. [`tests/test_live_e2e.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_live_e2e.py)).

---

## 3. Test Suite Inventory & Coverage Map

### Core & Configuration Tests
- [`tests/test_core_schemas.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_core_schemas.py): Validates `ParsedCommand`, `DocumentGroup`, `GroupEntry`, and `GroupingResponse` Pydantic models.
- [`tests/test_core_config_parsing.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_core_config_parsing.py): Validates `AppConfig` YAML loading, path resolution, and error raising on malformed YAML.
- [`tests/test_core_exceptions.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_core_exceptions.py): Ensures exception hierarchy integrity and inheritance from `FileOrganizerError`.
- [`tests/test_core_indexing.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_core_indexing.py): Tests area indexing, directory scanning, and house ID lookups.
- [`tests/test_state.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_state.py) & [`tests/test_state_runner.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_state_runner.py): Verifies atomic saving, loading, and migration of state files.

### Categorization Subsystem
- [`tests/test_categorization.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_categorization.py): Tests document classification passes, PDF image generation, and crash checkpoint recovery.
- [`tests/test_categorization_cat01.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_categorization_cat01.py): Verifies category 01 (Basic Info) classification rules.
- [`tests/test_categorization_continuation.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_categorization_continuation.py): Tests multi-page continuation detection.
- [`tests/test_categorization_gaps.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_categorization_gaps.py): Tests handling of unclassified or missing pages.
- [`tests/test_categorization_logic.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_categorization_logic.py): Tests category resolution rules and prompts.
- [`tests/test_fine_categorization.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_fine_categorization.py): Validates secondary fine-grained category disambiguation.

### Document Grouping Subsystem
- [`tests/test_grouping_core.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_grouping_core.py): Comprehensive boundary detection, window shrinking, and fallback tests.
- [`tests/test_grouping_core_contracts.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_grouping_core_contracts.py): Tests grouping rules for cohesive contract documents.
- [`tests/test_grouping_core_utility_bills.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_grouping_core_utility_bills.py): Tests grouping rules for monthly utility bill sequences.
- [`tests/test_grouping_core_precision_window.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_grouping_core_precision_window.py): Tests sliding window boundary refinements.
- [`tests/test_grouping_core_logic_config.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_grouping_core_logic_config.py): Tests grouping configuration heuristics.

### Routing Subsystem
- [`tests/test_routing_router.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_routing_router.py): Validates direct folder matching, category-to-folder constraints, and LLM selection.
- [`tests/test_routing_router_constrained_forms.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_routing_router_constrained_forms.py): Ensures forms are strictly constrained to valid form folders.
- [`tests/test_routing_router_constrained_letters.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_routing_router_constrained_letters.py): Ensures letters are constrained to letter folders.
- [`tests/test_routing_router_others_flow.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_routing_router_others_flow.py): Tests two-step verification for Miscellaneous/Others documents.
- [`tests/test_routing_router_escape_hatch.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_routing_router_escape_hatch.py): Verifies routing escape hatch when confidence is low.
- [`tests/test_routing_router_hallucination.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_routing_router_hallucination.py): Tests rejection and recovery when LLM selects non-existent folders.
- [`tests/test_routing_router_safety.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_routing_router_safety.py): Tests error halts on exhausted LLM retries and invalid schemas.
- [`tests/test_routing_router_finalization.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_routing_router_finalization.py): Tests shortcut generation and folder path formatting.

### Timeline, Dates & Page Integrity
- [`tests/test_timeline_cleaning.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_timeline_cleaning.py): Tests parsing Arabic, English, Hijri, and dual-calendar date formats; tests fuzzy name clustering.
- [`tests/test_timeline_arabic_numerals.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_timeline_arabic_numerals.py): Tests date parsing with Eastern Arabic numerals (٠-٩).
- [`tests/test_timeline_page_integrity.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_timeline_page_integrity.py): Verifies 1-to-1 page count preservation and anti-loss invariants.
- [`tests/test_timeline_core_edge_cases.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_timeline_core_edge_cases.py): Tests filename collision avoidance, unassigned tenants, and dry-run safety.

### LLM Client & Providers
- [`tests/test_llm_llm.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_llm_llm.py): Verifies structured response parsing and trace logging.
- [`tests/test_llm_llm_rate_limit.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_llm_llm_rate_limit.py): Tests rate-limit (HTTP 429) backoff and 65-second cooldown triggers.
- [`tests/test_llm_llm_resilience.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_llm_llm_resilience.py): Tests model rotation cascades and failovers.
- [`tests/test_llm_llm_critical_error.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_llm_llm_critical_error.py): Tests immediate halting on HTTP 401 Unauthorized.
- [`tests/test_llm_llm_failure_isolation.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_llm_llm_failure_isolation.py): Ensures provider failures don't leak unhandled exceptions.
- [`tests/test_llm_llm_skip_mocking.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_llm_llm_skip_mocking.py): Tests offline operation via `MockLLMProvider`.
- [`tests/test_llm_providers.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_llm_providers.py) & [`tests/test_providers.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_providers.py): Validates provider strategy interfaces.

### Reconciliation & Phase Regression Tests
- [`tests/test_reconcile_core.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_reconcile_core.py): Tests reconcile mode workflow, duplicate adoption, and ghost file tracking.
- [`tests/test_reconcile_bidirectional.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_reconcile_bidirectional.py): Tests synchronizing changes between disk and state JSON.
- [`tests/test_reconcile_phase43.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_reconcile_phase43.py) through [`tests/test_reconcile_phase57.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_reconcile_phase57.py): Targeted regression tests preserving fixes across phases (e.g., timeline folder renaming, duplicate shortcuts, orphan cleanup, ghost PDF recovery).

### Watcher & FS-UI Subsystem
- [`tests/test_watcher_lock.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_watcher_lock.py): Tests PID-based process locking and dead lock recovery.
- [`tests/test_watcher_orchestrator.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_watcher_orchestrator.py): Tests inbox monitoring, file stability delays, propose/finalize stages, and orphan cleanup.
- [`tests/test_watcher_prepend_mock.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_watcher_prepend_mock.py) & [`tests/test_finalize_prepend.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_finalize_prepend.py): Tests pre-pending operations and staging moves.

### PDF & Utility Operations
- [`tests/test_pdf_extract_compress.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_pdf_extract_compress.py): Tests PyMuPDF extraction boundaries and document compression.
- [`tests/test_pdf_extract_split.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_pdf_extract_split.py): Tests splitting PDF pages into individual documents.
- [`tests/test_utils_fs.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_utils_fs.py): Tests `atomic_write`, `merge_and_remove_dir`, and shortcut operations.
- [`tests/test_utils_logger.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_utils_logger.py): Tests log directory provisioning, JSONL formatting, decision traces, and log context singleton.

### Architectural & Compliance Audits
- [`tests/test_type_hint_compliance.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_type_hint_compliance.py): AST audit banning `typing.List` and `typing.Dict` across `src/` and `tests/`.
- [`tests/test_architecture_phase25.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_architecture_phase25.py): Validates that `src/core/` contains no UI code.
- [`tests/test_utils_logger_audit.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_utils_logger_audit.py): Ensures all loggers use `f"file_organizer.{__name__}"` and bans raw `print()` calls.
- [`tests/test_utils_telemetry_audit.py`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/tests/test_utils_telemetry_audit.py): Verifies no unmanaged console prints exist in `src/`.

---

## 4. Mocking & Fixture Strategies

### 1. Mocking LLM Clients & Providers
When testing modules that consume LLMs, use mock providers to return deterministic schema responses or simulate errors without network latency:
```python
class MockLLMClient:
    def __init__(self, responses=None):
        self.responses = responses or []
        self.call_count = 0
        
    def generate_content(self, contents, response_schema=None, **kwargs):
        resp = self.responses[self.call_count]
        self.call_count += 1
        if response_schema:
            return response_schema.model_validate(resp, context=kwargs.get('validation_context', {}))
        return resp
```

### 2. Mocking Rate Limit Delays
In tests exercising `LLMClient._route_llm_call`, always patch `time.sleep` or instantiate `LLMClient(delay_between_pages=0.0)` to avoid unintended inter-request sleeps:
```python
with patch("time.sleep") as mock_sleep:
    client._route_llm_call(...)
```

### 3. Mocking File System & Temporary Houses
Use `tmp_path` to construct the standard directory layout required by the pipeline and reconciliation engine:
```python
@pytest.fixture
def mock_house(tmp_path):
    house_dir = tmp_path / "123 - Test House"
    house_dir.mkdir()
    source_dir = house_dir / ".source_files"
    source_dir.mkdir()
    vault_dir = source_dir / "vault"
    vault_dir.mkdir()
    return house_dir
```

---

## 5. How to Run the Tests

### Run All Tests
```powershell
pytest
```

### Run Unit & Core Tests Quickly (excluding slow integration tests)
```powershell
pytest tests/test_core_*.py tests/test_routing_*.py tests/test_grouping_*.py tests/test_timeline_*.py
```

### Run Compliance & Architectural Audits
```powershell
pytest tests/test_type_hint_compliance.py tests/test_utils_logger_audit.py tests/test_utils_telemetry_audit.py tests/test_architecture_phase25.py
```

### Run with Verbose Output and Stop on First Failure
```powershell
pytest -v -x
```

### Run Specific Subsystem Tests
```powershell
# Routing tests
pytest tests/test_routing_*.py

# LLM resilience tests
pytest tests/test_llm_*.py

# Reconcile regression tests
pytest tests/test_reconcile_*.py

# Watcher orchestrator tests
pytest tests/test_watcher_*.py
```
