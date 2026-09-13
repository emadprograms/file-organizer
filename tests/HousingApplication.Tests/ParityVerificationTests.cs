using System.Net;
using System.Reflection;
using System.Text.Json;
using Dapper;
using FileOrganizer.Web.Data;
using FileOrganizer.Web.Models;
using Microsoft.Extensions.DependencyInjection;
using Xunit;

namespace FileOrganizer.Tests;

/// <summary>
/// VER-05 Parity Verification Test Suite:
/// - Verifies API response schemas match FastAPI JSON responses for /api/tree, /api/houses, /api/timeline, /api/categories, /api/search.
/// - Verifies Document and Tenant models match SQLite database schema structure.
/// - Verifies static assets (index.html, js/app.js, css/styles.css) are served with correct MIME types.
/// </summary>
public class ParityVerificationTests : IClassFixture<ApiTestFixture>, IAsyncLifetime
{
    private readonly ApiTestFixture _fixture;
    private readonly HttpClient _client;

    public ParityVerificationTests(ApiTestFixture fixture)
    {
        _fixture = fixture;
        _client = fixture.CreateClient();
    }

    public async Task InitializeAsync()
    {
        await _fixture.SeedDataAsync();
    }

    public Task DisposeAsync() => Task.CompletedTask;

    #region 1. API Response Schema Parity

    [Fact]
    public async Task VerifyTreeApi_OutputSchema_MatchesFastApiContract()
    {
        var response = await _client.GetAsync("/api/tree");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var json = await response.Content.ReadAsStringAsync();
        using var doc = JsonDocument.Parse(json);
        Assert.Equal(JsonValueKind.Array, doc.RootElement.ValueKind);
        Assert.True(doc.RootElement.GetArrayLength() > 0, "Tree should not be empty");

        var firstArea = doc.RootElement[0];
        Assert.True(firstArea.TryGetProperty("id", out var idProp));
        Assert.Equal(JsonValueKind.String, idProp.ValueKind);

        Assert.True(firstArea.TryGetProperty("name", out var nameProp));
        Assert.Equal(JsonValueKind.String, nameProp.ValueKind);

        Assert.True(firstArea.TryGetProperty("type", out var typeProp));
        Assert.Equal("area", typeProp.GetString());

        Assert.True(firstArea.TryGetProperty("children", out var childrenProp));
        Assert.Equal(JsonValueKind.Array, childrenProp.ValueKind);

        if (childrenProp.GetArrayLength() > 0)
        {
            var firstHouse = childrenProp[0];
            Assert.True(firstHouse.TryGetProperty("id", out var houseIdProp));
            Assert.Equal(JsonValueKind.String, houseIdProp.ValueKind);

            Assert.True(firstHouse.TryGetProperty("name", out var houseNameProp));
            Assert.Equal(JsonValueKind.String, houseNameProp.ValueKind);

            Assert.True(firstHouse.TryGetProperty("type", out var houseTypeProp));
            Assert.Equal("house", houseTypeProp.GetString());

            Assert.True(firstHouse.TryGetProperty("total_documents", out var totalDocsProp));
            Assert.Equal(JsonValueKind.Number, totalDocsProp.ValueKind);
        }
    }

    [Fact]
    public async Task VerifyHousesApi_OutputSchema_MatchesFastApiContract()
    {
        var response = await _client.GetAsync("/api/houses");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var json = await response.Content.ReadAsStringAsync();
        using var doc = JsonDocument.Parse(json);
        Assert.Equal(JsonValueKind.Array, doc.RootElement.ValueKind);
        Assert.True(doc.RootElement.GetArrayLength() > 0, "Houses list should not be empty");

        var firstHouse = doc.RootElement[0];
        Assert.True(firstHouse.TryGetProperty("id", out var idProp));
        Assert.Equal(JsonValueKind.String, idProp.ValueKind);

        Assert.True(firstHouse.TryGetProperty("name", out var nameProp));
        Assert.Equal(JsonValueKind.String, nameProp.ValueKind);

        Assert.True(firstHouse.TryGetProperty("area_id", out var areaProp));
        Assert.Equal(JsonValueKind.String, areaProp.ValueKind);

        Assert.True(firstHouse.TryGetProperty("total_documents", out var totalDocsProp));
        Assert.Equal(JsonValueKind.Number, totalDocsProp.ValueKind);
    }

