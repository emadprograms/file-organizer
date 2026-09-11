using System.Data.Common;
using Microsoft.Data.Sqlite;
using Microsoft.Extensions.Configuration;

namespace FileOrganizer.Web.Data;

public interface ISqliteDbConnectionFactory
{
    string DatabasePath { get; }
    SqliteConnection CreateConnection();
    Task<SqliteConnection> CreateConnectionAsync(CancellationToken cancellationToken = default);
}

public class SqliteDbConnectionFactory : ISqliteDbConnectionFactory
{
    private readonly string _connectionString;
    public string DatabasePath { get; }

    public SqliteDbConnectionFactory(IConfiguration? configuration = null, string? dbPath = null)
    {
        var resolvedPath = dbPath 
            ?? configuration?["ORGANIZER_DB_PATH"] 
            ?? configuration?["Database:Path"] 
            ?? "organizer.db";

        DatabasePath = resolvedPath;

        // Ensure parent directory exists for file-based sqlite databases
        if (!resolvedPath.Equals(":memory:", StringComparison.OrdinalIgnoreCase) &&
            !resolvedPath.StartsWith("file:", StringComparison.OrdinalIgnoreCase))
        {
            var dir = Path.GetDirectoryName(Path.GetFullPath(resolvedPath));
            if (!string.IsNullOrEmpty(dir) && !Directory.Exists(dir))
            {
                Directory.CreateDirectory(dir);
            }
        }

        // Connection string: Data Source={dbPath};Mode=ReadWrite;Cache=Default;Pooling=True;
        // When file does not exist, use ReadWriteCreate so the database is automatically created
        var mode = File.Exists(resolvedPath) ? "ReadWrite" : "ReadWriteCreate";
        _connectionString = $"Data Source={resolvedPath};Mode={mode};Cache=Default;Pooling=True;";
    }

    private static void ConfigurePragmas(SqliteConnection conn)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = "PRAGMA busy_timeout=5000; PRAGMA foreign_keys=ON; PRAGMA synchronous=NORMAL;";
        cmd.ExecuteNonQuery();

        try
        {
            cmd.CommandText = "PRAGMA journal_mode=WAL;";
            cmd.ExecuteNonQuery();
        }
        catch
        {
            try
            {
                cmd.CommandText = "PRAGMA journal_mode=DELETE;";
                cmd.ExecuteNonQuery();
            }
            catch
            {
                // Ignore if pragma cannot be set
            }
        }
    }

    private static async Task ConfigurePragmasAsync(SqliteConnection conn, CancellationToken cancellationToken)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = "PRAGMA busy_timeout=5000; PRAGMA foreign_keys=ON; PRAGMA synchronous=NORMAL;";
        await cmd.ExecuteNonQueryAsync(cancellationToken);

        try
        {
            cmd.CommandText = "PRAGMA journal_mode=WAL;";
            await cmd.ExecuteNonQueryAsync(cancellationToken);
        }
        catch
        {
            try
            {
                cmd.CommandText = "PRAGMA journal_mode=DELETE;";
                await cmd.ExecuteNonQueryAsync(cancellationToken);
            }
            catch
            {
                // Ignore if pragma cannot be set
            }
        }
    }

    public SqliteConnection CreateConnection()
    {
        var conn = new SqliteConnection(_connectionString);
        conn.Open();
        ConfigurePragmas(conn);
        return conn;
    }

    public async Task<SqliteConnection> CreateConnectionAsync(CancellationToken cancellationToken = default)
    {
        var conn = new SqliteConnection(_connectionString);
        await conn.OpenAsync(cancellationToken);
        await ConfigurePragmasAsync(conn, cancellationToken);
        return conn;
    }
}
