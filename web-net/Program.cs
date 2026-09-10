using System.IO.Compression;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using FileOrganizer.Web.Common;
using FileOrganizer.Web.Data;
using FileOrganizer.Web.Models;
using Microsoft.AspNetCore.Http.Json;

var builder = WebApplication.CreateBuilder(args);

// Configure JSON options to match snake_case API contracts
builder.Services.Configure<JsonOptions>(options =>
{
    options.SerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower;
    options.SerializerOptions.DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull;
});

// Configure CORS
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

// Register DI services
builder.Services.AddSingleton<ISqliteDbConnectionFactory, SqliteDbConnectionFactory>();
builder.Services.AddScoped<IFileOrganizerRepository, FileOrganizerRepository>();

var app = builder.Build();

// Ensure DB schema is initialized
using (var scope = app.Services.CreateScope())
{
    var repo = scope.ServiceProvider.GetRequiredService<IFileOrganizerRepository>();
    try
    {
        await repo.EnsureSchemaAsync();
    }
    catch (Exception ex)
    {
        app.Logger.LogWarning(ex, "Schema initialization warning");
    }
}

app.UseCors();

// Static file serving from wwwroot/
app.UseDefaultFiles();
app.UseStaticFiles();

// ---------------------------------------------------------------------------
// Health check
// ---------------------------------------------------------------------------
app.MapGet("/api/health", () => Results.Ok(new { status = "healthy", timestamp = DateTime.UtcNow }));

// ---------------------------------------------------------------------------
// Tree API
// ---------------------------------------------------------------------------
app.MapGet("/api/tree", async (
    bool? include_categories,
    bool? includeCategories,
    bool? include_timeline,
    bool? includeTimeline,
    IFileOrganizerRepository repo) =>
{
    var incCat = (include_categories ?? false) || (includeCategories ?? false);
    var incTime = (include_timeline ?? false) || (includeTimeline ?? false);
    var tree = await repo.GetTreeAsync(incCat, incTime);
    return Results.Ok(tree);
});

// ---------------------------------------------------------------------------
// Houses API
// ---------------------------------------------------------------------------
app.MapGet("/api/houses", async (string? area_id, string? areaId, IFileOrganizerRepository repo) =>
{
    var targetArea = area_id ?? areaId;
    var houses = await repo.GetHousesAsync(targetArea);
    return Results.Ok(houses);
});

app.MapPost("/api/areas/{areaId}/houses", async (
    string areaId,
    CreateHouseRequestDto request,
    IFileOrganizerRepository repo,
    IConfiguration config) =>
{
    if (string.IsNullOrWhiteSpace(request.HouseId))
    {
        return Results.BadRequest(new { error = "House ID is required and cannot be empty." });
    }

    var cleanAreaId = !string.IsNullOrWhiteSpace(areaId) ? areaId.Trim() : (request.AreaId?.Trim() ?? "");
    if (string.IsNullOrWhiteSpace(cleanAreaId))
    {
        return Results.BadRequest(new { error = "Area ID is required and cannot be empty." });
    }

    var areasRoot = config["AREAS_ROOT_PATH"] ?? "../areas";
    try
    {
        var result = await repo.CreateHouseAsync(
            cleanAreaId,
            request.HouseId,
            request.InitialTenantName,
            request.StartDate,
            areasRoot
        );
        return Results.Ok(result);
    }
    catch (InvalidOperationException ex)
    {
        return Results.Conflict(new { error = ex.Message });
    }
    catch (ArgumentException ex)
    {
        return Results.BadRequest(new { error = ex.Message });
    }
});

// House profile / card
app.MapGet("/api/areas/{areaId}/houses/{houseId}", async (string areaId, string houseId, IFileOrganizerRepository repo) =>
{
    var profile = await repo.GetHouseProfileAsync(areaId, houseId);
    if (profile == null)
        return Results.NotFound(new { error = "House not found." });
    return Results.Ok(profile);
});

app.MapGet("/api/areas/{areaId}/houses/{houseId}/profile", async (string areaId, string houseId, IFileOrganizerRepository repo) =>
{
    var profile = await repo.GetHouseProfileAsync(areaId, houseId);
    if (profile == null)
        return Results.NotFound(new { error = "House not found." });
    return Results.Ok(profile);
});

