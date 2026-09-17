using Microsoft.Data.Sqlite;
using Dapper;

namespace FileOrganizer.Web.Data;

public static class DatabaseInitializer
{
    public const string SchemaSql = @"
CREATE TABLE IF NOT EXISTS areas (
    id TEXT PRIMARY KEY,
    code TEXT
);

CREATE TABLE IF NOT EXISTS houses (
    id TEXT PRIMARY KEY,
    area_id TEXT NOT NULL REFERENCES areas(id)
);

CREATE TABLE IF NOT EXISTS tenants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    house_id TEXT NOT NULL REFERENCES houses(id),
    name TEXT NOT NULL,
    start_date DATE,
    end_date DATE,
    is_resident INTEGER NOT NULL DEFAULT 1,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    house_id TEXT NOT NULL REFERENCES houses(id),
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    page_count INTEGER NOT NULL,
    status TEXT DEFAULT 'completed',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
    vault_id TEXT PRIMARY KEY,
    house_id TEXT NOT NULL REFERENCES houses(id),
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    batch_id INTEGER NOT NULL REFERENCES batches(id),
    primary_date DATE,
    arabic_title TEXT,
    category TEXT,
    page_count INTEGER DEFAULT 1,
    is_manual INTEGER DEFAULT 0,
    notes TEXT,
    is_timeline_visible INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    house_id TEXT NOT NULL REFERENCES houses(id),
    category TEXT,
    content_explanation TEXT,
    expected_tenant_name TEXT,
    expected_house_number TEXT,
    raw_date TEXT,
    sender TEXT,
    receiver TEXT,
    subject TEXT,
    is_continuation BOOLEAN DEFAULT 0,
    tenant_id INTEGER REFERENCES tenants(id),
    resolved_date DATE,
    fine_category TEXT,
    fine_category_reason TEXT,
    vault_id TEXT REFERENCES documents(vault_id),
    UNIQUE(batch_id, page_number)
);

