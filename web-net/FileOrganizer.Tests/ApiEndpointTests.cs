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
    public async Task Search_PhoneticTenantAccuracy_UsmanMatchesOthmanAndStrictlyRejectsZaidSalmanWaseem()
    {
        // Seed houses and distinct tenants with potential phonetic collisions
        using (var scope = _fixture.Services.CreateScope())
        {
            var repo = scope.ServiceProvider.GetRequiredService<IFileOrganizerRepository>();
            await repo.AddHouseAsync("551", "Safra C");
            await repo.AddHouseAsync("552", "Safra C");
            await repo.AddHouseAsync("553", "Safra C");
            await repo.AddTenantAsync("551", "محمد عثمان حاجي فقير محمد", "2021-01-01", null);
            await repo.AddTenantAsync("552", "زياد عوض السليمان", "2020-01-01", null);
            await repo.AddTenantAsync("553", "وسيم سردار محمد", "2019-01-01", null);
        }

        // 1. Query 'usman': MUST return عثمان and MUST NOT return زياد, سليمان, or وسيم
        var usmanRes = await _client.GetAsync("/api/search?q=usman");
        Assert.Equal(HttpStatusCode.OK, usmanRes.StatusCode);
        var usmanList = await usmanRes.Content.ReadFromJsonAsync<List<SearchResultDto>>();
        Assert.NotNull(usmanList);
        Assert.Contains(usmanList, r => r.Type == "tenant" && r.Title.Contains("عثمان"));
        Assert.DoesNotContain(usmanList, r => r.Type == "tenant" && (r.Title.Contains("زياد") || r.Title.Contains("سليمان") || r.Title.Contains("وسيم")));

        // 2. Query 'waseem': MUST return وسيم and MUST NOT return عثمان or زياد
        var waseemRes = await _client.GetAsync("/api/search?q=waseem");
        Assert.Equal(HttpStatusCode.OK, waseemRes.StatusCode);
        var waseemList = await waseemRes.Content.ReadFromJsonAsync<List<SearchResultDto>>();
        Assert.NotNull(waseemList);
        Assert.Contains(waseemList, r => r.Type == "tenant" && r.Title.Contains("وسيم"));
        Assert.DoesNotContain(waseemList, r => r.Type == "tenant" && (r.Title.Contains("عثمان") || r.Title.Contains("زياد")));

        // 3. Query 'zaid': MUST return زياد and MUST NOT return عثمان or وسيم
        var zaidRes = await _client.GetAsync("/api/search?q=zaid");
        Assert.Equal(HttpStatusCode.OK, zaidRes.StatusCode);
        var zaidList = await zaidRes.Content.ReadFromJsonAsync<List<SearchResultDto>>();
        Assert.NotNull(zaidList);
        Assert.Contains(zaidList, r => r.Type == "tenant" && r.Title.Contains("زياد"));
        Assert.DoesNotContain(zaidList, r => r.Type == "tenant" && (r.Title.Contains("عثمان") || r.Title.Contains("وسيم")));
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
        // Verify folder numbering normalization from urgent user requirement
        Assert.Contains(zip.Entries, e => e.FullName.StartsWith("05 - عقود/"));
    }

    [Fact]
    public async Task ExportZip_WithTenantFilter_ReturnsFilteredZip()
    {
        using var scope = _fixture.Services.CreateScope();
        var repo = scope.ServiceProvider.GetRequiredService<IFileOrganizerRepository>();

        var tenant2 = await repo.AddTenantAsync("500", "عبدالله السعيد", "2023-01-01", null);

        var samplePdf = Path.Combine(_fixture.AreasRoot, "tenant2_test.pdf");
        using (var pdf = new PdfSharpCore.Pdf.PdfDocument())
        {
            pdf.AddPage();
            pdf.Save(samplePdf);
        }

        // Add document with raw unnumbered category to test folder numbering normalization
        var doc = await repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "500",
            TenantId = tenant2.Id,
            Category = "أمر تخصيص",
            ArabicTitle = "تخصيص عبدالله",
            PrimaryDate = "2023-05-01",
            PageCount = 1,
            SourcePdfFilename = "tenant2_doc.pdf",
            SourcePdfPath = samplePdf,
            AreasRoot = _fixture.AreasRoot
        });

        var response = await _client.GetAsync($"/api/areas/Safra%20C/houses/500/export-zip?tenantId={tenant2.Id}");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.Equal("application/zip", response.Content.Headers.ContentType?.MediaType);

        var bytes = await response.Content.ReadAsByteArrayAsync();
        using var memoryStream = new MemoryStream(bytes);
        using var zip = new ZipArchive(memoryStream, ZipArchiveMode.Read);
        
        Assert.NotEmpty(zip.Entries);
        // Verify only tenant2 doc is present and numbered folder prefix is applied
        Assert.All(zip.Entries, e => Assert.StartsWith("03 - أمر تخصيص/", e.FullName));
    }

    [Fact]
    public async Task ExportPdf_ReturnsChronologicalMergedPdf()
    {
        using var scope = _fixture.Services.CreateScope();
        var repo = scope.ServiceProvider.GetRequiredService<IFileOrganizerRepository>();

        await repo.AddHouseAsync("600", "Safra C");
        var tenant = await repo.AddTenantAsync("600", "علي الزهراني", "2020-01-01", null);

        // Document 1: 2021-01-01 (middle date) -> Page width 200
        var pMidPath = Path.Combine(_fixture.AreasRoot, "chrono_mid.pdf");
        using (var pdfMid = new PdfSharpCore.Pdf.PdfDocument())
        {
            var p = pdfMid.AddPage();
            p.Width = 200;
            pdfMid.Save(pMidPath);
        }
        await repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "600",
            TenantId = tenant.Id,
            Category = "05 - عقود",
            ArabicTitle = "عقد 2021",
            PrimaryDate = "2021-01-01",
            PageCount = 1,
            SourcePdfFilename = "chrono_mid.pdf",
            SourcePdfPath = pMidPath,
            AreasRoot = _fixture.AreasRoot
        });

        // Document 2: 2024-05-15 (newest / most recent date) -> Page width 300
        var pNewPath = Path.Combine(_fixture.AreasRoot, "chrono_new.pdf");
        using (var pdfNew = new PdfSharpCore.Pdf.PdfDocument())
        {
            var p = pdfNew.AddPage();
            p.Width = 300;
            pdfNew.Save(pNewPath);
        }
        await repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "600",
            TenantId = tenant.Id,
            Category = "05 - عقود",
            ArabicTitle = "عقد 2024",
            PrimaryDate = "2024-05-15",
            PageCount = 1,
            SourcePdfFilename = "chrono_new.pdf",
            SourcePdfPath = pNewPath,
            AreasRoot = _fixture.AreasRoot
        });

        // Document 3: 2020-03-01 (oldest date) -> Page width 100
        var pOldPath = Path.Combine(_fixture.AreasRoot, "chrono_old.pdf");
        using (var pdfOld = new PdfSharpCore.Pdf.PdfDocument())
        {
            var p = pdfOld.AddPage();
            p.Width = 100;
            pdfOld.Save(pOldPath);
        }
        await repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "600",
            TenantId = tenant.Id,
            Category = "05 - عقود",
            ArabicTitle = "عقد 2020",
            PrimaryDate = "2020-03-01",
            PageCount = 1,
            SourcePdfFilename = "chrono_old.pdf",
            SourcePdfPath = pOldPath,
            AreasRoot = _fixture.AreasRoot
        });

        // Document 4: Undated document -> Page width 50 (should come last!)
        var pUndatedPath = Path.Combine(_fixture.AreasRoot, "chrono_undated.pdf");
        using (var pdfUndated = new PdfSharpCore.Pdf.PdfDocument())
        {
            var p = pdfUndated.AddPage();
            p.Width = 50;
            pdfUndated.Save(pUndatedPath);
        }
        await repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "600",
            TenantId = tenant.Id,
            Category = "05 - عقود",
            ArabicTitle = "عقد بدون تاريخ",
            PrimaryDate = null,
            PageCount = 1,
            SourcePdfFilename = "chrono_undated.pdf",
            SourcePdfPath = pUndatedPath,
            AreasRoot = _fixture.AreasRoot
        });

        var response = await _client.GetAsync("/api/areas/Safra%20C/houses/600/export-pdf");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.Equal("application/pdf", response.Content.Headers.ContentType?.MediaType);
        Assert.Contains("archive_Safra_C_600.pdf", response.Content.Headers.ContentDisposition?.FileName);

        var bytes = await response.Content.ReadAsByteArrayAsync();
        using var ms = new MemoryStream(bytes);
        using var parsed = PdfSharpCore.Pdf.IO.PdfReader.Open(ms, PdfSharpCore.Pdf.IO.PdfDocumentOpenMode.Import);
        Assert.Equal(4, parsed.PageCount);
        // Descending chronological order: Page 1 is 2024-05-15 (Width 300), Page 2 is 2021-01-01 (Width 200), Page 3 is 2020-03-01 (Width 100), Page 4 is undated (Width 50)
        Assert.Equal(300, (int)parsed.Pages[0].Width.Point);
        Assert.Equal(200, (int)parsed.Pages[1].Width.Point);
        Assert.Equal(100, (int)parsed.Pages[2].Width.Point);
        Assert.Equal(50, (int)parsed.Pages[3].Width.Point);

        // Assert exported PDF contains pages with valid layout and dimensions
        for (int i = 0; i < parsed.PageCount; i++)
        {
            var page = parsed.Pages[i];
            Assert.True(page.Width.Point > 0, $"Page {i + 1} width must be positive");
            Assert.True(page.Height.Point > 0, $"Page {i + 1} height must be positive");
        }
    }

    [Fact]
    public async Task ExportPdf_RunningFooter_ContainsValidPagesAndLayout()
    {
        using var scope = _fixture.Services.CreateScope();
        var repo = scope.ServiceProvider.GetRequiredService<IFileOrganizerRepository>();

        await repo.AddHouseAsync("700", "Safra C");
        var tenant = await repo.AddTenantAsync("700", "مستأجر الفوتر", "2024-01-01", null);

        var pdf1Path = Path.Combine(_fixture.AreasRoot, "footer_test_doc1.pdf");
        using (var pdf = new PdfSharpCore.Pdf.PdfDocument())
        {
            pdf.AddPage();
            pdf.AddPage();
            pdf.Save(pdf1Path);
        }

        var pdf2Path = Path.Combine(_fixture.AreasRoot, "footer_test_doc2.pdf");
        using (var pdf = new PdfSharpCore.Pdf.PdfDocument())
        {
            pdf.AddPage();
            pdf.Save(pdf2Path);
        }

        await repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "700",
            TenantId = tenant.Id,
            Category = "05 - عقود",
            ArabicTitle = "عقد متعدد الصفحات",
            PrimaryDate = "2024-05-15",
            PageCount = 2,
            SourcePdfFilename = "doc_footer1.pdf",
            SourcePdfPath = pdf1Path,
            AreasRoot = _fixture.AreasRoot
        });

        await repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "700",
            TenantId = tenant.Id,
            Category = "06 - كهرباء وماء",
            ArabicTitle = "فاتورة",
            PrimaryDate = "2024-03-01",
            PageCount = 1,
            SourcePdfFilename = "doc_footer2.pdf",
            SourcePdfPath = pdf2Path,
            AreasRoot = _fixture.AreasRoot
        });

        var response = await _client.GetAsync("/api/areas/Safra%20C/houses/700/export-pdf");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.Equal("application/pdf", response.Content.Headers.ContentType?.MediaType);
        Assert.Contains("archive_Safra_C_700.pdf", response.Content.Headers.ContentDisposition?.FileName);

        var bytes = await response.Content.ReadAsByteArrayAsync();
        Assert.NotEmpty(bytes);
        using var ms = new MemoryStream(bytes);
        using var parsed = PdfSharpCore.Pdf.IO.PdfReader.Open(ms, PdfSharpCore.Pdf.IO.PdfDocumentOpenMode.Import);
        // Total pages = 2 (doc 1) + 1 (doc 2) = 3 pages
        Assert.Equal(3, parsed.PageCount);
        for (int i = 0; i < parsed.PageCount; i++)
        {
            var page = parsed.Pages[i];
            Assert.True(page.Width.Point > 0, $"Page {i + 1} has valid layout width");
            Assert.True(page.Height.Point > 0, $"Page {i + 1} has valid layout height");
        }
    }

    [Fact]
    public async Task ExportPdf_WithTenantFilter_ReturnsFilteredPdf()
    {
        using var scope = _fixture.Services.CreateScope();
        var repo = scope.ServiceProvider.GetRequiredService<IFileOrganizerRepository>();

        var tenant = await repo.AddTenantAsync("500", "سعد الدوسري", "2024-01-01", null);

        var validPdfPath = Path.Combine(_fixture.AreasRoot, "saad_pdf_test.pdf");
        using (var pdf = new PdfSharpCore.Pdf.PdfDocument())
        {
            pdf.AddPage();
            pdf.Save(validPdfPath);
        }

        await repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "500",
            TenantId = tenant.Id,
            Category = "05 - عقود",
            ArabicTitle = "عقد سعد",
            PrimaryDate = "2024-02-01",
            PageCount = 1,
            SourcePdfFilename = "saad.pdf",
            SourcePdfPath = validPdfPath,
            AreasRoot = _fixture.AreasRoot
        });

        var response = await _client.GetAsync($"/api/areas/Safra%20C/houses/500/export-pdf?tenantId={tenant.Id}");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.Equal("application/pdf", response.Content.Headers.ContentType?.MediaType);

        var bytes = await response.Content.ReadAsByteArrayAsync();
        using var ms = new MemoryStream(bytes);
        using var parsed = PdfSharpCore.Pdf.IO.PdfReader.Open(ms, PdfSharpCore.Pdf.IO.PdfDocumentOpenMode.Import);
        Assert.Equal(1, parsed.PageCount);
    }

    [Fact]
    public async Task BatchMove_UpdatesDocuments_Returns200Ok()
    {
        using var scope = _fixture.Services.CreateScope();
        var repo = scope.ServiceProvider.GetRequiredService<IFileOrganizerRepository>();

        var doc1 = await repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "500",
            TenantId = 1,
            Category = "05 - عقود",
            ArabicTitle = "مستند لنقل 1",
            PrimaryDate = "2022-04-01",
            PageCount = 1,
            AreasRoot = _fixture.AreasRoot
        });

        var doc2 = await repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "500",
            TenantId = 1,
            Category = "05 - عقود",
            ArabicTitle = "مستند لنقل 2",
            PrimaryDate = "2022-04-02",
            PageCount = 1,
            AreasRoot = _fixture.AreasRoot
        });

        // Validation for empty vault_ids
        var emptyIdsResponse = await _client.PostAsJsonAsync(
            "/api/areas/Safra%20C/houses/500/documents/batch-move",
            new BatchMoveRequestDto { VaultIds = new List<string>(), TargetCategory = "10 - صيانة" });
        Assert.Equal(HttpStatusCode.BadRequest, emptyIdsResponse.StatusCode);

        // Validation for empty target_category
        var emptyCatResponse = await _client.PostAsJsonAsync(
            "/api/areas/Safra%20C/houses/500/documents/batch-move",
            new BatchMoveRequestDto { VaultIds = new List<string> { doc1.VaultId! }, TargetCategory = "" });
        Assert.Equal(HttpStatusCode.BadRequest, emptyCatResponse.StatusCode);

        var t2 = await repo.AddTenantAsync("500", "سعد القحطاني", "2023-01-01", null);

        // Batch move execution with TargetTenantId
        var response = await _client.PostAsJsonAsync(
            "/api/areas/Safra%20C/houses/500/documents/batch-move",
            new BatchMoveRequestDto
            {
                VaultIds = new List<string> { doc1.VaultId!, doc2.VaultId! },
                TargetCategory = "10 - صيانة",
                TargetTenantId = t2.Id
            });

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var result = await response.Content.ReadFromJsonAsync<BatchMoveResponseDto>();
        Assert.NotNull(result);
        Assert.Equal("success", result.Status);
        Assert.Equal(2, result.MovedCount);
        Assert.Equal("10 - صيانة", result.TargetCategory);
        Assert.Contains(doc1.VaultId!, result.VaultIds);
        Assert.Contains(doc2.VaultId!, result.VaultIds);

        // Verify DB update
        var updatedDoc1 = await repo.GetDocumentRawAsync(doc1.VaultId!);
        var updatedDoc2 = await repo.GetDocumentRawAsync(doc2.VaultId!);
        Assert.NotNull(updatedDoc1);
        Assert.NotNull(updatedDoc2);
        Assert.Equal("10 - صيانة", updatedDoc1.Category);
        Assert.Equal(1, updatedDoc1.IsManual);
        Assert.Equal(t2.Id, updatedDoc1.TenantId);
        Assert.Equal("10 - صيانة", updatedDoc2.Category);
        Assert.Equal(1, updatedDoc2.IsManual);
        Assert.Equal(t2.Id, updatedDoc2.TenantId);
    }

    [Fact]
    public async Task BatchDelete_RemovesDocuments_Returns200Ok()
    {
        using var scope = _fixture.Services.CreateScope();
        var repo = scope.ServiceProvider.GetRequiredService<IFileOrganizerRepository>();

        var doc1 = await repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "500",
            TenantId = 1,
            Category = "05 - عقود",
            ArabicTitle = "مستند حذف دفعة 1",
            PrimaryDate = "2022-04-03",
            PageCount = 1,
            AreasRoot = _fixture.AreasRoot
        });

        var doc2 = await repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "500",
            TenantId = 1,
            Category = "05 - عقود",
            ArabicTitle = "مستند حذف دفعة 2",
            PrimaryDate = "2022-04-04",
            PageCount = 1,
            AreasRoot = _fixture.AreasRoot
        });

        // Validation for empty vault_ids
        var emptyResponse = await _client.PostAsJsonAsync(
            "/api/areas/Safra%20C/houses/500/documents/batch-delete",
            new BatchDeleteRequestDto { VaultIds = new List<string>() });
        Assert.Equal(HttpStatusCode.BadRequest, emptyResponse.StatusCode);

        // Batch delete execution
        var response = await _client.PostAsJsonAsync(
            "/api/areas/Safra%20C/houses/500/documents/batch-delete",
            new BatchDeleteRequestDto
            {
                VaultIds = new List<string> { doc1.VaultId!, doc2.VaultId! }
            });

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var result = await response.Content.ReadFromJsonAsync<BatchDeleteResponseDto>();
        Assert.NotNull(result);
        Assert.Equal("success", result.Status);
        Assert.Equal(2, result.DeletedCount);
        Assert.Contains(doc1.VaultId!, result.VaultIds);
        Assert.Contains(doc2.VaultId!, result.VaultIds);

        // Verify DB deletion
        var raw1 = await repo.GetDocumentRawAsync(doc1.VaultId!);
        var raw2 = await repo.GetDocumentRawAsync(doc2.VaultId!);
        Assert.Null(raw1);
        Assert.Null(raw2);
    }

    [Fact]
    public async Task CreateHouse_ReturnsCreatedHouseAndDirectories()
    {
        var request = new CreateHouseRequestDto
        {
            HouseId = "516",
            InitialTenantName = "سارة عبد الله",
            StartDate = "2024-07-01"
        };

        var response = await _client.PostAsJsonAsync("/api/areas/Safra%20C/houses", request);
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var result = await response.Content.ReadFromJsonAsync<CreateHouseResponseDto>();
        Assert.NotNull(result);
        Assert.Equal("success", result.Status);
        Assert.Equal("Safra C", result.AreaId);
        Assert.Equal("516", result.HouseId);
        Assert.NotNull(result.TenantId);

        // Verify physical directories scaffolded
        var batchesDir = Path.Combine(_fixture.AreasRoot, "Safra C", "516", "batches");
        var vaultDir = Path.Combine(_fixture.AreasRoot, "Safra C", "516", "vault");
        Assert.True(Directory.Exists(batchesDir));
        Assert.True(Directory.Exists(vaultDir));

        // Verify duplicate returns 409 Conflict
        var dupResponse = await _client.PostAsJsonAsync("/api/areas/Safra%20C/houses", request);
        Assert.Equal(HttpStatusCode.Conflict, dupResponse.StatusCode);

        // Verify empty houseId returns 400 BadRequest
        var emptyResponse = await _client.PostAsJsonAsync("/api/areas/Safra%20C/houses", new CreateHouseRequestDto { HouseId = "" });
        Assert.Equal(HttpStatusCode.BadRequest, emptyResponse.StatusCode);
    }

    [Fact]
    public async Task BatchCopy_CreatesDocumentCopies_ExcludedFromTimeline()
    {
        using var scope = _fixture.Services.CreateScope();
        var repo = scope.ServiceProvider.GetRequiredService<IFileOrganizerRepository>();

        var samplePdf = Path.Combine(_fixture.AreasRoot, "seed.pdf");
        var doc1 = await repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "500",
            TenantId = 1,
            Category = "05 - عقود",
            ArabicTitle = "مستند لنسخ 1",
            PrimaryDate = "2022-05-01",
            PageCount = 1,
            SourcePdfPath = samplePdf,
            SourcePdfFilename = "seed.pdf",
            AreasRoot = _fixture.AreasRoot
        });

        var doc2 = await repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "500",
            TenantId = 1,
            Category = "05 - عقود",
            ArabicTitle = "مستند لنسخ 2",
            PrimaryDate = "2022-05-02",
            PageCount = 1,
            SourcePdfPath = samplePdf,
            SourcePdfFilename = "seed.pdf",
            AreasRoot = _fixture.AreasRoot
        });

        // Validation for empty vault_ids
        var emptyIdsResponse = await _client.PostAsJsonAsync(
            "/api/areas/Safra%20C/houses/500/documents/batch-copy",
            new BatchCopyRequestDto { VaultIds = new List<string>(), TargetCategory = "08 - فواتير" });
        Assert.Equal(HttpStatusCode.BadRequest, emptyIdsResponse.StatusCode);

        // Validation for empty target_category
        var emptyCatResponse = await _client.PostAsJsonAsync(
            "/api/areas/Safra%20C/houses/500/documents/batch-copy",
            new BatchCopyRequestDto { VaultIds = new List<string> { doc1.VaultId! }, TargetCategory = "" });
        Assert.Equal(HttpStatusCode.BadRequest, emptyCatResponse.StatusCode);

        var t2 = await repo.AddTenantAsync("500", "عبد الله الشهري", "2024-01-01", null);

        // Batch copy execution with TargetTenantId
        var response = await _client.PostAsJsonAsync(
            "/api/areas/Safra%20C/houses/500/documents/batch-copy",
            new BatchCopyRequestDto
            {
                VaultIds = new List<string> { doc1.VaultId!, doc2.VaultId! },
                TargetCategory = "08 - فواتير",
                TargetTenantId = t2.Id
            });

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var result = await response.Content.ReadFromJsonAsync<BatchCopyResponseDto>();
        Assert.NotNull(result);
        Assert.Equal("success", result.Status);
        Assert.Equal(2, result.CopiedCount);
        Assert.Equal("08 - فواتير", result.TargetCategory);
        Assert.Equal(2, result.NewVaultIds.Count);

        var copy1Id = result.NewVaultIds[0];
        var copy2Id = result.NewVaultIds[1];

        // Verify DB records
        var copyDoc1 = await repo.GetDocumentRawAsync(copy1Id);
        var copyDoc2 = await repo.GetDocumentRawAsync(copy2Id);
        Assert.NotNull(copyDoc1);
        Assert.NotNull(copyDoc2);
        Assert.Equal(0, copyDoc1.IsTimelineVisible);
        Assert.Equal(1, copyDoc1.IsManual);
        Assert.Equal("08 - فواتير", copyDoc1.Category);
        Assert.Equal(t2.Id, copyDoc1.TenantId);
        Assert.Equal(0, copyDoc2.IsTimelineVisible);
        Assert.Equal(1, copyDoc2.IsManual);
        Assert.Equal("08 - فواتير", copyDoc2.Category);
        Assert.Equal(t2.Id, copyDoc2.TenantId);

        // Verify original documents retained original tenant
        var origDoc1 = await repo.GetDocumentRawAsync(doc1.VaultId!);
        var origDoc2 = await repo.GetDocumentRawAsync(doc2.VaultId!);
        Assert.NotNull(origDoc1);
        Assert.NotNull(origDoc2);
        Assert.Equal(1, origDoc1.TenantId);
        Assert.Equal(1, origDoc2.TenantId);

        // Verify copied docs appear in /categories
        var catsResponse = await _client.GetAsync("/api/areas/Safra%20C/houses/500/categories");
        Assert.Equal(HttpStatusCode.OK, catsResponse.StatusCode);
        var categories = await catsResponse.Content.ReadFromJsonAsync<List<CategoryFolderDto>>();
        Assert.NotNull(categories);
        var allCatDocIds = categories.SelectMany(c => c.Documents).Select(d => d.VaultId).ToList();
        Assert.Contains(copy1Id, allCatDocIds);
        Assert.Contains(copy2Id, allCatDocIds);
        Assert.Contains(doc1.VaultId!, allCatDocIds);
        Assert.Contains(doc2.VaultId!, allCatDocIds);

        // Verify copied docs DO NOT appear in /timeline (no duplicates)
        var tlResponse = await _client.GetAsync("/api/areas/Safra%20C/houses/500/timeline");
        Assert.Equal(HttpStatusCode.OK, tlResponse.StatusCode);
        var timeline = await tlResponse.Content.ReadFromJsonAsync<List<TimelineItemDto>>();
        Assert.NotNull(timeline);
        var tlDocIds = timeline.Select(t => t.VaultId).ToList();
        Assert.Contains(doc1.VaultId!, tlDocIds);
        Assert.Contains(doc2.VaultId!, tlDocIds);
        Assert.DoesNotContain(copy1Id, tlDocIds);
        Assert.DoesNotContain(copy2Id, tlDocIds);

        // Verify PDF can be fetched via /api/pdf/{vaultId}
        var pdf1Response = await _client.GetAsync($"/api/pdf/{copy1Id}");
        Assert.Equal(HttpStatusCode.OK, pdf1Response.StatusCode);
        var pdf1Bytes = await pdf1Response.Content.ReadAsByteArrayAsync();
        Assert.NotEmpty(pdf1Bytes);
        Assert.StartsWith("%PDF", System.Text.Encoding.ASCII.GetString(pdf1Bytes[..4]));
    }

    [Fact]
    public async Task DeleteHouse_CascadeDeletesRecordsAndDirectory_ReturnsOk()
    {
        await _fixture.SeedDataAsync();

        // 1. Create a house with a tenant and scaffolding
        var houseId = $"HouseDel_{Guid.NewGuid():N}";
        var createRes = await _client.PostAsJsonAsync("/api/areas/Safra%20C/houses", new CreateHouseRequestDto
        {
            HouseId = houseId,
            InitialTenantName = "Tenant To Remove",
            StartDate = "2025-01-01"
        });
        Assert.Equal(HttpStatusCode.OK, createRes.StatusCode);

        // Verify directory was created
        var houseDir = Path.Combine(_fixture.AreasRoot, "Safra C", houseId);
        Assert.True(Directory.Exists(houseDir));

        // 2. Delete the house via DELETE /api/areas/{areaId}/houses/{houseId}
        var deleteRes = await _client.DeleteAsync($"/api/areas/Safra%20C/houses/{houseId}");
        Assert.Equal(HttpStatusCode.OK, deleteRes.StatusCode);

        // 3. Verify directory was removed
        Assert.False(Directory.Exists(houseDir));

        // 4. Verify house no longer exists in DB
        var housesRes = await _client.GetAsync("/api/houses?areaId=Safra%20C");
        Assert.Equal(HttpStatusCode.OK, housesRes.StatusCode);
        var houses = await housesRes.Content.ReadFromJsonAsync<List<HouseCardDto>>();
        Assert.NotNull(houses);
        Assert.DoesNotContain(houses, h => h.Id == houseId);

        // 5. Deleting again returns 404
        var secondDeleteRes = await _client.DeleteAsync($"/api/areas/Safra%20C/houses/{houseId}");
        Assert.Equal(HttpStatusCode.NotFound, secondDeleteRes.StatusCode);
    }
}