// House vault listing
app.MapGet("/api/areas/{areaId}/houses/{houseId}/vault", async (string areaId, string houseId, IFileOrganizerRepository repo) =>
{
    var profile = await repo.GetHouseProfileAsync(areaId, houseId);
    if (profile == null)
        return Results.NotFound(new { error = "House not found." });

    var categories = await repo.GetCategoriesAsync(areaId, houseId);
    var allDocs = categories.SelectMany(c => c.Documents).ToList();
    return Results.Ok(allDocs);
});

app.MapGet("/api/houses/{houseId}/vault", async (string houseId, IFileOrganizerRepository repo) =>
{
    var categories = await repo.GetCategoriesAsync("", houseId);
    var allDocs = categories.SelectMany(c => c.Documents).ToList();
    return Results.Ok(allDocs);
});

// ---------------------------------------------------------------------------
// Export ZIP API
// ---------------------------------------------------------------------------
app.MapGet("/api/areas/{areaId}/houses/{houseId}/export-zip", async (
    string areaId,
    string houseId,
    int? tenantId,
    IFileOrganizerRepository repo,
    IConfiguration config) =>
{
    var profile = await repo.GetHouseProfileAsync(areaId, houseId);
    if (profile == null)
        return Results.NotFound(new { error = "House not found." });

    var categories = await repo.GetCategoriesAsync(areaId, houseId);
    var allDocs = categories.SelectMany(c => c.Documents).ToList();

    string? tenantName = null;
    if (tenantId.HasValue)
    {
        allDocs = allDocs.Where(d => d.TenantId == tenantId.Value).ToList();
        var tenants = await repo.GetTenantsAsync(houseId);
        tenantName = tenants.FirstOrDefault(t => t.Id == tenantId.Value)?.Name;
    }

    var areasRoot = config["AREAS_ROOT_PATH"] ?? config["AreasRoot"] ?? Path.Combine(Directory.GetCurrentDirectory(), "data");
    if (!Directory.Exists(areasRoot))
    {
        var envRoot = Environment.GetEnvironmentVariable("AREAS_ROOT_PATH") ?? Environment.GetEnvironmentVariable("AREAS_ROOT");
        if (!string.IsNullOrEmpty(envRoot) && Directory.Exists(envRoot))
            areasRoot = envRoot;
        else
            areasRoot = Directory.GetCurrentDirectory();
    }

    var houseDir = Path.Combine(areasRoot, areaId, houseId);
    var vaultDir = Path.Combine(houseDir, "vault");
    var sourceVaultDir = Path.Combine(houseDir, ".source_files", "vault");

    var memoryStream = new MemoryStream();
    using (var archive = new ZipArchive(memoryStream, ZipArchiveMode.Create, true))
    {
        var seenNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (var doc in allDocs)
        {
            var candidates = new[]
            {
                Path.Combine(vaultDir, $"doc_{doc.VaultId}.pdf"),
                Path.Combine(vaultDir, $"{doc.VaultId}.pdf"),
                Path.Combine(sourceVaultDir, $"doc_{doc.VaultId}.pdf"),
                Path.Combine(sourceVaultDir, $"{doc.VaultId}.pdf")
            };

            var filePath = candidates.FirstOrDefault(File.Exists);
            if (filePath == null) continue;

            var formattedCat = Constants.FormatCategoryWithPrefix(doc.Category);
            var safeCat = Regex.Replace(formattedCat, @"[\\/*?:""<>|]", "_").Trim();
            var safeTitle = Regex.Replace(doc.BriefArabicTitle ?? doc.Filename ?? doc.VaultId, @"[\\/*?:""<>|]", "_").Trim();
            var datePrefix = !string.IsNullOrEmpty(doc.Date) ? $"{doc.Date}_" : "";
            var baseName = $"{datePrefix}{safeTitle}.pdf";

            var archivePath = $"{safeCat}/{baseName}";
            int counter = 1;
            while (seenNames.Contains(archivePath))
            {
                archivePath = $"{safeCat}/{datePrefix}{safeTitle}_{counter}.pdf";
                counter++;
            }
            seenNames.Add(archivePath);

            var entry = archive.CreateEntry(archivePath, CompressionLevel.Optimal);
            using var entryStream = entry.Open();
            using var fileStream = File.OpenRead(filePath);
            await fileStream.CopyToAsync(entryStream);
        }

        if (seenNames.Count == 0)
        {
            var readme = archive.CreateEntry("README.txt");
            using var writer = new StreamWriter(readme.Open());
            await writer.WriteLineAsync($"No documents found in vault for Area {areaId}, House {houseId}.");
        }
    }

    memoryStream.Seek(0, SeekOrigin.Begin);
    var safeArea = Regex.Replace(areaId, @"[^\w\-]", "_");
    var safeHouse = Regex.Replace(houseId, @"[^\w\-]", "_");
    string filename;
    if (tenantId.HasValue)
    {
        if (!string.IsNullOrWhiteSpace(tenantName))
        {
            var safeTenant = Regex.Replace(tenantName, @"[^\w\-]", "_");
            filename = $"archive_{safeArea}_{safeHouse}_{safeTenant}.zip";
        }
        else
        {
            filename = $"archive_{safeArea}_{safeHouse}_tenant_{tenantId.Value}.zip";
        }
    }
    else
    {
        filename = $"archive_{safeArea}_{safeHouse}.zip";
    }

    return Results.File(memoryStream.ToArray(), "application/zip", filename);
});

