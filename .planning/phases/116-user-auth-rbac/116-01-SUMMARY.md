# Phase 116 Summary: User Data Model, Password Security & Auth API

## Executed Work
- **User Data Models**: Created `src/HousingApplication.Web/Models/User.cs` defining `User`, `UserDto`, `LoginRequestDto`, `LoginResponseDto`, and `AuthStatusResponseDto`.
- **Cryptographic Security**: Created `src/HousingApplication.Web/Common/PasswordHasher.cs` using PBKDF2 (HMAC-SHA256, 10,000 iterations, 16-byte random salt, constant-time verification, with default fallback support).
- **Database Initializer & Auto-Seeding**: Updated `DatabaseInitializer.cs` to create the `users` SQLite table with indexes and automatically seed all 10 users:
  - 4 Admins (Full Access): `Emad`, `Bubshait`, `Ehtezaz`, `Mustafa`
  - 6 Contributors (Read & Upload Only): `Nawaf`, `Naseem`, `Mulla`, `Mariam`, `Shaima`, `Mona`
- **Repository Integration**: Added `GetUserByUsernameAsync`, `GetUserByIdAsync`, and `GetAllUsersAsync` to `IFileOrganizerRepository` and `FileOrganizerRepository`.
- **Cookie Auth & Minimal APIs**:
  - Registered `AddAuthentication(CookieAuthenticationDefaults.AuthenticationScheme).AddCookie(...)` and `AddAuthorization()`.
  - Added `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`, and `GET /api/auth/users`.
  - Added role and permission claim handling (`role: Admin | Contributor`, `can_delete: true | false`).
- **RBAC Delete Guards**:
  - Implemented `IsRestrictedFromDelete(HttpContext context)` checking claims and headers (`X-User-Role`, `X-User`).
  - Protected `DELETE /api/documents/{vaultId}`, `POST /api/documents/batch-delete`, `DELETE /api/documents/{vaultId}/pages/{pageNumber}`, `DELETE /api/houses/{houseId}`, and category deletions with `403 Forbidden` (`{"error": "Forbidden: Contributors do not have permission to delete documents or resources."}`).
- **Verification**: Created `tests/HousingApplication.Tests/AuthAndRbacTests.cs` covering all scenarios. All 10/10 tests pass, and full test suite passes with 970/970 tests.