    [Fact]
    public async Task VerifyTimelineApi_OutputSchema_MatchesFastApiContract()
    {
        var response = await _client.GetAsync("/api/areas/Safra%20C/houses/500/timeline");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var json = await response.Content.ReadAsStringAsync();
        using var doc = JsonDocument.Parse(json);
        Assert.Equal(JsonValueKind.Array, doc.RootElement.ValueKind);
        Assert.True(doc.RootElement.GetArrayLength() > 0, "Timeline should contain seeded documents");

        var firstItem = doc.RootElement[0];
        Assert.True(firstItem.TryGetProperty("vault_id", out var vaultIdProp));
        Assert.Equal(JsonValueKind.String, vaultIdProp.ValueKind);

        Assert.True(firstItem.TryGetProperty("primary_tenant", out var tenantProp));
        Assert.Equal(JsonValueKind.String, tenantProp.ValueKind);

        Assert.True(firstItem.TryGetProperty("brief_arabic_title", out var titleProp));
        Assert.Equal(JsonValueKind.String, titleProp.ValueKind);

        Assert.True(firstItem.TryGetProperty("dates", out var datesProp));
        Assert.Equal(JsonValueKind.Array, datesProp.ValueKind);

        Assert.True(firstItem.TryGetProperty("is_manual", out var manualProp));
        Assert.Equal(JsonValueKind.Number, manualProp.ValueKind);
    }

    [Fact]
    public async Task VerifyCategoriesApi_OutputSchema_MatchesFastApiContract()
    {
        var response = await _client.GetAsync("/api/areas/Safra%20C/houses/500/categories");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var json = await response.Content.ReadAsStringAsync();
        using var doc = JsonDocument.Parse(json);
        Assert.Equal(JsonValueKind.Array, doc.RootElement.ValueKind);
        Assert.True(doc.RootElement.GetArrayLength() > 0, "Categories list should not be empty");

        var firstCat = doc.RootElement[0];
        Assert.True(firstCat.TryGetProperty("tenant", out var tenantProp));
        Assert.True(firstCat.TryGetProperty("name", out var nameProp));
        Assert.True(firstCat.TryGetProperty("document_count", out var countProp));
        Assert.Equal(JsonValueKind.Number, countProp.ValueKind);

        Assert.True(firstCat.TryGetProperty("documents", out var docsProp));
        Assert.Equal(JsonValueKind.Array, docsProp.ValueKind);

        if (docsProp.GetArrayLength() > 0)
        {
            var firstDoc = docsProp[0];
            Assert.True(firstDoc.TryGetProperty("vault_id", out var vIdProp));
            Assert.True(firstDoc.TryGetProperty("filename", out _));
            Assert.True(firstDoc.TryGetProperty("start_page", out _));
            Assert.True(firstDoc.TryGetProperty("end_page", out _));
            Assert.True(firstDoc.TryGetProperty("brief_arabic_title", out _));
            Assert.True(firstDoc.TryGetProperty("is_manual", out _));
        }
    }

    [Fact]
    public async Task VerifySearchApi_OutputSchema_MatchesFastApiContract()
    {
        var response = await _client.GetAsync("/api/search?q=500");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var json = await response.Content.ReadAsStringAsync();
        using var doc = JsonDocument.Parse(json);
        Assert.Equal(JsonValueKind.Array, doc.RootElement.ValueKind);

        if (doc.RootElement.GetArrayLength() > 0)
        {
            var firstResult = doc.RootElement[0];
            Assert.True(firstResult.TryGetProperty("id", out var idProp));
            Assert.True(firstResult.TryGetProperty("type", out var typeProp));
            Assert.True(firstResult.TryGetProperty("title", out var titleProp));
            Assert.True(firstResult.TryGetProperty("url", out var urlProp));

            var typeStr = typeProp.GetString();
            Assert.Contains(typeStr, new[] { "house", "tenant", "document" });
        }
    }

    #endregion

    #region 2. Database Schema and Model Mapping Parity