// ---------------------------------------------------------------------------
// Export Combined Chronological PDF Dossier API
// ---------------------------------------------------------------------------
app.MapGet("/api/areas/{areaId}/houses/{houseId}/export-pdf", async (
    string areaId,
    string houseId,
    int? tenantId,
    IFileOrganizerRepository repo,
    IConfiguration config) =>
{
    var profile = await repo.GetHouseProfileAsync(areaId, houseId);
    if (profile == null)
        return Results.NotFound(new { error = "House not found." });

    var categories = await repo.GetCategoriesAsync(areaId, houseId);
    var allDocs = categories.SelectMany(c => c.Documents).ToList();

    string? tenantName = null;
    if (tenantId.HasValue)
    {
        allDocs = allDocs.Where(d => d.TenantId == tenantId.Value).ToList();
        var tenants = await repo.GetTenantsAsync(houseId);
        tenantName = tenants.FirstOrDefault(t => t.Id == tenantId.Value)?.Name;
    }

    // Descending chronological sort: newest/most recent dates first, empty/null dates last, tie-break by VaultId
    var sortedDocs = allDocs
        .OrderByDescending(d => !string.IsNullOrWhiteSpace(d.Date))
        .ThenByDescending(d => d.Date)
        .ThenBy(d => d.VaultId)
        .ToList();

    var areasRoot = config["AREAS_ROOT_PATH"] ?? config["AreasRoot"] ?? Path.Combine(Directory.GetCurrentDirectory(), "data");
    if (!Directory.Exists(areasRoot))
    {
        var envRoot = Environment.GetEnvironmentVariable("AREAS_ROOT_PATH") ?? Environment.GetEnvironmentVariable("AREAS_ROOT");
        if (!string.IsNullOrEmpty(envRoot) && Directory.Exists(envRoot))
            areasRoot = envRoot;
        else
            areasRoot = Directory.GetCurrentDirectory();
    }

    var houseDir = Path.Combine(areasRoot, areaId, houseId);
    var vaultDir = Path.Combine(houseDir, "vault");
    var sourceVaultDir = Path.Combine(houseDir, ".source_files", "vault");

    using var outputDoc = new PdfSharpCore.Pdf.PdfDocument();

    foreach (var doc in sortedDocs)
    {
        var candidates = new[]
        {
            Path.Combine(vaultDir, $"doc_{doc.VaultId}.pdf"),
            Path.Combine(vaultDir, $"{doc.VaultId}.pdf"),
            Path.Combine(sourceVaultDir, $"doc_{doc.VaultId}.pdf"),
            Path.Combine(sourceVaultDir, $"{doc.VaultId}.pdf")
        };

        var filePath = candidates.FirstOrDefault(File.Exists);
        if (filePath != null)
        {
            try
            {
                using var inputDoc = PdfSharpCore.Pdf.IO.PdfReader.Open(filePath, PdfSharpCore.Pdf.IO.PdfDocumentOpenMode.Import);
                for (int i = 0; i < inputDoc.PageCount; i++)
                {
                    outputDoc.AddPage(inputDoc.Pages[i]);
                }
            }
            catch
            {
                // Ignore unreadable or corrupted PDF
            }
        }
    }

    if (outputDoc.PageCount == 0)
    {
        outputDoc.AddPage();
    }

    using var ms = new MemoryStream();
    outputDoc.Save(ms, false);

    var safeArea = Regex.Replace(areaId, @"[^\w\-]", "_");
    var safeHouse = Regex.Replace(houseId, @"[^\w\-]", "_");
    string filename;
    if (tenantId.HasValue)
    {
        if (!string.IsNullOrWhiteSpace(tenantName))
        {
            var safeTenant = Regex.Replace(tenantName, @"[^\w\-]", "_");
            filename = $"archive_{safeArea}_{safeHouse}_{safeTenant}.pdf";
        }
        else
        {
            filename = $"archive_{safeArea}_{safeHouse}_tenant_{tenantId.Value}.pdf";
        }
    }
    else
    {
        filename = $"archive_{safeArea}_{safeHouse}.pdf";
    }

    return Results.File(ms.ToArray(), "application/pdf", filename);
});

