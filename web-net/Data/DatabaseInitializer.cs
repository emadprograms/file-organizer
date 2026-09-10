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
    start_date DATE NOT NULL,
    end_date DATE
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
CREATE INDEX IF NOT EXISTS idx_documents_timeline ON documents(is_timeline_visible);
";

    public static void InitializeSchema(SqliteConnection connection)
    {
        using var cmd = connection.CreateCommand();
        cmd.CommandText = SchemaSql;
        cmd.ExecuteNonQuery();

        try
        {
            using var alterCmd = connection.CreateCommand();
            alterCmd.CommandText = "ALTER TABLE documents ADD COLUMN is_timeline_visible INTEGER DEFAULT 1;";
            alterCmd.ExecuteNonQuery();
        }
        catch (SqliteException) { }
    }

    public static async Task InitializeSchemaAsync(SqliteConnection connection)
    {
        using var cmd = connection.CreateCommand();
        cmd.CommandText = SchemaSql;
        await cmd.ExecuteNonQueryAsync();

        try
        {
            using var alterCmd = connection.CreateCommand();
            alterCmd.CommandText = "ALTER TABLE documents ADD COLUMN is_timeline_visible INTEGER DEFAULT 1;";
            await alterCmd.ExecuteNonQueryAsync();
        }
        catch (SqliteException) { }
    }
}
