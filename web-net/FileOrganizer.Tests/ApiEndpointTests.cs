using System.IO.Compression;
using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using FileOrganizer.Web.Data;
using FileOrganizer.Web.Models;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Xunit;

namespace FileOrganizer.Tests;

public class ApiTestFixture : WebApplicationFactory<Program>, IDisposable
{
    public string DbPath { get; }
    public string AreasRoot { get; }

    public ApiTestFixture()
    {
        DbPath = Path.Combine(Path.GetTempPath(), $"test_api_db_{Guid.NewGuid():N}.db");
        AreasRoot = Path.Combine(Path.GetTempPath(), $"test_api_areas_{Guid.NewGuid():N}");
        Directory.CreateDirectory(AreasRoot);
    }

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureAppConfiguration((_, config) =>
        {
            config.AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["ORGANIZER_DB_PATH"] = DbPath,
                ["AREAS_ROOT_PATH"] = AreasRoot
            });
        });

        builder.ConfigureServices(services =>
        {
            var descriptor = services.SingleOrDefault(d => d.ServiceType == typeof(ISqliteDbConnectionFactory));
            if (descriptor != null)
                services.Remove(descriptor);

            services.AddSingleton<ISqliteDbConnectionFactory>(new SqliteDbConnectionFactory(dbPath: DbPath));
        });
    }

    private bool _seeded;

    public async Task SeedDataAsync()
    {
        if (_seeded) return;
        _seeded = true;

        using var scope = Services.CreateScope();
        var repo = scope.ServiceProvider.GetRequiredService<IFileOrganizerRepository>();

        await repo.EnsureSchemaAsync();
        await repo.AddAreaAsync("Safra C", "SC");
        await repo.AddHouseAsync("500", "Safra C");
        var tenant = await repo.AddTenantAsync("500", "فاطمة أحمد", "2022-01-01", null);

        // Seed a document for 500
        var samplePdf = Path.Combine(AreasRoot, "seed.pdf");
        var pdfBytes = "%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"u8.ToArray();
        await File.WriteAllBytesAsync(samplePdf, pdfBytes);

        await repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "500",
            TenantId = tenant.Id,
            Category = "05 - عقود",
            ArabicTitle = "عقد إيجار اختبار",
            PrimaryDate = "2022-03-15",
            PageCount = 1,
            SourcePdfFilename = "contract.pdf",
            SourcePdfPath = samplePdf,
            VaultId = "seedvault001",
            AreasRoot = AreasRoot
        });
    }

    public new void Dispose()
    {
        base.Dispose();
        try
        {
            if (File.Exists(DbPath)) File.Delete(DbPath);
            if (File.Exists($"{DbPath}-wal")) File.Delete($"{DbPath}-wal");
            if (File.Exists($"{DbPath}-shm")) File.Delete($"{DbPath}-shm");
            if (Directory.Exists(AreasRoot)) Directory.Delete(AreasRoot, true);
        }
        catch { }
    }
}

public class ApiEndpointTests : IClassFixture<ApiTestFixture>, IAsyncLifetime
{
    private readonly ApiTestFixture _fixture;
    private readonly HttpClient _client;

    public ApiEndpointTests(ApiTestFixture fixture)
    {
        _fixture = fixture;
        _client = fixture.CreateClient();
    }

    public async Task InitializeAsync()
    {
        await _fixture.SeedDataAsync();
    }

    public Task DisposeAsync() => Task.CompletedTask;

    [Fact]
    public async Task GetTree_Returns200Ok_WithAreasList()
    {
        var response = await _client.GetAsync("/api/tree");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var tree = await response.Content.ReadFromJsonAsync<List<TreeAreaDto>>();
        Assert.NotNull(tree);
        Assert.NotEmpty(tree);

        var area = tree.FirstOrDefault(a => a.Name == "Safra C");
        Assert.NotNull(area);
        Assert.Equal("area", area.Type);
        Assert.NotNull(area.Children);
        Assert.Contains(area.Children, h => h.Id == "500");
    }