// ---------------------------------------------------------------------------
// Timeline API
// ---------------------------------------------------------------------------
app.MapGet("/api/areas/{areaId}/houses/{houseId}/timeline", async (
    string areaId,
    string houseId,
    string? tenant_name,
    string? tenantName,
    IFileOrganizerRepository repo) =>
{
    var tName = tenant_name ?? tenantName;
    var timeline = await repo.GetTimelineAsync(areaId, houseId, tName);
    return Results.Ok(timeline);
});

// ---------------------------------------------------------------------------
// Categories API
// ---------------------------------------------------------------------------
app.MapGet("/api/areas/{areaId}/houses/{houseId}/categories", async (string areaId, string houseId, IFileOrganizerRepository repo) =>
{
    var categories = await repo.GetCategoriesAsync(areaId, houseId);
    return Results.Ok(categories);
});

app.MapDelete("/api/areas/{areaId}/houses/{houseId}/categories/{categoryName}", async (
    string areaId,
    string houseId,
    string categoryName,
    IFileOrganizerRepository repo) =>
{
    var reassigned = await repo.DeleteCategoryAsync(houseId, categoryName);
    return Results.Ok(new
    {
        status = "success",
        deleted_category = categoryName.Trim(),
        reassigned_docs = reassigned
    });
});

// ---------------------------------------------------------------------------
// Tenants API
// ---------------------------------------------------------------------------
app.MapGet("/api/areas/{areaId}/houses/{houseId}/tenants", async (string areaId, string houseId, IFileOrganizerRepository repo) =>
{
    var tenants = await repo.GetTenantsAsync(houseId);
    return Results.Ok(tenants);
});

app.MapPost("/api/areas/{areaId}/houses/{houseId}/tenants", async (
    string areaId,
    string houseId,
    TenantBulkUpdateRequestDto payload,
    IFileOrganizerRepository repo) =>
{
    var result = await repo.BulkUpdateTenantsAsync(houseId, payload.Tenants, payload.Reallocate);
    return Results.Ok(result);
});

app.MapPost("/api/areas/{areaId}/houses/{houseId}/reallocate", async (
    string areaId,
    string houseId,
    IFileOrganizerRepository repo) =>
{
    var result = await repo.BulkUpdateTenantsAsync(houseId, Array.Empty<TenantDto>(), reallocate: true);
    return Results.Ok(result);
});

// ---------------------------------------------------------------------------
// Search API
// ---------------------------------------------------------------------------
app.MapGet("/api/search", async (string? q, int? limit, IFileOrganizerRepository repo) =>
{
    if (string.IsNullOrWhiteSpace(q))
        return Results.Ok(Array.Empty<SearchResultDto>());

    var results = await repo.SearchAsync(q.Trim(), limit ?? 50);
    return Results.Ok(results);
});

// ---------------------------------------------------------------------------
// PDF Streaming API
// ---------------------------------------------------------------------------
app.MapGet("/api/pdf/{vaultId}", async (string vaultId, IFileOrganizerRepository repo, IConfiguration config) =>
{
    var areasRoot = config["AREAS_ROOT_PATH"] ?? "../areas";
    var doc = await repo.GetDocumentDetailsAsync(vaultId, areasRoot);

    string? filePath = doc?.PhysicalPath;
    if (string.IsNullOrEmpty(filePath) || !File.Exists(filePath))
    {
        var candidates = new[]
        {
            doc != null ? Path.Combine(areasRoot, doc.AreaId ?? "", doc.HouseId ?? "", "vault", $"doc_{vaultId}.pdf") : "",
            doc != null ? Path.Combine(areasRoot, doc.AreaId ?? "", doc.HouseId ?? "", "vault", $"{vaultId}.pdf") : "",
            doc != null ? Path.Combine(areasRoot, doc.AreaId ?? "", doc.HouseId ?? "", ".source_files", "vault", $"doc_{vaultId}.pdf") : "",
            doc != null ? Path.Combine(areasRoot, doc.AreaId ?? "", doc.HouseId ?? "", ".source_files", "vault", $"{vaultId}.pdf") : "",
            (doc?.BatchFilePath != null && doc.AreaId != null && doc.HouseId != null)
                ? Path.Combine(areasRoot, doc.AreaId, doc.HouseId, doc.BatchFilePath)
                : ""
        };

        filePath = candidates.FirstOrDefault(File.Exists);
    }

    if (string.IsNullOrEmpty(filePath) || !File.Exists(filePath))
        return Results.NotFound(new { error = "Resource not found.", solution = "Verify the endpoint URL and the resource ID." });

    return Results.File(filePath, "application/pdf", enableRangeProcessing: true);
});

