# Phase 92: Database Layer & Relational Schema — Context

## Goal
Implement a complete, production-grade SQLite database layer for the application that serves as the single source of truth for all areas, houses, tenants, batches, pages, and documents.

## Scope
- Implement SQLite schema DDL (areas, houses, tenants, batches, pages, documents) with WAL mode, foreign key enforcement, unique constraints, and performance indices.
- Build connection manager / session helper (`src/db/connection.py`).
- Define Pydantic / dataclass domain models (`src/db/models.py`).
- Implement Data Access Layer / Repository (`src/db/repository.py`) covering all CRUD operations.
- Full TDD coverage in `tests/db/test_schema.py` and `tests/db/test_repository.py`.