    [Fact]
    public async Task GetHouses_Returns200Ok()
    {
        var response = await _client.GetAsync("/api/houses");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var houses = await response.Content.ReadFromJsonAsync<List<HouseCardDto>>();
        Assert.NotNull(houses);
        Assert.NotEmpty(houses);
        Assert.Contains(houses, h => h.Id == "500");
    }

    [Fact]
    public async Task GetTimeline_Returns200Ok()
    {
        var response = await _client.GetAsync("/api/areas/Safra%20C/houses/500/timeline");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var timeline = await response.Content.ReadFromJsonAsync<List<TimelineItemDto>>();
        Assert.NotNull(timeline);
        Assert.NotEmpty(timeline);
        Assert.Contains(timeline, t => t.VaultId == "seedvault001");
    }

    [Fact]
    public async Task Search_Returns200Ok()
    {
        var response = await _client.GetAsync("/api/search?q=test");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var results = await response.Content.ReadFromJsonAsync<List<SearchResultDto>>();
        Assert.NotNull(results);
    }

    [Fact]
    public async Task PostIngest_WithMultipartUpload_Returns200Ok_AndPersists()
    {
        using var content = new MultipartFormDataContent();

        var pdfBytes = "%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"u8.ToArray();
        var fileContent = new ByteArrayContent(pdfBytes);
        fileContent.Headers.ContentType = new MediaTypeHeaderValue("application/pdf");
        content.Add(fileContent, "file", "upload_contract.pdf");

        content.Add(new StringContent("manual"), "mode");
        content.Add(new StringContent("Safra C"), "area_id");
        content.Add(new StringContent("500"), "house_id");
        content.Add(new StringContent("05 - عقود"), "category");
        content.Add(new StringContent("عقد إيجار جديد"), "arabic_title");
        content.Add(new StringContent("2023-01-10"), "primary_date");
        content.Add(new StringContent("Uploaded via integration test"), "notes");

        var response = await _client.PostAsync("/api/ingest", content);
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var ingestRes = await response.Content.ReadFromJsonAsync<IngestResponseDto>();
        Assert.NotNull(ingestRes);
        Assert.Equal("success", ingestRes.Status);
        Assert.False(string.IsNullOrEmpty(ingestRes.VaultId));
        Assert.Equal("500", ingestRes.HouseId);
        Assert.Equal("Safra C", ingestRes.AreaId);

        // Verify document is persisted in database
        using var scope = _fixture.Services.CreateScope();
        var repo = scope.ServiceProvider.GetRequiredService<IFileOrganizerRepository>();
        var doc = await repo.GetDocumentDetailsAsync(ingestRes.VaultId!);
        Assert.NotNull(doc);
        Assert.Equal("عقد إيجار جديد", doc.ArabicTitle);
        Assert.Equal("2023-01-10", doc.PrimaryDate);
        Assert.Equal("Uploaded via integration test", doc.Notes);
    }