app.MapGet("/api/areas/{areaId}/houses/{houseId}/pdf/{vaultId}", async (
    string areaId,
    string houseId,
    string vaultId,
    IFileOrganizerRepository repo,
    IConfiguration config) =>
{
    var areasRoot = config["AREAS_ROOT_PATH"] ?? "../areas";
    var cleanHouseId = TextUtils.ExtractHouseNumber(houseId);

    string? filePath = null;

    if (vaultId.StartsWith("fs_"))
    {
        try
        {
            var b64 = vaultId[3..];
            b64 += new string('=', (4 - b64.Length % 4) % 4);
            var relPath = Encoding.UTF8.GetString(Convert.FromBase64String(b64.Replace('-', '+').Replace('_', '/')));
            var cand = Path.Combine(areasRoot, areaId, houseId, relPath);
            if (File.Exists(cand)) filePath = cand;
        }
        catch { }
    }

    if (filePath == null)
    {
        var candidates = new[]
        {
            Path.Combine(areasRoot, areaId, houseId, "vault", $"doc_{vaultId}.pdf"),
            Path.Combine(areasRoot, areaId, houseId, "vault", $"{vaultId}.pdf"),
            Path.Combine(areasRoot, areaId, cleanHouseId, "vault", $"doc_{vaultId}.pdf"),
            Path.Combine(areasRoot, areaId, cleanHouseId, "vault", $"{vaultId}.pdf"),
            Path.Combine(areasRoot, areaId, houseId, ".source_files", "vault", $"doc_{vaultId}.pdf"),
            Path.Combine(areasRoot, areaId, houseId, ".source_files", "vault", $"{vaultId}.pdf"),
            Path.Combine(areasRoot, areaId, cleanHouseId, ".source_files", "vault", $"doc_{vaultId}.pdf"),
            Path.Combine(areasRoot, areaId, cleanHouseId, ".source_files", "vault", $"{vaultId}.pdf")
        };

        filePath = candidates.FirstOrDefault(File.Exists);
    }

    if (filePath == null)
    {
        var doc = await repo.GetDocumentDetailsAsync(vaultId, areasRoot);
        if (doc?.PhysicalPath != null && File.Exists(doc.PhysicalPath))
        {
            filePath = doc.PhysicalPath;
        }
    }

    if (string.IsNullOrEmpty(filePath) || !File.Exists(filePath))
        return Results.NotFound(new { error = "Resource not found.", solution = "Verify the endpoint URL and the resource ID." });

    return Results.File(filePath, "application/pdf", enableRangeProcessing: true);
});

// ---------------------------------------------------------------------------
// Document Management API
// ---------------------------------------------------------------------------
app.MapGet("/api/areas/{areaId}/houses/{houseId}/documents/{vaultId}", async (
    string areaId,
    string houseId,
    string vaultId,
    IFileOrganizerRepository repo,
    IConfiguration config) =>
{
    var areasRoot = config["AREAS_ROOT_PATH"] ?? "../areas";
    var doc = await repo.GetDocumentDetailsAsync(vaultId, areasRoot);
    if (doc == null)
        return Results.NotFound(new { error = "Document not found." });
    return Results.Ok(doc);
});

app.MapGet("/api/areas/{areaId}/houses/{houseId}/documents/{vaultId}/metadata", async (
    string areaId,
    string houseId,
    string vaultId,
    IFileOrganizerRepository repo,
    IConfiguration config) =>
{
    var areasRoot = config["AREAS_ROOT_PATH"] ?? "../areas";
    var doc = await repo.GetDocumentDetailsAsync(vaultId, areasRoot);
    if (doc == null)
        return Results.NotFound(new { error = "Document not found." });
    return Results.Ok(doc);
});