    [Fact]
    public async Task VerifyDocumentModel_MatchesDatabaseStructure()
    {
        using var scope = _fixture.Services.CreateScope();
        var factory = scope.ServiceProvider.GetRequiredService<ISqliteDbConnectionFactory>();
        using var conn = factory.CreateConnection();

        // Retrieve SQLite pragma info for 'documents' table
        var columns = (await conn.QueryAsync<PragmaTableInfo>("PRAGMA table_info(documents)")).ToList();
        Assert.NotEmpty(columns);

        var columnNames = columns.Select(c => c.Name.ToLowerInvariant()).ToHashSet();

        // Essential columns required by DB-01 / NET-01
        var expectedColumns = new[]
        {
            "vault_id",
            "house_id",
            "tenant_id",
            "batch_id",
            "primary_date",
            "arabic_title",
            "category",
            "page_count",
            "is_manual",
            "notes",
            "created_at"
        };

        foreach (var col in expectedColumns)
        {
            Assert.Contains(col, columnNames);
        }

        // Verify Document C# model has corresponding properties
        var docProperties = typeof(Document).GetProperties(BindingFlags.Public | BindingFlags.Instance)
            .Select(p => p.Name.ToLowerInvariant())
            .ToHashSet();

        // Check property coverage (converting snake_case to lowercase property match)
        Assert.Contains("vaultid", docProperties);
        Assert.Contains("houseid", docProperties);
        Assert.Contains("tenantid", docProperties);
        Assert.Contains("batchid", docProperties);
        Assert.Contains("primarydate", docProperties);
        Assert.Contains("arabictitle", docProperties);
        Assert.Contains("category", docProperties);
        Assert.Contains("pagecount", docProperties);
        Assert.Contains("ismanual", docProperties);
        Assert.Contains("notes", docProperties);
        Assert.Contains("createdat", docProperties);
    }

    [Fact]
    public async Task VerifyTenantModel_MatchesDatabaseStructure()
    {
        using var scope = _fixture.Services.CreateScope();
        var factory = scope.ServiceProvider.GetRequiredService<ISqliteDbConnectionFactory>();
        using var conn = factory.CreateConnection();

        // Retrieve SQLite pragma info for 'tenants' table
        var columns = (await conn.QueryAsync<PragmaTableInfo>("PRAGMA table_info(tenants)")).ToList();
        Assert.NotEmpty(columns);

        var columnNames = columns.Select(c => c.Name.ToLowerInvariant()).ToHashSet();

        var expectedColumns = new[]
        {
            "id",
            "house_id",
            "name",
            "start_date",
            "end_date"
        };

        foreach (var col in expectedColumns)
        {
            Assert.Contains(col, columnNames);
        }

        // Verify Tenant C# model has corresponding properties
        var tenantProperties = typeof(Tenant).GetProperties(BindingFlags.Public | BindingFlags.Instance)
            .Select(p => p.Name.ToLowerInvariant())
            .ToHashSet();

        Assert.Contains("id", tenantProperties);
        Assert.Contains("houseid", tenantProperties);
        Assert.Contains("name", tenantProperties);
        Assert.Contains("startdate", tenantProperties);
        Assert.Contains("enddate", tenantProperties);
    }

    private sealed class PragmaTableInfo
    {
        public int Cid { get; set; }
        public string Name { get; set; } = string.Empty;
        public string Type { get; set; } = string.Empty;
        public int NotNull { get; set; }
        public string? DfltValue { get; set; }
        public int Pk { get; set; }
    }

    #endregion

    #region 3. Static Asset Serving & MIME Type Parity

    [Fact]
    public async Task VerifyStaticAssets_IndexHtml_ServesWithCorrectMimeType()
    {
        var response = await _client.GetAsync("/index.html");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.NotNull(response.Content.Headers.ContentType);
        Assert.Equal("text/html", response.Content.Headers.ContentType.MediaType);

        var content = await response.Content.ReadAsStringAsync();
        Assert.Contains("<!DOCTYPE html>", content, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task VerifyStaticAssets_AppJs_ServesWithCorrectMimeType()
    {
        var response = await _client.GetAsync("/js/app.js");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.NotNull(response.Content.Headers.ContentType);
        
        // ASP.NET Core can serve JavaScript as text/javascript or application/javascript
        var mediaType = response.Content.Headers.ContentType.MediaType;
        Assert.True(
            mediaType == "text/javascript" || mediaType == "application/javascript",
            $"Expected JavaScript MIME type, but got: {mediaType}");

        var content = await response.Content.ReadAsStringAsync();
        Assert.NotEmpty(content);
    }

    [Fact]
    public async Task VerifyStaticAssets_StylesCss_ServesWithCorrectMimeType()
    {
        var response = await _client.GetAsync("/css/styles.css");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.NotNull(response.Content.Headers.ContentType);
        Assert.Equal("text/css", response.Content.Headers.ContentType.MediaType);

        var content = await response.Content.ReadAsStringAsync();
        Assert.NotEmpty(content);
    }

    #endregion
}