    [Fact]
    public async Task GetRoot_ServesIndexHtml()
    {
        var response = await _client.GetAsync("/");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var html = await response.Content.ReadAsStringAsync();
        Assert.Contains("<html", html, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task PostPreviewAi_Returns200Ok_WithPredictions()
    {
        using var content = new MultipartFormDataContent();

        // PDF containing Arabic contract keywords
        var pdfBytes = "%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n% عقد إيجار 2024-06-15\n%%EOF"u8.ToArray();
        var fileContent = new ByteArrayContent(pdfBytes);
        fileContent.Headers.ContentType = new MediaTypeHeaderValue("application/pdf");
        content.Add(fileContent, "file", "contract_2024-06-15.pdf");
        content.Add(new StringContent("Safra C"), "area_id");
        content.Add(new StringContent("500"), "house_id");

        var response = await _client.PostAsync("/api/ingest/preview-ai", content);
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var preview = await response.Content.ReadFromJsonAsync<AIPreviewResponseDto>();
        Assert.NotNull(preview);
        Assert.Equal("success", preview.Status);
        Assert.Equal("05 - عقود", preview.SuggestedCategory);
        Assert.Equal("2024-06-15", preview.SuggestedDate);
    }

    [Fact]
    public async Task GetDbInspectorStats_Returns200Ok()
    {
        var res1 = await _client.GetAsync("/api/db/inspector/stats");
        Assert.Equal(HttpStatusCode.OK, res1.StatusCode);
        var stats1 = await res1.Content.ReadFromJsonAsync<DbInfoResponseDto>();
        Assert.NotNull(stats1);
        Assert.True(stats1.Connected);
        Assert.True(stats1.Tables.ContainsKey("houses"));

        var res2 = await _client.GetAsync("/api/db/info");
        Assert.Equal(HttpStatusCode.OK, res2.StatusCode);
    }

    [Fact]
    public async Task GetDbInspectorTable_Returns200Ok()
    {
        var response = await _client.GetAsync("/api/db/inspector/tenants");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var tableData = await response.Content.ReadFromJsonAsync<DbTableResponseDto>();
        Assert.NotNull(tableData);
        Assert.Equal("tenants", tableData.Table);
        Assert.NotEmpty(tableData.Columns);
        Assert.True(tableData.Total > 0);
        Assert.NotEmpty(tableData.Rows);
    }

    [Fact]
    public async Task DocumentCrud_Copy_Update_ResetLock_Works()
    {
        // 1. Get document details
        var getRes = await _client.GetAsync("/api/areas/Safra%20C/houses/500/documents/seedvault001");
        Assert.Equal(HttpStatusCode.OK, getRes.StatusCode);
        var doc = await getRes.Content.ReadFromJsonAsync<DocumentDetailsDto>();
        Assert.NotNull(doc);
        Assert.Equal("seedvault001", doc.VaultId);

        // 2. Update document
        var updatePayload = new DocumentUpdateRequestDto
        {
            ArabicTitle = "عقد معدل للتوثيق",
            Notes = "تم التعديل عبر API"
        };
        var patchRes = await _client.PatchAsJsonAsync("/api/areas/Safra%20C/houses/500/documents/seedvault001", updatePayload);
        Assert.Equal(HttpStatusCode.OK, patchRes.StatusCode);
        var patchData = await patchRes.Content.ReadFromJsonAsync<DocumentActionResponseDto>();
        Assert.NotNull(patchData);
        Assert.Equal("عقد معدل للتوثيق", patchData.ArabicTitle);

        // 3. Reset lock
        var resetRes = await _client.PostAsync("/api/areas/Safra%20C/houses/500/documents/seedvault001/reset-lock", null);
        Assert.Equal(HttpStatusCode.OK, resetRes.StatusCode);
        var resetData = await resetRes.Content.ReadFromJsonAsync<DocumentActionResponseDto>();
        Assert.NotNull(resetData);
        Assert.Equal(0, resetData.IsManual);

        // 4. Copy document
        var copyPayload = new DocumentCopyRequestDto
        {
            TargetTitle = "نسخة من العقد",
            TargetCategory = "05 - عقود"
        };
        var copyRes = await _client.PostAsJsonAsync("/api/areas/Safra%20C/houses/500/documents/seedvault001/copy", copyPayload);
        Assert.Equal(HttpStatusCode.OK, copyRes.StatusCode);
        var copyData = await copyRes.Content.ReadFromJsonAsync<DocumentActionResponseDto>();
        Assert.NotNull(copyData);
        Assert.Equal("success", copyData.Status);
        Assert.NotEqual("seedvault001", copyData.VaultId);
    }

    [Fact]
    public async Task GetPdf_StreamsPdf_WithApplicationPdfContentType()
    {
        var response = await _client.GetAsync("/api/areas/Safra%20C/houses/500/pdf/seedvault001");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.Equal("application/pdf", response.Content.Headers.ContentType?.MediaType);

        var bytes = await response.Content.ReadAsByteArrayAsync();
        Assert.NotEmpty(bytes);
        Assert.StartsWith("%PDF", System.Text.Encoding.ASCII.GetString(bytes[..4]));
    }

    [Fact]
    public async Task GetHouseProfile_Returns200Ok()
    {
        var response = await _client.GetAsync("/api/areas/Safra%20C/houses/500");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var profile = await response.Content.ReadFromJsonAsync<HouseProfileDto>();
        Assert.NotNull(profile);
        Assert.Equal("500", profile.HouseId);
        Assert.Equal("Safra C", profile.AreaId);
        Assert.NotEmpty(profile.Tenants);
    }

    [Fact]
    public async Task GetCategories_Returns200Ok()
    {
        var response = await _client.GetAsync("/api/areas/Safra%20C/houses/500/categories");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var categories = await response.Content.ReadFromJsonAsync<List<CategoryFolderDto>>();
        Assert.NotNull(categories);
        Assert.NotEmpty(categories);
    }

    [Fact]
    public async Task GetTenants_Returns200Ok()
    {
        var response = await _client.GetAsync("/api/areas/Safra%20C/houses/500/tenants");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var tenants = await response.Content.ReadFromJsonAsync<List<TenantDto>>();
        Assert.NotNull(tenants);
        Assert.NotEmpty(tenants);
        Assert.Contains(tenants, t => t.Name == "فاطمة أحمد");
    }

    [Fact]
    public async Task PostIngest_WithInvalidExtension_Returns400()
    {
        using var content = new MultipartFormDataContent();
        var fileContent = new ByteArrayContent(new byte[] { 1, 2, 3 });
        content.Add(fileContent, "file", "document.txt");
        content.Add(new StringContent("Safra C"), "area_id");
        content.Add(new StringContent("500"), "house_id");

        var response = await _client.PostAsync("/api/ingest", content);
        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
    }

    [Fact]
    public async Task PostIngest_WithInvalidMagicBytes_Returns400()
    {
        using var content = new MultipartFormDataContent();
        var fakePdfBytes = "NOT A REAL PDF FILE"u8.ToArray();
        var fileContent = new ByteArrayContent(fakePdfBytes);
        fileContent.Headers.ContentType = new MediaTypeHeaderValue("application/pdf");
        content.Add(fileContent, "file", "fake.pdf");
        content.Add(new StringContent("Safra C"), "area_id");
        content.Add(new StringContent("500"), "house_id");

        var response = await _client.PostAsync("/api/ingest", content);
        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
    }

    [Fact]
    public async Task DeleteCategory_Returns200Ok()
    {
        var response = await _client.DeleteAsync("/api/areas/Safra%20C/houses/500/categories/05%20-%20عقود");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }

    [Fact]
    public async Task TriggerReallocate_Returns200Ok()
    {
        var response = await _client.PostAsync("/api/areas/Safra%20C/houses/500/reallocate", null);
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var result = await response.Content.ReadFromJsonAsync<TenantReallocationResponseDto>();
        Assert.NotNull(result);
        Assert.Equal("success", result.Status);
    }

    [Fact]
    public async Task DeleteDocument_NonExistent_Returns404NotFound()
    {
        var response = await _client.DeleteAsync("/api/areas/Safra%20C/houses/500/documents/non_existent_vault_id");
        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }

    [Fact]
    public async Task DeleteDocument_Existing_Returns200Ok()
    {
        using var scope = _fixture.Services.CreateScope();
        var repo = scope.ServiceProvider.GetRequiredService<IFileOrganizerRepository>();
        var ingest = await repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "500",
            TenantId = 1,
            Category = "05 - عقود",
            ArabicTitle = "مستند للحذف عبر API",
            PrimaryDate = "2022-04-01",
            PageCount = 1,
            AreasRoot = _fixture.AreasRoot
        });

        var response = await _client.DeleteAsync($"/api/areas/Safra%20C/houses/500/documents/{ingest.VaultId}");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var verifyNotFound = await _client.DeleteAsync($"/api/areas/Safra%20C/houses/500/documents/{ingest.VaultId}");
        Assert.Equal(HttpStatusCode.NotFound, verifyNotFound.StatusCode);
    }

    [Fact]
    public async Task ExportZip_ReturnsZipArchive()
    {
        var response = await _client.GetAsync("/api/areas/Safra%20C/houses/500/export-zip");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.Equal("application/zip", response.Content.Headers.ContentType?.MediaType);
        Assert.Contains("archive_Safra_C_500.zip", response.Content.Headers.ContentDisposition?.FileName);

        var bytes = await response.Content.ReadAsByteArrayAsync();
        using var memoryStream = new MemoryStream(bytes);
        using var zip = new ZipArchive(memoryStream, ZipArchiveMode.Read);
        Assert.NotEmpty(zip.Entries);
    }
}