app.MapPatch("/api/areas/{areaId}/houses/{houseId}/documents/{vaultId}", async (
    string areaId,
    string houseId,
    string vaultId,
    DocumentUpdateRequestDto payload,
    IFileOrganizerRepository repo) =>
{
    var result = await repo.UpdateDocumentAsync(
        vaultId,
        arabicTitle: payload.ArabicTitle,
        category: payload.Category,
        tenantId: payload.TenantId,
        primaryDate: payload.PrimaryDate,
        isManual: payload.IsManual ?? 1,
        notes: payload.Notes);

    if (result == null)
        return Results.NotFound(new { error = "Document not found." });
    return Results.Ok(result);
});

app.MapPatch("/api/areas/{areaId}/houses/{houseId}/documents/{vaultId}/notes", async (
    string areaId,
    string houseId,
    string vaultId,
    DocumentNotesRequestDto payload,
    IFileOrganizerRepository repo) =>
{
    var result = await repo.UpdateDocumentNotesAsync(vaultId, payload.Notes);
    if (result == null)
        return Results.NotFound(new { error = "Document not found." });
    return Results.Ok(result);
});

app.MapPatch("/api/areas/{areaId}/houses/{houseId}/documents/{vaultId}/tenant", async (
    string areaId,
    string houseId,
    string vaultId,
    DocumentTenantUpdateRequestDto payload,
    IFileOrganizerRepository repo) =>
{
    var result = await repo.UpdateDocumentTenantAsync(vaultId, payload.TenantId);
    if (result == null)
        return Results.NotFound(new { error = "Document not found." });
    return Results.Ok(result);
});

app.MapPost("/api/areas/{areaId}/houses/{houseId}/documents/{vaultId}/copy", async (
    string areaId,
    string houseId,
    string vaultId,
    DocumentCopyRequestDto payload,
    IFileOrganizerRepository repo,
    IConfiguration config) =>
{
    var areasRoot = config["AREAS_ROOT_PATH"] ?? "../areas";
    var result = await repo.CopyDocumentAsync(
        vaultId,
        targetCategory: payload.TargetCategory,
        targetTenantId: payload.TargetTenantId,
        targetTitle: payload.TargetTitle,
        areasRoot: areasRoot);

    if (result == null)
        return Results.NotFound(new { error = "Source document not found." });
    return Results.Ok(result);
});

app.MapPost("/api/areas/{areaId}/houses/{houseId}/documents/{vaultId}/reset-lock", async (
    string areaId,
    string houseId,
    string vaultId,
    IFileOrganizerRepository repo) =>
{
    var result = await repo.ResetDocumentLockAsync(vaultId);
    if (result == null)
        return Results.NotFound(new { error = "Document not found." });
    return Results.Ok(result);
});

app.MapDelete("/api/areas/{areaId}/houses/{houseId}/documents/{vaultId}", async (
    string areaId,
    string houseId,
    string vaultId,
    IFileOrganizerRepository repo,
    IConfiguration config) =>
{
    var areasRoot = config["AREAS_ROOT_PATH"] ?? "../areas";
    var success = await repo.DeleteDocumentAsync(areaId, houseId, vaultId, areasRoot);
    if (!success)
        return Results.NotFound(new { status = "error", message = "Document not found" });

    return Results.Ok(new { status = "success", message = $"Document {vaultId} deleted" });
});

app.MapPost("/api/areas/{areaId}/houses/{houseId}/documents/batch-delete", async (
    string areaId,
    string houseId,
    BatchDeleteRequestDto dto,
    IFileOrganizerRepository repo,
    IConfiguration config) =>
{
    if (dto.VaultIds == null || dto.VaultIds.Count == 0)
        return Results.BadRequest(new { error = "vault_ids must not be empty." });

    var areasRoot = config["AREAS_ROOT_PATH"] ?? "../areas";
    var result = await repo.BatchDeleteDocumentsAsync(areaId, houseId, dto.VaultIds, areasRoot);
    return Results.Ok(result);
});

app.MapPost("/api/areas/{areaId}/houses/{houseId}/documents/batch-move", async (
    string areaId,
    string houseId,
    BatchMoveRequestDto dto,
    IFileOrganizerRepository repo) =>
{
    if (dto.VaultIds == null || dto.VaultIds.Count == 0)
        return Results.BadRequest(new { error = "vault_ids must not be empty." });

    if (string.IsNullOrWhiteSpace(dto.TargetCategory))
        return Results.BadRequest(new { error = "target_category must not be empty." });

    var result = await repo.BatchMoveDocumentsAsync(areaId, houseId, dto.VaultIds, dto.TargetCategory);
    return Results.Ok(result);
});