CREATE INDEX IF NOT EXISTS idx_houses_area ON houses(area_id);
CREATE INDEX IF NOT EXISTS idx_tenants_house ON tenants(house_id);
CREATE INDEX IF NOT EXISTS idx_batches_house ON batches(house_id);
CREATE INDEX IF NOT EXISTS idx_pages_batch ON pages(batch_id);
CREATE INDEX IF NOT EXISTS idx_pages_house ON pages(house_id);
CREATE INDEX IF NOT EXISTS idx_documents_house ON documents(house_id);
CREATE INDEX IF NOT EXISTS idx_documents_tenant ON documents(tenant_id);
CREATE INDEX IF NOT EXISTS idx_documents_date ON documents(primary_date);
CREATE INDEX IF NOT EXISTS idx_documents_manual ON documents(is_manual);
CREATE INDEX IF NOT EXISTS idx_pages_vault ON pages(vault_id);
CREATE INDEX IF NOT EXISTS idx_documents_house_cat ON documents(house_id, category);
CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);
CREATE INDEX IF NOT EXISTS idx_documents_title ON documents(arabic_title);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
";

    public static void InitializeSchema(SqliteConnection connection)
    {
        try
        {
            using var cmd = connection.CreateCommand();
            cmd.CommandText = SchemaSql;
            cmd.ExecuteNonQuery();
        }
        catch (SqliteException) { }

        try
        {
            using var alterCmd = connection.CreateCommand();
            alterCmd.CommandText = "ALTER TABLE documents ADD COLUMN is_timeline_visible INTEGER DEFAULT 1;";
            alterCmd.ExecuteNonQuery();
        }
        catch (SqliteException) { }

        try
        {
            using var idxCmd = connection.CreateCommand();
            idxCmd.CommandText = "CREATE INDEX IF NOT EXISTS idx_documents_timeline ON documents(is_timeline_visible);";
            idxCmd.ExecuteNonQuery();
        }
        catch (SqliteException) { }

        try
        {
            using var alterCmd = connection.CreateCommand();
            alterCmd.CommandText = "ALTER TABLE tenants ADD COLUMN is_resident INTEGER NOT NULL DEFAULT 1;";
            alterCmd.ExecuteNonQuery();
        }
        catch (SqliteException) { }

        try
        {
            using var alterCmd = connection.CreateCommand();
            alterCmd.CommandText = "ALTER TABLE tenants ADD COLUMN notes TEXT;";
            alterCmd.ExecuteNonQuery();
        }
        catch (SqliteException) { }

        try
        {
            using var idxCmd = connection.CreateCommand();
            idxCmd.CommandText = "CREATE INDEX IF NOT EXISTS idx_tenants_resident ON tenants(is_resident);";
            idxCmd.ExecuteNonQuery();
        }
        catch (SqliteException) { }

        EnsureTenantStartDateNullable(connection);
        EnsureUsersSeeded(connection);
    }

    public static async Task InitializeSchemaAsync(SqliteConnection connection)
    {
        try
        {
            using var cmd = connection.CreateCommand();
            cmd.CommandText = SchemaSql;
            await cmd.ExecuteNonQueryAsync();
        }
        catch (SqliteException) { }

        try
        {
            using var alterCmd = connection.CreateCommand();
            alterCmd.CommandText = "ALTER TABLE documents ADD COLUMN is_timeline_visible INTEGER DEFAULT 1;";
            await alterCmd.ExecuteNonQueryAsync();
        }
        catch (SqliteException) { }

        try
        {
            using var idxCmd = connection.CreateCommand();
            idxCmd.CommandText = "CREATE INDEX IF NOT EXISTS idx_documents_timeline ON documents(is_timeline_visible);";
            await idxCmd.ExecuteNonQueryAsync();
        }
        catch (SqliteException) { }

        try
        {
            using var alterCmd = connection.CreateCommand();
            alterCmd.CommandText = "ALTER TABLE tenants ADD COLUMN is_resident INTEGER NOT NULL DEFAULT 1;";
            await alterCmd.ExecuteNonQueryAsync();
        }
        catch (SqliteException) { }

        try
        {
            using var alterCmd = connection.CreateCommand();
            alterCmd.CommandText = "ALTER TABLE tenants ADD COLUMN notes TEXT;";
            await alterCmd.ExecuteNonQueryAsync();
        }
        catch (SqliteException) { }

        try
        {
            using var idxCmd = connection.CreateCommand();
            idxCmd.CommandText = "CREATE INDEX IF NOT EXISTS idx_tenants_resident ON tenants(is_resident);";
            await idxCmd.ExecuteNonQueryAsync();
        }
        catch (SqliteException) { }

        await EnsureTenantStartDateNullableAsync(connection);
        await EnsureUsersSeededAsync(connection);
    }

    public static readonly (string Username, string DisplayName, string Role)[] DefaultUsers = new[]
    {
        ("Emad", "Emad", "Admin"),
        ("Bubshait", "Bubshait", "Admin"),
        ("Ehtezaz", "Ehtezaz", "Admin"),
        ("Mustafa", "Mustafa", "Admin"),
        ("Nawaf", "Nawaf", "Contributor"),
        ("Naseem", "Naseem", "Contributor"),
        ("Mulla", "Mulla", "Contributor"),
        ("Mariam", "Mariam", "Contributor"),
        ("Shaima", "Shaima", "Contributor"),
        ("Mona", "Mona", "Contributor")
    };

    public static void EnsureUsersSeeded(SqliteConnection connection)
    {
        try
        {
            using (var createCmd = connection.CreateCommand())
            {
                createCmd.CommandText = @"
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        display_name TEXT NOT NULL,
                        password_hash TEXT NOT NULL,
                        salt TEXT NOT NULL,
                        role TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        is_active INTEGER NOT NULL DEFAULT 1
                    );
                    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);";
                createCmd.ExecuteNonQuery();
            }

            foreach (var (username, displayName, role) in DefaultUsers)
            {
                using var checkCmd = connection.CreateCommand();
                checkCmd.CommandText = "SELECT COUNT(1) FROM users WHERE LOWER(username) = LOWER(@u);";
                checkCmd.Parameters.AddWithValue("@u", username);
                var exists = Convert.ToInt32(checkCmd.ExecuteScalar()) > 0;
                if (!exists)
                {
                    var (hash, salt) = Common.PasswordHasher.HashPassword($"{username.ToLower()}123");
                    using var insCmd = connection.CreateCommand();
                    insCmd.CommandText = @"
                        INSERT INTO users (username, display_name, password_hash, salt, role, is_active)
                        VALUES (@u, @d, @h, @s, @r, 1);";
                    insCmd.Parameters.AddWithValue("@u", username);
                    insCmd.Parameters.AddWithValue("@d", displayName);
                    insCmd.Parameters.AddWithValue("@h", hash);
                    insCmd.Parameters.AddWithValue("@s", salt);
                    insCmd.Parameters.AddWithValue("@r", role);
                    insCmd.ExecuteNonQuery();
                }
            }
        }
        catch (SqliteException) { }
    }

    public static async Task EnsureUsersSeededAsync(SqliteConnection connection)
    {
        try
        {
            using (var createCmd = connection.CreateCommand())
            {
                createCmd.CommandText = @"
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        display_name TEXT NOT NULL,
                        password_hash TEXT NOT NULL,
                        salt TEXT NOT NULL,
                        role TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        is_active INTEGER NOT NULL DEFAULT 1
                    );
                    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);";
                await createCmd.ExecuteNonQueryAsync();
            }

            foreach (var (username, displayName, role) in DefaultUsers)
            {
                using var checkCmd = connection.CreateCommand();
                checkCmd.CommandText = "SELECT COUNT(1) FROM users WHERE LOWER(username) = LOWER(@u);";
                checkCmd.Parameters.AddWithValue("@u", username);
                var count = Convert.ToInt32(await checkCmd.ExecuteScalarAsync());
                if (count == 0)
                {
                    var (hash, salt) = Common.PasswordHasher.HashPassword($"{username.ToLower()}123");
                    using var insCmd = connection.CreateCommand();
                    insCmd.CommandText = @"
                        INSERT INTO users (username, display_name, password_hash, salt, role, is_active)
                        VALUES (@u, @d, @h, @s, @r, 1);";
                    insCmd.Parameters.AddWithValue("@u", username);
                    insCmd.Parameters.AddWithValue("@d", displayName);
                    insCmd.Parameters.AddWithValue("@h", hash);
                    insCmd.Parameters.AddWithValue("@s", salt);
                    insCmd.Parameters.AddWithValue("@r", role);
                    await insCmd.ExecuteNonQueryAsync();
                }
            }
        }
        catch (SqliteException) { }
    }

    private static void EnsureTenantStartDateNullable(SqliteConnection connection)
    {
        try
        {
            var isNotNull = false;
            using (var chkCmd = connection.CreateCommand())
            {
                chkCmd.CommandText = "PRAGMA table_info(tenants);";
                using var reader = chkCmd.ExecuteReader();
                while (reader.Read())
                {
                    if (reader.GetString(1) == "start_date" && reader.GetInt32(3) == 1)
                    {
                        isNotNull = true;
                        break;
                    }
                }
            }

            if (isNotNull)
            {
                using var migCmd = connection.CreateCommand();
                migCmd.CommandText = @"
                    PRAGMA foreign_keys = OFF;
                    CREATE TABLE IF NOT EXISTS tenants_nullable_mig (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        house_id TEXT NOT NULL REFERENCES houses(id),
                        name TEXT NOT NULL,
                        start_date DATE,
                        end_date DATE,
                        is_resident INTEGER NOT NULL DEFAULT 1,
                        notes TEXT
                    );
                    INSERT INTO tenants_nullable_mig (id, house_id, name, start_date, end_date, is_resident, notes)
                    SELECT id, house_id, name, start_date, end_date, is_resident, notes FROM tenants;
                    DROP TABLE tenants;
                    ALTER TABLE tenants_nullable_mig RENAME TO tenants;
                    CREATE INDEX IF NOT EXISTS idx_tenants_house ON tenants(house_id);
                    CREATE INDEX IF NOT EXISTS idx_tenants_resident ON tenants(is_resident);
                    PRAGMA foreign_keys = ON;";
                migCmd.ExecuteNonQuery();
            }
        }
        catch (SqliteException) { }
    }

    private static async Task EnsureTenantStartDateNullableAsync(SqliteConnection connection)
    {
        try
        {
            var isNotNull = false;
            using (var chkCmd = connection.CreateCommand())
            {
                chkCmd.CommandText = "PRAGMA table_info(tenants);";
                using var reader = await chkCmd.ExecuteReaderAsync();
                while (await reader.ReadAsync())
                {
                    if (reader.GetString(1) == "start_date" && reader.GetInt32(3) == 1)
                    {
                        isNotNull = true;
                        break;
                    }
                }
            }

            if (isNotNull)
            {
                using var migCmd = connection.CreateCommand();
                migCmd.CommandText = @"
                    PRAGMA foreign_keys = OFF;
                    CREATE TABLE IF NOT EXISTS tenants_nullable_mig (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        house_id TEXT NOT NULL REFERENCES houses(id),
                        name TEXT NOT NULL,
                        start_date DATE,
                        end_date DATE,
                        is_resident INTEGER NOT NULL DEFAULT 1,
                        notes TEXT
                    );
                    INSERT INTO tenants_nullable_mig (id, house_id, name, start_date, end_date, is_resident, notes)
                    SELECT id, house_id, name, start_date, end_date, is_resident, notes FROM tenants;
                    DROP TABLE tenants;
                    ALTER TABLE tenants_nullable_mig RENAME TO tenants;
                    CREATE INDEX IF NOT EXISTS idx_tenants_house ON tenants(house_id);
                    CREATE INDEX IF NOT EXISTS idx_tenants_resident ON tenants(is_resident);
                    PRAGMA foreign_keys = ON;";
                await migCmd.ExecuteNonQueryAsync();
            }
        }
        catch (SqliteException) { }
    }
}
