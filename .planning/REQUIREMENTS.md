# Milestone v17.0 Requirements: User Authentication, Roles & Permissions

## Requirements

### Authentication & User Store (AUTH)

- [x] **AUTH-01**: SQLite database schema includes `users` table (`id INTEGER PRIMARY KEY`, `username TEXT UNIQUE NOT NULL`, `display_name TEXT NOT NULL`, `password_hash TEXT NOT NULL`, `salt TEXT NOT NULL`, `role TEXT NOT NULL`, `created_at TEXT NOT NULL`, `is_active INTEGER NOT NULL DEFAULT 1`) with idempotent migration in `DatabaseInitializer.cs`.
- [x] **AUTH-02**: System automatically seeds 10 predefined users on startup:
  - Full Access (Admin): `Emad`, `Bubshait`, `Ehtezaz`, `Mustafa`
  - Read & Upload Only (Contributor): `Nawaf`, `Naseem`, `Mulla`, `Mariam`, `Shaima`, `Mona`
  - Passwords securely hashed with unique cryptographic salt.
- [x] **AUTH-03**: Secure session and cookie-based authentication:
  - `POST /api/auth/login`: verifies username and password, generates auth cookie/session, returns user details.
  - `POST /api/auth/logout`: terminates session and clears cookie.
  - `GET /api/auth/me`: returns authenticated user profile (`username`, `displayName`, `role`, `canDelete: boolean`) or 401 Unauthorized.
- [x] **AUTH-04**: Fast login switch/preset support for development & multi-user workstation environments.

### Role-Based Access Control & Backend Protection (RBAC)

- [x] **RBAC-01**: Single document deletion (`DELETE /api/areas/{area}/houses/{house}/documents/{vault_id}`) strictly requires `Admin` role; returns `403 Forbidden` if requested by `Contributor`.
- [x] **RBAC-02**: Batch document deletion (`POST /api/areas/{area}/houses/{house}/documents/batch-delete`) strictly requires `Admin` role; returns `403 Forbidden` if requested by `Contributor`.
- [x] **RBAC-03**: Document page editor deletion (`POST /api/areas/{area}/houses/{house}/documents/{vault_id}/delete-pages`) strictly requires `Admin` role; returns `403 Forbidden` if requested by `Contributor`.
- [x] **RBAC-04**: House deletion (`DELETE /api/areas/{area}/houses/{house}`) strictly requires `Admin` role; returns `403 Forbidden` if requested by `Contributor`.

### UI Authentication & Session Controls (UI)

- [x] **UI-01**: Dedicated bilingual (Arabic/English) Login Screen (`#login-screen`):
  - Card-based UI matching existing eye-comfort and dark mode themes.
  - Quick-switch user avatar selector + password input.
  - Error alert for invalid credentials or disabled accounts.
- [x] **UI-02**: Top navbar integration displaying active logged-in user:
  - User avatar with initials or icon.
  - User display name and distinctive role badge (`صلاحيات كاملة • Full Access` vs `قراءة ورفع فقط • Read & Upload`).
- [x] **UI-03**: Top navbar Logout button with confirmation or instant execution, immediately returning user to the login screen and resetting app state.

### Permission-Aware UI Masking (PERM)

- [x] **PERM-01**: In Categories view and Timeline view, the 3-dots document action menu hides or disables the "Delete Document" (`.doc-menu-item-delete`) action for Contributor users.
- [x] **PERM-02**: In Categories view, multi-select floating action dock (`#batch-action-bar`) hides the "Delete Selected" button for Contributor users.
- [x] **PERM-03**: In Document Page Editor (`doc-page-editor.js`), single page 1-tap delete buttons and "Delete Selected Pages" action buttons are hidden/disabled for Contributor users.
- [x] **PERM-04**: In House Settings modal (`#tenant-modal`), the "Danger Zone" / "Delete House" section is completely hidden from Contributor users.

### Verification & Testing (VER)

- [x] **VER-01**: Backend xUnit tests in `tests/HousingApplication.Tests/` validating user repository, password hashing, seeding of 10 users, login/logout endpoints, and 403 Forbidden enforcement on all delete endpoints.
- [x] **VER-02**: Frontend Vitest tests in `tests/web/components/` validating login UI, session state management, role badge rendering, and UI delete masking for Contributor vs Admin.
- [x] **VER-03**: End-to-end milestone audit and 100% static asset synchronization between `src/HousingApplication.Web/wwwroot/` and `dist/win-x64/wwwroot/`.

## Traceability

| Requirement | Phase | Status |
|---|---|---|
| AUTH-01 | Phase 116 | Complete |
| AUTH-02 | Phase 116 | Complete |
| AUTH-03 | Phase 116 | Complete |
| AUTH-04 | Phase 116 | Complete |
| RBAC-01 | Phase 116 | Complete |
| RBAC-02 | Phase 116 | Complete |
| RBAC-03 | Phase 116 | Complete |
| RBAC-04 | Phase 116 | Complete |
| UI-01 | Phase 117 | Complete |
| UI-02 | Phase 117 | Complete |
| UI-03 | Phase 117 | Complete |
| PERM-01 | Phase 118 | Complete |
| PERM-02 | Phase 118 | Complete |
| PERM-03 | Phase 118 | Complete |
| PERM-04 | Phase 118 | Complete |
| VER-01 | Phase 116 | Complete |
| VER-02 | Phase 117, Phase 118 | Complete |
| VER-03 | Phase 119 | Complete |