app.MapPost("/api/areas/{areaId}/houses/{houseId}/documents/batch-copy", async (
    string areaId,
    string houseId,
    BatchCopyRequestDto dto,
    IFileOrganizerRepository repo,
    IConfiguration config) =>
{
    if (dto.VaultIds == null || dto.VaultIds.Count == 0)
        return Results.BadRequest(new { error = "vault_ids must not be empty." });

    if (string.IsNullOrWhiteSpace(dto.TargetCategory))
        return Results.BadRequest(new { error = "target_category must not be empty." });

    var areasRoot = config["AREAS_ROOT_PATH"] ?? "../areas";
    var result = await repo.BatchCopyDocumentsAsync(areaId, houseId, dto.VaultIds, dto.TargetCategory, areasRoot);
    return Results.Ok(result);
});

// ---------------------------------------------------------------------------
// Ingest API
// ---------------------------------------------------------------------------
app.MapPost("/api/ingest/preview-ai", async (
    HttpRequest request,
    IFileOrganizerRepository repo) =>
{
    if (!request.HasFormContentType)
        return Results.BadRequest(new { error = "Expected multipart/form-data content type." });

    var form = await request.ReadFormAsync();
    var file = form.Files["file"] ?? form.Files.FirstOrDefault();
    if (file == null || file.Length == 0)
        return Results.BadRequest(new { error = "Uploaded file is empty or missing." });

    if (!file.FileName.EndsWith(".pdf", StringComparison.OrdinalIgnoreCase))
        return Results.BadRequest(new { error = "Invalid file type. Only PDF files (.pdf) are supported." });

    using var stream = file.OpenReadStream();
    byte[] header = new byte[4];
    int bytesRead = await stream.ReadAsync(header, 0, 4);
    if (bytesRead < 4 || header[0] != '%' || header[1] != 'P' || header[2] != 'D' || header[3] != 'F')
        return Results.BadRequest(new { error = "Invalid file format. File does not begin with %PDF header." });

    stream.Position = 0;
    using var ms = new MemoryStream();
    await stream.CopyToAsync(ms);
    var bytes = ms.ToArray();

    var areaId = form["area_id"].FirstOrDefault();
    var houseId = form["house_id"].FirstOrDefault();

    var preview = await AIPreviewExtractor.ExtractAsync(bytes, file.FileName, areaId, houseId, repo);
    return Results.Ok(preview);
});

app.MapPost("/api/ingest", async (
    HttpRequest request,
    IFileOrganizerRepository repo,
    IConfiguration config) =>
{
    if (!request.HasFormContentType)
        return Results.BadRequest(new { error = "Expected multipart/form-data content type." });

    var form = await request.ReadFormAsync();
    var file = form.Files["file"] ?? form.Files.FirstOrDefault();
    if (file == null || file.Length == 0)
        return Results.BadRequest(new { error = "Uploaded file is empty or missing." });

    if (!file.FileName.EndsWith(".pdf", StringComparison.OrdinalIgnoreCase))
        return Results.BadRequest(new { error = "Invalid file type. Only PDF files (.pdf) are supported." });

    using var stream = file.OpenReadStream();
    byte[] header = new byte[4];
    int bytesRead = await stream.ReadAsync(header, 0, 4);
    if (bytesRead < 4 || header[0] != '%' || header[1] != 'P' || header[2] != 'D' || header[3] != 'F')
        return Results.BadRequest(new { error = "Invalid file format. File does not begin with %PDF header." });

    var mode = form["mode"].FirstOrDefault() ?? "manual";
    var areaId = form["area_id"].FirstOrDefault() ?? "";
    var houseId = form["house_id"].FirstOrDefault() ?? "";

    if (string.IsNullOrWhiteSpace(areaId) || string.IsNullOrWhiteSpace(houseId))
        return Results.BadRequest(new { error = "area_id and house_id are required." });

    var cleanHouseId = TextUtils.ExtractHouseNumber(houseId);

    int? tenantId = null;
    if (int.TryParse(form["tenant_id"].FirstOrDefault(), out var tid))
        tenantId = tid;

    var tenantName = form["tenant_name"].FirstOrDefault();
    var category = form["category"].FirstOrDefault();
    var arabicTitle = form["arabic_title"].FirstOrDefault();
    var primaryDate = form["primary_date"].FirstOrDefault();
    var notes = form["notes"].FirstOrDefault();

    // Resolve tenant
    int resolvedTenantId;
    if (tenantId.HasValue)
    {
        var tenants = await repo.GetTenantsAsync(cleanHouseId);
        var t = tenants.FirstOrDefault(x => x.Id == tenantId.Value);
        if (t == null)
            return Results.BadRequest(new { error = $"Tenant ID {tenantId.Value} does not exist or does not belong to house '{cleanHouseId}'." });
        resolvedTenantId = tenantId.Value;
    }
    else if (!string.IsNullOrWhiteSpace(tenantName))
    {
        var tenants = await repo.GetTenantsAsync(cleanHouseId);
        var matched = tenants.FirstOrDefault(x => string.Equals(x.Name.Trim(), tenantName.Trim(), StringComparison.OrdinalIgnoreCase));
        if (matched != null && matched.Id.HasValue)
        {
            resolvedTenantId = matched.Id.Value;
        }
        else
        {
            var newT = await repo.AddTenantAsync(cleanHouseId, tenantName.Trim(), primaryDate ?? DateTime.Today.ToString("yyyy-MM-dd"));
            resolvedTenantId = newT.Id;
        }
    }
    else
    {
        var tenants = await repo.GetTenantsAsync(cleanHouseId);
        if (tenants.Count > 0 && tenants[0].Id.HasValue)
        {
            resolvedTenantId = tenants[0].Id!.Value;
        }
        else
        {
            var defT = await repo.AddTenantAsync(cleanHouseId, "Default Tenant", "1970-01-01");
            resolvedTenantId = defT.Id;
        }
    }

    var vaultId = Guid.NewGuid().ToString("N");
    var areasRootPath = config["AREAS_ROOT_PATH"] ?? "../areas";

    var tempFile = Path.GetTempFileName();
    try
    {
        stream.Position = 0;
        await using (var fs = File.Create(tempFile))
        {
            await stream.CopyToAsync(fs);
        }

        var result = await repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = areaId,
            HouseId = cleanHouseId,
            TenantId = resolvedTenantId,
            Category = string.IsNullOrWhiteSpace(category) ? "13 - رسائل متنوعة" : category,
            ArabicTitle = string.IsNullOrWhiteSpace(arabicTitle) ? Path.GetFileNameWithoutExtension(file.FileName) : arabicTitle,
            PrimaryDate = primaryDate,
            Notes = notes,
            PageCount = 1,
            SourcePdfFilename = file.FileName,
            SourcePdfPath = tempFile,
            VaultId = vaultId,
            Mode = mode,
            AreasRoot = areasRootPath
        });

        return Results.Ok(result);
    }
    finally
    {
        if (File.Exists(tempFile))
        {
            try { File.Delete(tempFile); } catch { }
        }
    }
});

// ---------------------------------------------------------------------------
// Database Inspector API
// ---------------------------------------------------------------------------
app.MapGet("/api/db/info", async (IFileOrganizerRepository repo) =>
{
    var stats = await repo.GetDbStatsAsync();
    return Results.Ok(stats);
});

app.MapGet("/api/db/inspector/stats", async (IFileOrganizerRepository repo) =>
{
    var stats = await repo.GetDbStatsAsync();
    return Results.Ok(stats);
});

app.MapGet("/api/db/tables/{tableName}", async (
    string tableName,
    int? limit,
    int? offset,
    string? search,
    IFileOrganizerRepository repo) =>
{
    try
    {
        var data = await repo.GetDbTableDataAsync(tableName, limit ?? 50, offset ?? 0, search);
        return Results.Ok(data);
    }
    catch (ArgumentException ex)
    {
        return Results.BadRequest(new { error = ex.Message });
    }
});

app.MapGet("/api/db/inspector/{tableName}", async (
    string tableName,
    int? limit,
    int? offset,
    string? search,
    IFileOrganizerRepository repo) =>
{
    try
    {
        var data = await repo.GetDbTableDataAsync(tableName, limit ?? 50, offset ?? 0, search);
        return Results.Ok(data);
    }
    catch (ArgumentException ex)
    {
        return Results.BadRequest(new { error = ex.Message });
    }
});

// ---------------------------------------------------------------------------
// SPA Fallback Routing
// ---------------------------------------------------------------------------
app.MapFallbackToFile("index.html");

app.Run();

public partial class Program { }
