using FileOrganizer.Web.Common;
using FileOrganizer.Web.Data;
using FileOrganizer.Web.Models;
using Dapper;
using Xunit;

namespace FileOrganizer.Tests;

public class RepositoryTests : IDisposable
{
    private readonly string _dbPath;
    private readonly ISqliteDbConnectionFactory _factory;
    private readonly FileOrganizerRepository _repo;

    public RepositoryTests()
    {
        _dbPath = Path.Combine(Path.GetTempPath(), $"test_organizer_{Guid.NewGuid():N}.db");
        _factory = new SqliteDbConnectionFactory(dbPath: _dbPath);
        _repo = new FileOrganizerRepository(_factory);
        _repo.EnsureSchemaAsync().GetAwaiter().GetResult();
    }

    public void Dispose()
    {
        try
        {
            if (File.Exists(_dbPath))
                File.Delete(_dbPath);

            var walPath = $"{_dbPath}-wal";
            if (File.Exists(walPath))
                File.Delete(walPath);

            var shmPath = $"{_dbPath}-shm";
            if (File.Exists(shmPath))
                File.Delete(shmPath);
        }
        catch
        {
            // Ignore cleanup errors for temp db
        }
    }

    [Fact]
    public async Task GetTreeAsync_ReturnsHierarchicalTreeWithTenureMetrics()
    {
        // Arrange
        await _repo.AddAreaAsync("Safra C", "SC");
        await _repo.AddHouseAsync("514", "Safra C");
        
        var currentYear = DateTime.Now.Year;
        var startYearShort = currentYear - 2;
        var t1 = await _repo.AddTenantAsync("514", "أحمد علي", $"{startYearShort}-01-01", null);

        var ingestReq = new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "514",
            TenantId = t1.Id,
            Category = "عقود",
            ArabicTitle = "عقد إيجار تجريبي",
            PrimaryDate = $"{startYearShort}-05-10",
            PageCount = 2
        };
        await _repo.AddManualDocumentAsync(ingestReq);

        // Act
        var tree = await _repo.GetTreeAsync();

        // Assert
        Assert.NotEmpty(tree);
        var area = tree.FirstOrDefault(a => a.Name == "Safra C");
        Assert.NotNull(area);
        Assert.Equal("area", area.Type);
        Assert.NotNull(area.Children);

        var house = area.Children.FirstOrDefault(h => h.Id == "514");
        Assert.NotNull(house);
        Assert.Equal("514", house.Name);
        Assert.Equal("أحمد علي", house.CurrentTenant);
        Assert.Equal("short", house.DurationCategory);
        Assert.Contains($"Since {startYearShort}", house.Subtitle);
        Assert.Equal(1, house.TotalDocuments);
        Assert.NotNull(house.Children);

        var tenant = house.Children.FirstOrDefault(t => t.Name == "أحمد علي");
        Assert.NotNull(tenant);
        Assert.Equal("short", tenant.DurationCategory);
        Assert.Equal($"{startYearShort} - Present", tenant.Subtitle);
    }

    [Fact]
    public async Task GetHousesAsync_ReturnsTenureColorCoding()
    {
        // Arrange: 3 houses with short (<5y green), medium (5-10y yellow), long (>10y red)
        await _repo.AddAreaAsync("Safra C", "SC");
        await _repo.AddHouseAsync("101", "Safra C");
        await _repo.AddHouseAsync("102", "Safra C");
        await _repo.AddHouseAsync("103", "Safra C");

        var currentYear = DateTime.Now.Year;
        // House 101: 2 years -> short (<5y) -> green
        await _repo.AddTenantAsync("101", "Tenant Green", $"{currentYear - 2}-01-01", null);

        // House 102: 7 years -> medium (5-10y) -> yellow
        await _repo.AddTenantAsync("102", "Tenant Yellow", $"{currentYear - 7}-01-01", null);

        // House 103: 15 years -> long (>10y) -> red
        await _repo.AddTenantAsync("103", "Tenant Red", $"{currentYear - 15}-01-01", null);

        // Act
        var houses = await _repo.GetHousesAsync("Safra C");

        // Assert
        Assert.Equal(3, houses.Count);

        var h101 = houses.First(h => h.Id == "101");
        Assert.Equal("short", h101.DurationCategory);
        Assert.Equal("green", h101.TenureColor);
        Assert.Equal(2, h101.TenureDurationYears);

        var h102 = houses.First(h => h.Id == "102");
        Assert.Equal("medium", h102.DurationCategory);
        Assert.Equal("yellow", h102.TenureColor);
        Assert.Equal(7, h102.TenureDurationYears);

        var h103 = houses.First(h => h.Id == "103");
        Assert.Equal("long", h103.DurationCategory);
        Assert.Equal("red", h103.TenureColor);
        Assert.Equal(15, h103.TenureDurationYears);
    }

    [Fact]
    public async Task GetHouseProfileAsync_ReturnsProfileTenancyRegisterAndArabicStrings()
    {
        // Arrange
        await _repo.AddAreaAsync("Safra C", "SC");
        await _repo.AddHouseAsync("514", "Safra C");

        var tPast = await _repo.AddTenantAsync("514", "سعيد خليل", "2015-01-01", "2019-12-31");
        var tActive = await _repo.AddTenantAsync("514", "محمد الشروقي", "2020-01-01", null);

        await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "514",
            TenantId = tActive.Id,
            Category = "05 - عقود",
            ArabicTitle = "عقد إيجار سنوي",
            PrimaryDate = "2020-02-01",
            PageCount = 3
        });

        await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "514",
            TenantId = tPast.Id,
            Category = "06 - كهرباء وماء",
            ArabicTitle = "فاتورة قديمة",
            PrimaryDate = "2017-06-15",
            PageCount = 1
        });

        // Act
        var profile = await _repo.GetHouseProfileAsync("Safra C", "514");

        // Assert
        Assert.NotNull(profile);
        Assert.Equal("514", profile.HouseId);
        Assert.Equal("Safra C", profile.AreaId);
        Assert.Equal("محمد الشروقي", profile.ActiveResident);

        Assert.Equal(2, profile.Tenants.Count);
        var activeItem = profile.Tenants.First(t => t.Id == tActive.Id);
        Assert.True(activeItem.IsActive);
        Assert.Contains("بدء الإيجار 2020", activeItem.DurationStrAr);
        Assert.Equal(1, activeItem.DocumentCount);

        var pastItem = profile.Tenants.First(t => t.Id == tPast.Id);
        Assert.False(pastItem.IsActive);
        Assert.Contains("فترة الإيجار: 2017", pastItem.DurationStrAr);

        Assert.Equal(2, profile.Archive.TotalDocuments);
        Assert.Equal(4, profile.Archive.TotalPages);
        Assert.Equal(2, profile.Archive.BatchCount);
        Assert.Equal("2017-06-15", profile.Archive.OldestDate);
        Assert.Equal("2020-02-01", profile.Archive.NewestDate);
        Assert.NotEmpty(profile.Archive.Categories);
    }

    [Fact]
    public async Task GetTimelineAsync_ReturnsChronologicalDocuments()
    {
        // Arrange
        await _repo.AddAreaAsync("Safra C");
        await _repo.AddHouseAsync("514", "Safra C");
        var t = await _repo.AddTenantAsync("514", "خالد يوسف", "2021-01-01", null);

        await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "514",
            TenantId = t.Id,
            Category = "عقود",
            ArabicTitle = "عقد إيجار 2021",
            PrimaryDate = "2021-01-15",
            PageCount = 1
        });

        await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "514",
            TenantId = t.Id,
            Category = "كهرباء وماء",
            ArabicTitle = "فاتورة 2023",
            PrimaryDate = "2023-04-10",
            PageCount = 1
        });

        // Act
        var timeline = await _repo.GetTimelineAsync("Safra C", "514");

        // Assert
        Assert.Equal(2, timeline.Count);
        // Chronological descending: 2023 first, then 2021
        Assert.Equal("عقد إيجار 2021", timeline[1].BriefArabicTitle);
        Assert.Equal("فاتورة 2023", timeline[0].BriefArabicTitle);
        Assert.Equal("خالد يوسف", timeline[0].PrimaryTenant);
        Assert.Equal(1, timeline[0].IsManual);
    }

    [Fact]
    public async Task GetCategoriesAsync_ReturnsStandardAndCustomFolders()
    {
        // Arrange
        await _repo.AddAreaAsync("Safra C");
        await _repo.AddHouseAsync("514", "Safra C");
        var t = await _repo.AddTenantAsync("514", "علي حسن", "2022-01-01", null);

        await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "514",
            TenantId = t.Id,
            Category = "عقود",
            ArabicTitle = "عقد إيجار رئيسي",
            PrimaryDate = "2022-01-05",
            PageCount = 2
        });

        await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "514",
            TenantId = t.Id,
            Category = "14 - تصاريح بناء",
            ArabicTitle = "تصريح بناء غرفة",
            PrimaryDate = "2023-02-20",
            PageCount = 1
        });

        // Act
        var folders = await _repo.GetCategoriesAsync("Safra C", "514");

        // Assert
        Assert.NotEmpty(folders);
        var contractFolder = folders.FirstOrDefault(f => f.Name == "05 - عقود");
        Assert.NotNull(contractFolder);
        Assert.Equal(1, contractFolder.DocumentCount);
        Assert.Single(contractFolder.Documents);
        Assert.Equal("عقد إيجار رئيسي", contractFolder.Documents[0].BriefArabicTitle);

        var customFolder = folders.FirstOrDefault(f => f.Name == "14 - تصاريح بناء");
        Assert.NotNull(customFolder);
        Assert.Equal(1, customFolder.DocumentCount);
    }

    [Fact]
    public async Task GetTenantsAsync_ReturnsDeduplicatedTenants()
    {
        // Arrange
        await _repo.AddAreaAsync("Safra C");
        await _repo.AddHouseAsync("514", "Safra C");

        await _repo.AddTenantAsync("514", "فاضل عباس", "2018-01-01", "2020-01-01");
        await _repo.AddTenantAsync("514", "فاضل عباس", "2020-01-02", null); // Same name, later period
        await _repo.AddTenantAsync("514", "جاسم محمد", "2015-01-01", "2017-12-31");

        // Act
        var tenants = await _repo.GetTenantsAsync("514");

        // Assert: Distinct by name, active/latest first
        Assert.Equal(2, tenants.Count);
        Assert.Equal("فاضل عباس", tenants[0].Name);
        Assert.Equal("جاسم محمد", tenants[1].Name);
    }

    [Fact]
    public async Task SearchAsync_SearchesHousesTenantsDocumentsAndPages()
    {
        // Arrange
        await _repo.AddAreaAsync("Safra C");
        await _repo.AddHouseAsync("514", "Safra C");
        var t = await _repo.AddTenantAsync("514", "عبدالله إبراهيم", "2020-01-01", null);

        var ingest = await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "514",
            TenantId = t.Id,
            Category = "05 - عقود",
            ArabicTitle = "اتفاقية صيانة المكيفات",
            PrimaryDate = "2022-08-14",
            Notes = "ملاحظات إضافية بخصوص الضمان",
            PageCount = 1
        });

        // Act & Assert 1: Search house
        var searchHouse = await _repo.SearchAsync("514");
        Assert.Contains(searchHouse, r => r.Type == "house" && r.Id == "514");

        // Act & Assert 2: Search tenant (exact and phonetic)
        var searchTenant = await _repo.SearchAsync("عبدالله");
        Assert.Contains(searchTenant, r => r.Type == "tenant" && r.Title.Contains("عبدالله"));

        // Act & Assert 3: Search document title
        var searchDoc = await _repo.SearchAsync("المكيفات");
        Assert.Contains(searchDoc, r => r.Type == "document" && r.Title.Contains("اتفاقية صيانة المكيفات"));

        // Act & Assert 4: Search document notes
        var searchNotes = await _repo.SearchAsync("الضمان");
        Assert.Contains(searchNotes, r => r.Type == "document" && r.VaultId == ingest.VaultId);
    }

    [Fact]
    public async Task SearchAsync_TenantTimelineColorCoding_AssignsCorrectStatusAndCategory()
    {
        // Arrange
        await _repo.AddAreaAsync("Safra C");
        await _repo.AddHouseAsync("999", "Safra C");

        int currentYear = DateTime.Now.Year;
        // Tenant 1: Active < 5 years (e.g. current year - 2)
        await _repo.AddTenantAsync("999", "طارق القصير", $"{currentYear - 2}-01-01", null);
        // Tenant 2: Active 5-10 years (e.g. current year - 7)
        await _repo.AddTenantAsync("999", "سعيد المتوسط", $"{currentYear - 7}-01-01", "Present");
        // Tenant 3: Active > 10 years (e.g. current year - 14)
        await _repo.AddTenantAsync("999", "ماجد الطويل", $"{currentYear - 14}-01-01", null);
        // Tenant 4: Past tenant (ended)
        await _repo.AddTenantAsync("999", "فهد المغادر", $"{currentYear - 10}-01-01", $"{currentYear - 5}-12-31");

        // Act
        var results = await _repo.SearchAsync("999");
        var tenants = results.Where(r => r.Type == "tenant").ToList();

        // Assert
        var tareq = tenants.FirstOrDefault(t => t.TenantName == "طارق القصير");
        Assert.NotNull(tareq);
        Assert.True(tareq.IsCurrent);
        Assert.Equal("short", tareq.DurationCategory);

        var saeed = tenants.FirstOrDefault(t => t.TenantName == "سعيد المتوسط");
        Assert.NotNull(saeed);
        Assert.True(saeed.IsCurrent);
        Assert.Equal("medium", saeed.DurationCategory);

        var majed = tenants.FirstOrDefault(t => t.TenantName == "ماجد الطويل");
        Assert.NotNull(majed);
        Assert.True(majed.IsCurrent);
        Assert.Equal("long", majed.DurationCategory);

        var fahad = tenants.FirstOrDefault(t => t.TenantName == "فهد المغادر");
        Assert.NotNull(fahad);
        Assert.False(fahad.IsCurrent);
        Assert.Null(fahad.DurationCategory);
    }

    [Fact]
    public async Task AddManualDocumentAsync_VerifiesIsManualAndPageInheritance()
    {
        // Arrange
        await _repo.AddAreaAsync("Safra C");
        await _repo.AddHouseAsync("514", "Safra C");
        var t = await _repo.AddTenantAsync("514", "سلمان ناصر", "2021-01-01", null);

        var request = new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "514",
            TenantId = t.Id,
            Category = "عقود",
            ArabicTitle = "عقد إيجار مجمع",
            PrimaryDate = "2021-03-15",
            Notes = "إدخال يدوي رسمي",
            PageCount = 3
        };

        // Act
        var response = await _repo.AddManualDocumentAsync(request);

        // Assert response
        Assert.Equal("success", response.Status);
        Assert.Equal("manual", response.Mode);
        Assert.NotNull(response.VaultId);
        Assert.Equal(1, response.IsManual);
        Assert.Equal(3, response.PageCount);

        // Assert Document in SQLite
        var doc = await _repo.GetDocumentRawAsync(response.VaultId);
        Assert.NotNull(doc);
        Assert.Equal(1, doc.IsManual);
        Assert.Equal("عقد إيجار مجمع", doc.ArabicTitle);
        Assert.Equal("05 - عقود", doc.Category);
        Assert.Equal(3, doc.PageCount);
        Assert.Equal("إدخال يدوي رسمي", doc.Notes);

        // Assert Pages inheritance in SQLite
        var pages = await _repo.GetPagesByVaultIdAsync(response.VaultId);
        Assert.Equal(3, pages.Count);

        // Page 1: first page, not continuation, has subject
        var p1 = pages[0];
        Assert.Equal(1, p1.PageNumber);
        Assert.False(p1.IsContinuation);
        Assert.Equal("عقد إيجار مجمع", p1.Subject);
        Assert.Equal("Page 1 of عقد إيجار مجمع", p1.ContentExplanation);
        Assert.Equal(t.Id, p1.TenantId);
        Assert.Equal("2021-03-15", p1.ResolvedDate);
        Assert.Equal("05 - عقود", p1.FineCategory);
        Assert.Equal("Manually verified by user", p1.FineCategoryReason);

        // Page 2: continuation page, no subject
        var p2 = pages[1];
        Assert.Equal(2, p2.PageNumber);
        Assert.True(p2.IsContinuation);
        Assert.Null(p2.Subject);
        Assert.Equal("Page 2 of عقد إيجار مجمع", p2.ContentExplanation);
        Assert.Equal(t.Id, p2.TenantId);
        Assert.Equal("05 - عقود", p2.FineCategory);

        // Page 3: continuation page
        var p3 = pages[2];
        Assert.Equal(3, p3.PageNumber);
        Assert.True(p3.IsContinuation);
        Assert.Null(p3.Subject);
    }

    [Fact]
    public async Task UpdateDocumentAsync_UpdatesMetadataAndSyncsPages()
    {
        // Arrange
        await _repo.AddAreaAsync("Safra C");
        await _repo.AddHouseAsync("514", "Safra C");
        var t1 = await _repo.AddTenantAsync("514", "مستأجر 1", "2020-01-01", "2022-01-01");
        var t2 = await _repo.AddTenantAsync("514", "مستأجر 2", "2022-01-02", null);

        var ingest = await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "514",
            TenantId = t1.Id,
            Category = "05 - عقود",
            ArabicTitle = "عنوان أصلي",
            PrimaryDate = "2021-01-01",
            PageCount = 2
        });

        // Act: Update title, category, tenant, primary date, and notes
        var updateResult = await _repo.UpdateDocumentAsync(
            ingest.VaultId!,
            arabicTitle: "عنوان معدل جديد",
            category: "06 - كهرباء وماء",
            tenantId: t2.Id,
            primaryDate: "2023-05-15",
            notes: "تم التعديل بواسطة النظام"
        );

        // Assert
        Assert.NotNull(updateResult);
        Assert.Equal("عنوان معدل جديد", updateResult.ArabicTitle);
        Assert.Equal("06 - كهرباء وماء", updateResult.Category);
        Assert.Equal(t2.Id, updateResult.TenantId);
        Assert.Equal("مستأجر 2", updateResult.TenantName);
        Assert.Equal("2023-05-15", updateResult.PrimaryDate);

        // Assert pages also synced
        var pages = await _repo.GetPagesByVaultIdAsync(ingest.VaultId!);
        Assert.All(pages, p =>
        {
            Assert.Equal(t2.Id, p.TenantId);
            Assert.Equal("06 - كهرباء وماء", p.FineCategory);
            Assert.Equal("2023-05-15", p.ResolvedDate);
        });
    }

    [Fact]
    public async Task CopyDocumentAsync_DuplicatesDocumentWithIsManualOne()
    {
        // Arrange
        await _repo.AddAreaAsync("Safra C");
        await _repo.AddHouseAsync("514", "Safra C");
        var t = await _repo.AddTenantAsync("514", "حسين علي", "2021-01-01", null);

        var ingest = await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "514",
            TenantId = t.Id,
            Category = "05 - عقود",
            ArabicTitle = "عقد أصلي",
            PrimaryDate = "2021-05-01",
            PageCount = 1
        });

        // Act
        var copyResult = await _repo.CopyDocumentAsync(
            ingest.VaultId!,
            targetCategory: "09 - إشعارات",
            targetTitle: "نسخة طبق الأصل للإشعار"
        );

        // Assert
        Assert.NotNull(copyResult);
        Assert.NotEqual(ingest.VaultId, copyResult.VaultId);
        Assert.Equal("09 - إشعارات", copyResult.Category);
        Assert.Equal("نسخة طبق الأصل للإشعار", copyResult.ArabicTitle);
        Assert.Equal(1, copyResult.IsManual);

        var copiedDoc = await _repo.GetDocumentRawAsync(copyResult.VaultId);
        Assert.NotNull(copiedDoc);
        Assert.Equal(1, copiedDoc.IsManual);
        Assert.Equal("09 - إشعارات", copiedDoc.Category);
    }

    [Fact]
    public async Task GetDocumentByVaultIdAsync_ReturnsMetadataAndPages()
    {
        // Arrange
        await _repo.AddAreaAsync("Safra C");
        await _repo.AddHouseAsync("514", "Safra C");
        var t = await _repo.AddTenantAsync("514", "طارق سعيد", "2021-01-01", null);

        var tempAreasRoot = Path.Combine(Path.GetTempPath(), $"areas_{Guid.NewGuid():N}");
        var ingest = await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "514",
            TenantId = t.Id,
            Category = "05 - عقود",
            ArabicTitle = "عقد مفصل",
            PrimaryDate = "2021-04-20",
            PageCount = 2,
            AreasRoot = tempAreasRoot
        });

        // Act
        var docDetails = await _repo.GetDocumentByVaultIdAsync(ingest.VaultId!, tempAreasRoot);

        // Assert
        Assert.NotNull(docDetails);
        Assert.Equal(ingest.VaultId, docDetails.VaultId);
        Assert.Equal("514", docDetails.HouseId);
        Assert.Equal("Safra C", docDetails.AreaId);
        Assert.Equal("طارق سعيد", docDetails.TenantName);
        Assert.Equal("عقد مفصل", docDetails.ArabicTitle);
        Assert.Equal("05 - عقود", docDetails.Category);
        Assert.Equal(2, docDetails.PageCount);
        Assert.Equal(1, docDetails.IsManual);
        Assert.Equal(2, docDetails.Pages.Count);
        Assert.NotNull(docDetails.PhysicalPath);
        Assert.Contains(ingest.VaultId!, docDetails.PhysicalPath);
    }

    [Fact]
    public async Task Concurrency_MultipleReadersAndWriter_ExecuteWithoutLockErrorsInWalMode()
    {
        // Arrange
        await _repo.AddAreaAsync("Safra C");
        await _repo.AddHouseAsync("514", "Safra C");
        var t = await _repo.AddTenantAsync("514", "عمار خالد", "2020-01-01", null);

        // Act: Run concurrent reads and writes simultaneously
        var writeTasks = Enumerable.Range(1, 10).Select(i => _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "514",
            TenantId = t.Id,
            Category = "عقود",
            ArabicTitle = $"عقد متزامن {i}",
            PrimaryDate = $"2020-01-{i:D2}",
            PageCount = 1
        }));

        var readTasks = Enumerable.Range(1, 20).Select(_ => _repo.GetTreeAsync());

        await Task.WhenAll(writeTasks.Concat<Task>(readTasks));

        // Assert
        var tree = await _repo.GetTreeAsync();
        var house = tree.First(a => a.Name == "Safra C").Children!.First(h => h.Id == "514");
        Assert.Equal(10, house.TotalDocuments);
    }

    [Fact]
    public async Task DeleteDocumentAsync_DeletesFileAndDatabaseRecords()
    {
        // Arrange
        await _repo.AddAreaAsync("Safra C");
        await _repo.AddHouseAsync("514", "Safra C");
        var t = await _repo.AddTenantAsync("514", "عمر الفاروق", "2021-01-01", null);

        var tempAreasRoot = Path.Combine(Path.GetTempPath(), $"areas_{Guid.NewGuid():N}");
        var ingest = await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Safra C",
            HouseId = "514",
            TenantId = t.Id,
            Category = "05 - عقود",
            ArabicTitle = "وثيقة للحذف",
            PrimaryDate = "2021-06-15",
            PageCount = 1,
            AreasRoot = tempAreasRoot
        });

        var vaultDir = Path.Combine(tempAreasRoot, "Safra C", "514", "vault");
        Directory.CreateDirectory(vaultDir);
        var expectedFilePath = Path.Combine(vaultDir, $"doc_{ingest.VaultId}.pdf");
        await File.WriteAllBytesAsync(expectedFilePath, new byte[] { 0x25, 0x50, 0x44, 0x46 });

        Assert.True(File.Exists(expectedFilePath));
        var rawDocBefore = await _repo.GetDocumentRawAsync(ingest.VaultId!);
        Assert.NotNull(rawDocBefore);

        // Act
        var deleted = await _repo.DeleteDocumentAsync("Safra C", "514", ingest.VaultId!, tempAreasRoot);

        // Assert
        Assert.True(deleted);
        Assert.False(File.Exists(expectedFilePath));

        var rawDocAfter = await _repo.GetDocumentRawAsync(ingest.VaultId!);
        Assert.Null(rawDocAfter);

        var pagesAfter = await _repo.GetPagesByVaultIdAsync(ingest.VaultId!);
        Assert.Empty(pagesAfter);

        // Deleting already deleted or non-existent document returns false
        var notFound = await _repo.DeleteDocumentAsync("Safra C", "514", ingest.VaultId!, tempAreasRoot);
        Assert.False(notFound);

        try
        {
            if (Directory.Exists(tempAreasRoot))
                Directory.Delete(tempAreasRoot, true);
        }
        catch
        {
            // Ignore cleanup errors
        }
    }

    [Fact]
    public async Task GetHousesAsync_And_GetTreeAsync_VacantHouse_ReturnsGreyAndNoActiveTenant()
    {
        // Arrange: House 538 in Safra C with multiple past tenants:
        // - Tenant 1: 2011 - 2021
        // - Tenant 2: 2013 - 2023
        // - Tenant 3: 2000 - 2024 (earliest start year, but latest vacate year!)
        await _repo.AddAreaAsync("Safra C", "SC");
        await _repo.AddHouseAsync("538", "Safra C");
        await _repo.AddTenantAsync("538", "مطلق إبراهيم", "2011-11-21", "2021-12-05");
        await _repo.AddTenantAsync("538", "حمد إبراهيم", "2013-07-21", "2023-03-12");
        await _repo.AddTenantAsync("538", "يحيى محمد", "2000-09-16", "2024-09-16");

        // Act 1: GetHousesAsync (Area Grid view)
        var houses = await _repo.GetHousesAsync("Safra C");
        var h538 = houses.FirstOrDefault(h => h.Id == "538");
        Assert.NotNull(h538);
        Assert.Null(h538.CurrentTenant);
        Assert.Null(h538.DurationCategory);
        Assert.Equal("grey", h538.TenureColor);
        Assert.Null(h538.TenureDurationYears);
        // The latest tenant who vacated was in 2024 (يحيى: 2000 - 2024)
        Assert.Equal("2000 - 2024", h538.Subtitle);

        // Act 2: GetTreeAsync
        var tree = await _repo.GetTreeAsync();
        var safra = tree.FirstOrDefault(a => a.Name == "Safra C");
        Assert.NotNull(safra);
        Assert.NotNull(safra.Children);
        var treeHouse = safra.Children!.FirstOrDefault(h => h.Id == "538");
        Assert.NotNull(treeHouse);
        Assert.Null(treeHouse.CurrentTenant);
        Assert.Null(treeHouse.DurationCategory);
        Assert.Equal("2000 - 2024", treeHouse.Subtitle);
        Assert.NotNull(treeHouse.Children);
        Assert.Equal(3, treeHouse.Children!.Count);

        // Most recent vacate date (2024) should be first
        Assert.Equal("يحيى محمد", treeHouse.Children[0].Name);
        Assert.Equal("2000 - 2024", treeHouse.Children[0].Subtitle);
        Assert.Null(treeHouse.Children[0].DurationCategory);

        Assert.Equal("حمد إبراهيم", treeHouse.Children[1].Name);
        Assert.Equal("2013 - 2023", treeHouse.Children[1].Subtitle);

        Assert.Equal("مطلق إبراهيم", treeHouse.Children[2].Name);
        Assert.Equal("2011 - 2021", treeHouse.Children[2].Subtitle);

        // Act 3: GetHouseProfileAsync
        var profile = await _repo.GetHouseProfileAsync("Safra C", "538");
        Assert.NotNull(profile);
        Assert.Null(profile.ActiveResident);
        Assert.Equal(3, profile.Tenants.Count);
        Assert.All(profile.Tenants, t => Assert.False(t.IsActive));
        // Profile should also list most recent past tenant first
        Assert.Equal("يحيى محمد", profile.Tenants[0].Name);
    }

    [Fact]
    public async Task AddTenantAsync_Applicant_SetsIsResidentZeroAndStoresNotes()
    {
        // Arrange
        await _repo.AddAreaAsync("AreaApp", "AA");
        await _repo.AddHouseAsync("H-App1", "AreaApp");

        // Act
        var added = await _repo.AddTenantAsync("H-App1", "مقدم طلب تجريبي", "2024-01-01", null, isResident: 0, notes: "Order canceled");

        // Assert
        Assert.Equal(0, added.IsResident);
        Assert.Equal("Order canceled", added.Notes);

        var tenants = await _repo.GetTenantsAsync("H-App1");
        var retrieved = tenants.FirstOrDefault(t => t.Name == "مقدم طلب تجريبي");
        Assert.NotNull(retrieved);
        Assert.Equal(0, retrieved.IsResident);
        Assert.Equal("Order canceled", retrieved.Notes);
    }

    [Fact]
    public async Task GetHouseCardsAsync_WithOnlyNonResidingApplicant_RemainsVacantGrey()
    {
        // Arrange
        await _repo.AddAreaAsync("AreaApp", "AA");
        await _repo.AddHouseAsync("H-App2", "AreaApp");
        await _repo.AddTenantAsync("H-App2", "Non Residing Applicant", "2024-01-01", null, isResident: 0, notes: "Application pending");

        // Act
        var houses = await _repo.GetHousesAsync("AreaApp");
        var card = houses.FirstOrDefault(h => h.Id == "H-App2");

        // Assert
        Assert.NotNull(card);
        Assert.Equal("grey", card.TenureColor);
        Assert.Null(card.CurrentTenant);
        Assert.Null(card.Subtitle);
    }

    [Fact]
    public async Task GetHouseCardsAsync_WithPastResidentAndApplicant_ShowsPastResidentSubtitleAndVacantGrey()
    {
        // Arrange
        await _repo.AddAreaAsync("AreaApp", "AA");
        await _repo.AddHouseAsync("H-App3", "AreaApp");
        await _repo.AddTenantAsync("H-App3", "Past Resident", "2018-01-01", "2022-12-31", isResident: 1);
        await _repo.AddTenantAsync("H-App3", "Applicant 2024", "2024-01-01", null, isResident: 0, notes: "Order canceled");

        // Act
        var houses = await _repo.GetHousesAsync("AreaApp");
        var card = houses.FirstOrDefault(h => h.Id == "H-App3");

        // Assert
        Assert.NotNull(card);
        Assert.Equal("grey", card.TenureColor);
        Assert.Null(card.CurrentTenant);
        Assert.Equal("2018 - 2022", card.Subtitle);
    }

    [Fact]
    public async Task GetHouseProfileAsync_SegregatesActiveResidentFromApplicants()
    {
        // Arrange
        await _repo.AddAreaAsync("AreaApp", "AA");
        await _repo.AddHouseAsync("H-App4", "AreaApp");
        await _repo.AddTenantAsync("H-App4", "Resident Name", "2020-01-01", null, isResident: 1);
        await _repo.AddTenantAsync("H-App4", "Applicant Person", "2024-01-01", null, isResident: 0, notes: "Order canceled");

        // Act
        var profile = await _repo.GetHouseProfileAsync("AreaApp", "H-App4");

        // Assert
        Assert.NotNull(profile);
        Assert.Equal("Resident Name", profile.ActiveResident);

        var applicant = profile.Tenants.FirstOrDefault(t => t.Name == "Applicant Person");
        Assert.NotNull(applicant);
        Assert.Equal(0, applicant.IsResident);
        Assert.False(applicant.IsActive);
        Assert.Equal("Order canceled", applicant.Notes);

        var resident = profile.Tenants.FirstOrDefault(t => t.Name == "Resident Name");
        Assert.NotNull(resident);
        Assert.Equal(1, resident.IsResident);
        Assert.True(resident.IsActive);
    }

    [Fact]
    public async Task BulkUpdateTenantsAsync_Reallocation_NeverAssignsDocsToNonResidingApplicant()
    {
        // Arrange
        await _repo.AddAreaAsync("AreaApp", "AA");
        await _repo.AddHouseAsync("H-App5", "AreaApp");
        var pastResident = await _repo.AddTenantAsync("H-App5", "Past Resident 2018", "2018-01-01", "2022-12-31", isResident: 1);
        var applicant = await _repo.AddTenantAsync("H-App5", "Applicant 2024", "2024-01-01", null, isResident: 0, notes: "Pending order");

        // Ingest a document and mark it as is_manual = 0 to allow reallocation
        var ingest = new IngestRequestDto
        {
            AreaId = "AreaApp",
            HouseId = "H-App5",
            TenantId = pastResident.Id,
            Category = "عقود",
            ArabicTitle = "عقد إيجار قديم",
            PrimaryDate = "2024-06-01"
        };
        var resp = await _repo.AddManualDocumentAsync(ingest);
        var vaultId = resp.VaultId;

        await using (var conn = await _factory.CreateConnectionAsync())
        {
            await conn.ExecuteAsync("UPDATE documents SET is_manual = 0 WHERE vault_id = @VaultId;",
                new { VaultId = vaultId });
        }

        // Act: Bulk update with reallocate = true
        var updatedList = new List<TenantDto>
        {
            new TenantDto { Id = pastResident.Id, Name = pastResident.Name, StartDate = pastResident.StartDate, EndDate = pastResident.EndDate, HouseId = "H-App5", IsResident = 1 },
            new TenantDto { Id = applicant.Id, Name = applicant.Name, StartDate = applicant.StartDate, EndDate = applicant.EndDate, HouseId = "H-App5", IsResident = 0, Notes = "Pending order" }
        };

        var reallocResult = await _repo.BulkUpdateTenantsAsync("H-App5", updatedList, reallocate: true);

        // Assert: Reallocation assigns to past resident, NEVER to applicant
        Assert.NotNull(vaultId);
        var doc = await _repo.GetDocumentRawAsync(vaultId);
        Assert.NotNull(doc);
        Assert.Equal(pastResident.Id, doc.TenantId);
        Assert.NotEqual(applicant.Id, doc.TenantId);
    }

    [Fact]
    public async Task BulkUpdateTenantsAsync_NeverReallocatesOrTouches_ApplicantDocuments()
    {
        // Arrange
        await _repo.AddAreaAsync("AreaAppProt", "AAP");
        await _repo.AddHouseAsync("H-AppProt1", "AreaAppProt");
        var resident = await _repo.AddTenantAsync("H-AppProt1", "Resident Main", "2020-01-01", null, isResident: 1);
        var applicant = await _repo.AddTenantAsync("H-AppProt1", "Applicant Person", "2023-01-01", null, isResident: 0);

        // Adds a document belonging to the Applicant with primary date 2021-05-15 (which falls squarely in the Resident's tenure)
        var ingest = new IngestRequestDto
        {
            AreaId = "AreaAppProt",
            HouseId = "H-AppProt1",
            TenantId = applicant.Id,
            Category = "عقود",
            ArabicTitle = "وثيقة مقدم طلب",
            PrimaryDate = "2021-05-15"
        };
        var resp = await _repo.AddManualDocumentAsync(ingest);
        var vaultId = resp.VaultId;

        // Mark as is_manual = 0 so that it would normally be subject to reallocation
        await using (var conn = await _factory.CreateConnectionAsync())
        {
            await conn.ExecuteAsync("UPDATE documents SET is_manual = 0 WHERE vault_id = @VaultId;",
                new { VaultId = vaultId });
        }

        // Act: Bulk update with reallocate = true
        var updatedList = new List<TenantDto>
        {
            new TenantDto { Id = resident.Id, Name = resident.Name, StartDate = resident.StartDate, EndDate = resident.EndDate, HouseId = "H-AppProt1", IsResident = 1 },
            new TenantDto { Id = applicant.Id, Name = applicant.Name, StartDate = applicant.StartDate, EndDate = applicant.EndDate, HouseId = "H-AppProt1", IsResident = 0 }
        };

        await _repo.BulkUpdateTenantsAsync("H-AppProt1", updatedList, reallocate: true);

        // Assert: Document's TenantId remains the Applicant's ID, and was NOT moved to the Resident
        Assert.NotNull(vaultId);
        var doc = await _repo.GetDocumentRawAsync(vaultId);
        Assert.NotNull(doc);
        Assert.Equal(applicant.Id, doc.TenantId);
        Assert.NotEqual(resident.Id, doc.TenantId);
    }

    [Fact]
    public async Task BulkUpdateTenantsAsync_WithOnlyApplicants_DoesNotReallocate()
    {
        // Arrange
        await _repo.AddAreaAsync("AreaOnlyApp", "AOA");
        await _repo.AddHouseAsync("H-OnlyApp1", "AreaOnlyApp");
        var applicant = await _repo.AddTenantAsync("H-OnlyApp1", "Sole Applicant", "2023-01-01", null, isResident: 0);

        var ingest = new IngestRequestDto
        {
            AreaId = "AreaOnlyApp",
            HouseId = "H-OnlyApp1",
            TenantId = applicant.Id,
            Category = "عقود",
            ArabicTitle = "وثيقة",
            PrimaryDate = "2023-05-15"
        };
        var resp = await _repo.AddManualDocumentAsync(ingest);
        var vaultId = resp.VaultId;

        await using (var conn = await _factory.CreateConnectionAsync())
        {
            await conn.ExecuteAsync("UPDATE documents SET is_manual = 0 WHERE vault_id = @VaultId;",
                new { VaultId = vaultId });
        }

        var updatedList = new List<TenantDto>
        {
            new TenantDto { Id = applicant.Id, Name = applicant.Name, StartDate = applicant.StartDate, EndDate = applicant.EndDate, HouseId = "H-OnlyApp1", IsResident = 0 }
        };

        var result = await _repo.BulkUpdateTenantsAsync("H-OnlyApp1", updatedList, reallocate: true);

        Assert.Equal(0, result.ReallocatedCount);
        Assert.NotNull(vaultId);
        var doc = await _repo.GetDocumentRawAsync(vaultId);
        Assert.NotNull(doc);
        Assert.Equal(applicant.Id, doc.TenantId);
    }

    [Fact]
    public async Task BulkUpdateTenantsAsync_PreservesApplicantStatusAndNotes()
    {
        // Arrange
        await _repo.AddAreaAsync("AreaApp", "AA");
        await _repo.AddHouseAsync("H-App6", "AreaApp");
        var resident = await _repo.AddTenantAsync("H-App6", "Resident Main", "2020-01-01", null, isResident: 1);
        var applicant = await _repo.AddTenantAsync("H-App6", "Applicant Initial", "2023-01-01", null, isResident: 0, notes: "Original note");

        // Act: Bulk update modifying applicant and adding new applicant
        var updatedList = new List<TenantDto>
        {
            new TenantDto { Id = resident.Id, Name = resident.Name, StartDate = resident.StartDate, EndDate = resident.EndDate, HouseId = "H-App6", IsResident = 1 },
            new TenantDto { Id = applicant.Id, Name = "Applicant Modified", StartDate = applicant.StartDate, EndDate = applicant.EndDate, HouseId = "H-App6", IsResident = 0, Notes = "Updated custom note" },
            new TenantDto { Name = "New Applicant Added", StartDate = "2024-02-01", HouseId = "H-App6", IsResident = 0, Notes = "New application note" }
        };

        await _repo.BulkUpdateTenantsAsync("H-App6", updatedList, reallocate: false);

        // Assert
        var tenants = await _repo.GetTenantsAsync("H-App6");
        Assert.Equal(3, tenants.Count);

        var residentDto = tenants.FirstOrDefault(t => t.Id == resident.Id);
        Assert.NotNull(residentDto);
        Assert.Equal(1, residentDto.IsResident);

        var modApplicantDto = tenants.FirstOrDefault(t => t.Id == applicant.Id);
        Assert.NotNull(modApplicantDto);
        Assert.Equal("Applicant Modified", modApplicantDto.Name);
        Assert.Equal(0, modApplicantDto.IsResident);
        Assert.Equal("Updated custom note", modApplicantDto.Notes);

        var newApplicantDto = tenants.FirstOrDefault(t => t.Name == "New Applicant Added");
        Assert.NotNull(newApplicantDto);
        Assert.Equal(0, newApplicantDto.IsResident);
        Assert.Equal("New application note", newApplicantDto.Notes);
    }

    [Fact]
    public async Task BulkUpdateTenantsAsync_WhenRemovingTenantWithDocuments_ReassignsDocumentsAndDeletesTenant()
    {
        // Arrange
        await _repo.AddAreaAsync("AreaDel", "AD");
        await _repo.AddHouseAsync("H-Del1", "AreaDel");
        var t1 = await _repo.AddTenantAsync("H-Del1", "Tenant Surviving", "2020-01-01", null, isResident: 1);
        var t2 = await _repo.AddTenantAsync("H-Del1", "Tenant To Remove", "2022-01-01", "2023-01-01", isResident: 1);

        var ingest = new IngestRequestDto
        {
            AreaId = "AreaDel",
            HouseId = "H-Del1",
            TenantId = t2.Id,
            Category = "عقود",
            ArabicTitle = "عقد مستأجر محذوف",
            PrimaryDate = "2022-05-01"
        };
        var resp = await _repo.AddManualDocumentAsync(ingest);
        var vaultId = resp.VaultId;

        // Act: remove t2 from the payload
        var updatedList = new List<TenantDto>
        {
            new TenantDto { Id = t1.Id, Name = t1.Name, StartDate = t1.StartDate, EndDate = t1.EndDate, HouseId = "H-Del1", IsResident = 1 }
        };

        var result = await _repo.BulkUpdateTenantsAsync("H-Del1", updatedList, reallocate: true);

        // Assert: t2 was deleted, doc was reallocated to t1 without FK violation!
        var tenants = await _repo.GetTenantsAsync("H-Del1");
        Assert.Single(tenants);
        Assert.Equal(t1.Id, tenants[0].Id);

        var doc = await _repo.GetDocumentRawAsync(vaultId);
        Assert.NotNull(doc);
        Assert.Equal(t1.Id, doc.TenantId);
    }

    [Fact]
    public async Task BulkUpdateTenantsAsync_WhenRemovingTenantWithDocuments_WithoutReallocate_StillReassignsDocumentsAndDeletesTenant()
    {
        // Arrange
        await _repo.AddAreaAsync("AreaDel2", "AD2");
        await _repo.AddHouseAsync("H-Del2", "AreaDel2");
        var t1 = await _repo.AddTenantAsync("H-Del2", "Tenant Surviving", "2020-01-01", null, isResident: 1);
        var t2 = await _repo.AddTenantAsync("H-Del2", "Tenant To Remove", "2022-01-01", "2023-01-01", isResident: 1);

        var ingest = new IngestRequestDto
        {
            AreaId = "AreaDel2",
            HouseId = "H-Del2",
            TenantId = t2.Id,
            Category = "عقود",
            ArabicTitle = "عقد مستأجر محذوف",
            PrimaryDate = "2022-05-01"
        };
        var resp = await _repo.AddManualDocumentAsync(ingest);
        var vaultId = resp.VaultId;

        // Act: remove t2 without reallocation
        var updatedList = new List<TenantDto>
        {
            new TenantDto { Id = t1.Id, Name = t1.Name, StartDate = t1.StartDate, EndDate = t1.EndDate, HouseId = "H-Del2", IsResident = 1 }
        };

        var result = await _repo.BulkUpdateTenantsAsync("H-Del2", updatedList, reallocate: false);

        // Assert: t2 was deleted, doc was moved to t1 fallback without FK violation!
        var tenants = await _repo.GetTenantsAsync("H-Del2");
        Assert.Single(tenants);
        Assert.Equal(t1.Id, tenants[0].Id);

        var doc = await _repo.GetDocumentRawAsync(vaultId!);
        Assert.NotNull(doc);
        Assert.Equal(t1.Id, doc.TenantId);
    }

    [Fact]
    public async Task BulkUpdateTenantsAsync_WhenAddingApplicantWithNullStartDate_SucceedsWithoutConstraintError()
    {
        // Arrange
        await _repo.AddAreaAsync("AreaNullStart", "ANS");
        await _repo.AddHouseAsync("H-614Test", "AreaNullStart");
        var resident = await _repo.AddTenantAsync("H-614Test", "Existing Resident", "2002-03-11", null, isResident: 1);

        // Act: Add a new applicant with StartDate = null
        var updatedList = new List<TenantDto>
        {
            new TenantDto { Id = resident.Id, Name = resident.Name, StartDate = resident.StartDate, EndDate = resident.EndDate, HouseId = "H-614Test", IsResident = 1 },
            new TenantDto { Name = "New Applicant No Date", StartDate = null, EndDate = null, HouseId = "H-614Test", IsResident = 0 }
        };

        var result = await _repo.BulkUpdateTenantsAsync("H-614Test", updatedList, reallocate: false);

        // Assert: Both resident and applicant are saved
        var tenants = await _repo.GetTenantsAsync("H-614Test");
        Assert.Equal(2, tenants.Count);
        var applicant = tenants.FirstOrDefault(t => t.Name == "New Applicant No Date");
        Assert.NotNull(applicant);
        Assert.Equal(0, applicant.IsResident);
        Assert.Null(applicant.StartDate);
    }

    [Fact]
    public async Task GetTenantsAsync_AnchorsStartDate_ToEarliestDocumentDate()
    {
        // Arrange: Tenant created with initial date 2022-01-01
        await _repo.AddAreaAsync("AreaAnchor", "ANC");
        await _repo.AddHouseAsync("H-Anchor1", "AreaAnchor");
        var tenant = await _repo.AddTenantAsync("H-Anchor1", "Tenant Anchored", "2022-01-01", null, isResident: 1);

        // Add document with earlier date 2019-06-15
        await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "AreaAnchor",
            HouseId = "H-Anchor1",
            TenantId = tenant.Id,
            Category = "05 - عقود",
            ArabicTitle = "عقد قديم",
            PrimaryDate = "2019-06-15",
            VaultId = Guid.NewGuid().ToString("N"),
            PageCount = 1
        });

        // Act
        var tenants = await _repo.GetTenantsAsync("H-Anchor1");
        var profile = await _repo.GetHouseProfileAsync("AreaAnchor", "H-Anchor1");

        // Assert: StartDate is anchored to the earliest document date 2019-06-15
        var tDto = tenants.FirstOrDefault(t => t.Id == tenant.Id);
        Assert.NotNull(tDto);
        Assert.Equal("2019-06-15", tDto.StartDate);

        Assert.NotNull(profile);
        var pDto = profile.Tenants.FirstOrDefault(t => t.Name == "Tenant Anchored");
        Assert.NotNull(pDto);
        Assert.Equal("2019-06-15", pDto.StartDate);
    }

    [Fact]
    public async Task AddTenantAsync_BrandNewTenantWithZeroDocuments_AllowsNullStartDate_AndSnapsOnFirstUpload()
    {
        // Arrange: Brand new tenant with zero documents created with null startDate
        await _repo.AddAreaAsync("AreaZeroDoc", "AZD");
        await _repo.AddHouseAsync("H-Zero1", "AreaZeroDoc");
        var newTenant = await _repo.AddTenantAsync("H-Zero1", "New Tenant Zero", startDate: null, isResident: 1);

        // Act 1: Fetch before any documents uploaded
        var tenantsBefore = await _repo.GetTenantsAsync("H-Zero1");
        var tBefore = tenantsBefore.FirstOrDefault(t => t.Id == newTenant.Id);
        Assert.NotNull(tBefore);
        Assert.Null(tBefore.StartDate);

        // Act 2: Upload first document with date 2024-05-10
        await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "AreaZeroDoc",
            HouseId = "H-Zero1",
            TenantId = newTenant.Id,
            Category = "01 - كتب رسمية",
            ArabicTitle = "أول كتاب",
            PrimaryDate = "2024-05-10",
            VaultId = Guid.NewGuid().ToString("N"),
            PageCount = 1
        });

        // Act 3: Fetch after first upload
        var tenantsAfter = await _repo.GetTenantsAsync("H-Zero1");
        var profileAfter = await _repo.GetHouseProfileAsync("AreaZeroDoc", "H-Zero1");

        // Assert: StartDate automatically snaps to the first document date 2024-05-10
        var tAfter = tenantsAfter.FirstOrDefault(t => t.Id == newTenant.Id);
        Assert.NotNull(tAfter);
        Assert.Equal("2024-05-10", tAfter.StartDate);

        Assert.NotNull(profileAfter);
        var pAfter = profileAfter.Tenants.FirstOrDefault(t => t.Name == "New Tenant Zero");
        Assert.NotNull(pAfter);
        Assert.Equal("2024-05-10", pAfter.StartDate);
    }

    [Fact]
    public async Task GetTenantsAsync_AnchorsStartDate_ToEarliestDocumentDate_EvenWhenManualDateIsOlder()
    {
        // Arrange: Existing tenant has an older manual start date 2015-01-01
        await _repo.AddAreaAsync("AreaOlderManual", "AOM");
        await _repo.AddHouseAsync("H-Older1", "AreaOlderManual");
        var tenant = await _repo.AddTenantAsync("H-Older1", "Older Tenant", "2015-01-01", null, isResident: 1);

        // Add document with later date 2018-05-20 (earliest document for this tenant)
        await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "AreaOlderManual",
            HouseId = "H-Older1",
            TenantId = tenant.Id,
            Category = "05 - عقود",
            ArabicTitle = "عقد إيجار 2018",
            PrimaryDate = "2018-05-20",
            VaultId = Guid.NewGuid().ToString("N"),
            PageCount = 1
        });

        // Act
        var tenants = await _repo.GetTenantsAsync("H-Older1");
        var profile = await _repo.GetHouseProfileAsync("AreaOlderManual", "H-Older1");

        // Assert: Both GetTenantsAsync and GetHouseProfileAsync return 2018-05-20, unconditionally anchoring to earliest document
        var tDto = tenants.FirstOrDefault(t => t.Id == tenant.Id);
        Assert.NotNull(tDto);
        Assert.Equal("2018-05-20", tDto.StartDate);

        Assert.NotNull(profile);
        var pDto = profile.Tenants.FirstOrDefault(t => t.Name == "Older Tenant");
        Assert.NotNull(pDto);
        Assert.Equal("2018-05-20", pDto.StartDate);
    }

    [Fact]
    public async Task GetTreeAsync_And_GetHousesAsync_AccuratelyReflectDocumentAnchoredStartDate_WhenDocumentDateIsUpdated()
    {
        // Arrange
        await _repo.AddAreaAsync("Area616", "A616");
        await _repo.AddHouseAsync("616", "Area616");
        var tenant = await _repo.AddTenantAsync("616", "House 616 Tenant", "1990-01-01", null, isResident: 1);

        var docReq = new IngestRequestDto
        {
            AreaId = "Area616",
            HouseId = "616",
            TenantId = tenant.Id,
            Category = "05 - عقود",
            ArabicTitle = "عقد إيجار قديم 1990",
            PrimaryDate = "1990-01-01",
            VaultId = Guid.NewGuid().ToString("N"),
            PageCount = 1
        };
        var addedDoc = await _repo.AddManualDocumentAsync(docReq);

        // Before update: tree and houses reflect 1990
        var treeBefore = await _repo.GetTreeAsync();
        var houseBefore = treeBefore.FirstOrDefault(a => a.Name == "Area616")?.Children?.FirstOrDefault(h => h.Id == "616");
        Assert.NotNull(houseBefore);
        Assert.Equal("long", houseBefore.DurationCategory);
        Assert.Contains("Since 1990", houseBefore.Subtitle);
        var tenantBefore = houseBefore.Children?.FirstOrDefault(t => t.Name == "House 616 Tenant");
        Assert.NotNull(tenantBefore);
        Assert.Equal("1990 - Present", tenantBefore.Subtitle);
        Assert.Equal("long", tenantBefore.DurationCategory);

        // Act: Update document date to 2 years ago (short tenure < 5y)
        var currentYear = DateTime.Now.Year;
        var newStartYear = currentYear - 2;
        var newDateStr = $"{newStartYear}-06-15";

        await _repo.UpdateDocumentAsync(addedDoc.VaultId, primaryDate: newDateStr);

        // Assert: GetTreeAsync, GetHousesAsync, GetHouseProfileAsync, and GetTenantsAsync ALL reflect newDateStr
        var treeAfter = await _repo.GetTreeAsync();
        var houseAfter = treeAfter.FirstOrDefault(a => a.Name == "Area616")?.Children?.FirstOrDefault(h => h.Id == "616");
        Assert.NotNull(houseAfter);
        Assert.Equal("short", houseAfter.DurationCategory);
        Assert.Equal($"Since {newStartYear} (2y)", houseAfter.Subtitle);
        var tenantAfter = houseAfter.Children?.FirstOrDefault(t => t.Name == "House 616 Tenant");
        Assert.NotNull(tenantAfter);
        Assert.Equal($"{newStartYear} - Present", tenantAfter.Subtitle);
        Assert.Equal("short", tenantAfter.DurationCategory);
        Assert.Equal(newDateStr, tenantAfter.StartDate);

        // GetHousesAsync check
        var houses = await _repo.GetHousesAsync("Area616");
        var houseCard = houses.FirstOrDefault(h => h.Id == "616");
        Assert.NotNull(houseCard);
        Assert.Equal("short", houseCard.DurationCategory);
        Assert.Equal(2, houseCard.TenureDurationYears);
        Assert.Equal($"Since {newStartYear} (2y)", houseCard.Subtitle);

        // GetHouseProfileAsync check (tenant selection UI)
        var profile = await _repo.GetHouseProfileAsync("Area616", "616");
        Assert.NotNull(profile);
        var profileTenant = profile.Tenants.FirstOrDefault(t => t.Name == "House 616 Tenant");
        Assert.NotNull(profileTenant);
        Assert.Equal(newDateStr, profileTenant.StartDate);
        Assert.Equal("short", profileTenant.DurationCategory);

        // GetTenantsAsync check
        var tenantsList = await _repo.GetTenantsAsync("616");
        var tDto = tenantsList.FirstOrDefault(t => t.Name == "House 616 Tenant");
        Assert.NotNull(tDto);
        Assert.Equal(newDateStr, tDto.StartDate);
    }

    [Fact]
    public async Task DeleteDocumentAsync_UpdatesTreeAndHouseCardDocumentAnchoredStartDate()
    {
        // Arrange: House 617 with two documents: 2010 and 2022
        await _repo.AddAreaAsync("Area617", "A617");
        await _repo.AddHouseAsync("617", "Area617");
        var tenant = await _repo.AddTenantAsync("617", "Multi Doc Tenant", "1995-01-01", null, isResident: 1);

        var doc1 = await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Area617",
            HouseId = "617",
            TenantId = tenant.Id,
            Category = "05 - عقود",
            ArabicTitle = "عقد قديم 2010",
            PrimaryDate = "2010-01-01",
            VaultId = Guid.NewGuid().ToString("N"),
            PageCount = 1
        });

        var currentYear = DateTime.Now.Year;
        var recentYear = currentYear - 1;
        var doc2 = await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Area617",
            HouseId = "617",
            TenantId = tenant.Id,
            Category = "01 - بيانات أساسية",
            ArabicTitle = "وثيقة حديثة",
            PrimaryDate = $"{recentYear}-08-01",
            VaultId = Guid.NewGuid().ToString("N"),
            PageCount = 1
        });

        // Initially anchors to 2010
        var tree1 = await _repo.GetTreeAsync();
        var h1 = tree1.FirstOrDefault(a => a.Name == "Area617")?.Children?.FirstOrDefault(h => h.Id == "617");
        Assert.NotNull(h1);
        Assert.Contains("Since 2010", h1.Subtitle);

        // Act: Delete 2010 document
        var delOk = await _repo.DeleteDocumentAsync("Area617", "617", doc1.VaultId);
        Assert.True(delOk);

        // Assert: Next earliest document (recentYear) now anchors the house card and tree
        var tree2 = await _repo.GetTreeAsync();
        var h2 = tree2.FirstOrDefault(a => a.Name == "Area617")?.Children?.FirstOrDefault(h => h.Id == "617");
        Assert.NotNull(h2);
        Assert.Equal("short", h2.DurationCategory);
        Assert.Contains($"Since {recentYear}", h2.Subtitle);

        var tenantNode = h2.Children?.FirstOrDefault(t => t.Name == "Multi Doc Tenant");
        Assert.NotNull(tenantNode);
        Assert.Equal($"{recentYear} - Present", tenantNode.Subtitle);
        Assert.Equal($"{recentYear}-08-01", tenantNode.StartDate);
    }

    [Fact]
    public async Task Applicants_NeverAppearBeforeResidentTenants_InTree_And_HouseProfile()
    {
        // Arrange: House 618 in Area618 with an applicant who applied recently (2025-01-01, end_date null),
        // a past resident (2015-01-01 to 2020-01-01), and a current resident (2020-01-01 to null).
        await _repo.AddAreaAsync("Area618", "A618");
        await _repo.AddHouseAsync("618", "Area618");

        // Insert applicant FIRST into database
        var applicant = await _repo.AddTenantAsync("618", "Applicant Person", "2025-01-01", null, isResident: 0);
        // Insert past resident
        var pastTenant = await _repo.AddTenantAsync("618", "Past Resident", "2015-01-01", "2020-01-01", isResident: 1);
        // Insert current resident
        var currentTenant = await _repo.AddTenantAsync("618", "Current Resident", "2020-01-01", null, isResident: 1);

        // Act 1: GetTreeAsync
        var tree = await _repo.GetTreeAsync();
        var houseNode = tree.FirstOrDefault(a => a.Name == "Area618")?.Children?.FirstOrDefault(h => h.Id == "618");
        Assert.NotNull(houseNode);
        Assert.NotNull(houseNode.Children);
        var treeTenants = houseNode.Children.Where(c => c.Type == "tenant").ToList();
        Assert.Equal(3, treeTenants.Count);
        Assert.Equal("Current Resident", treeTenants[0].Name);
        Assert.Equal(1, treeTenants[0].IsResident);
        Assert.Equal("Past Resident", treeTenants[1].Name);
        Assert.Equal(1, treeTenants[1].IsResident);
        Assert.Equal("Applicant Person", treeTenants[2].Name);
        Assert.Equal(0, treeTenants[2].IsResident);

        // Act 2: GetHousesAsync
        var houses = await _repo.GetHousesAsync("Area618");
        var houseCard = houses.FirstOrDefault(h => h.Id == "618");
        Assert.NotNull(houseCard);
        Assert.Equal("Current Resident", houseCard.CurrentTenant);

        // Act 3: GetHouseProfileAsync
        var profile = await _repo.GetHouseProfileAsync("Area618", "618");
        Assert.NotNull(profile);
        Assert.Equal(3, profile.Tenants.Count);
        Assert.Equal("Current Resident", profile.Tenants[0].Name);
        Assert.Equal(1, profile.Tenants[0].IsResident);
        Assert.Equal("Past Resident", profile.Tenants[1].Name);
        Assert.Equal(1, profile.Tenants[1].IsResident);
        Assert.Equal("Applicant Person", profile.Tenants[2].Name);
        Assert.Equal(0, profile.Tenants[2].IsResident);

        // Act 4: GetTenantsAsync
        var tenantsList = await _repo.GetTenantsAsync("618");
        Assert.Equal(3, tenantsList.Count);
        Assert.Equal("Current Resident", tenantsList[0].Name);
        Assert.Equal(1, tenantsList[0].IsResident);
        Assert.Equal("Past Resident", tenantsList[1].Name);
        Assert.Equal(1, tenantsList[1].IsResident);
        Assert.Equal("Applicant Person", tenantsList[2].Name);
        Assert.Equal(0, tenantsList[2].IsResident);
    }

    [Fact]
    public async Task GetHouseProfileAsync_PopulatesTenantLevelCategoryCounts_IsolatedPerTenant()
    {
        // Arrange
        await _repo.AddAreaAsync("Area500", "A500");
        await _repo.AddHouseAsync("500", "Area500");

        var tActive = await _repo.AddTenantAsync("500", "Active Tenant Fawaz", "2022-01-01", null, 1);
        var tPast = await _repo.AddTenantAsync("500", "Past Tenant Abdullah", "2018-01-01", "2021-12-31", 1);

        // Active tenant has 1 contract doc
        await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Area500",
            HouseId = "500",
            TenantId = tActive.Id,
            Category = "05 - عقود",
            ArabicTitle = "عقد إيجار جديد",
            PrimaryDate = "2022-01-01",
            PageCount = 2
        });

        // Past tenant has 2 contract docs
        await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Area500",
            HouseId = "500",
            TenantId = tPast.Id,
            Category = "05 - عقود",
            ArabicTitle = "عقد إيجار قديم 1",
            PrimaryDate = "2018-01-01",
            PageCount = 1
        });
        await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "Area500",
            HouseId = "500",
            TenantId = tPast.Id,
            Category = "05 - عقود",
            ArabicTitle = "عقد إيجار قديم 2",
            PrimaryDate = "2019-01-01",
            PageCount = 1
        });

        // Act
        var profile = await _repo.GetHouseProfileAsync("Area500", "500");
        var houses = await _repo.GetHousesAsync("Area500");
        var houseCard = houses.FirstOrDefault(h => h.Id == "500");

        // Assert
        Assert.NotNull(profile);
        Assert.Equal(2, profile.Tenants.Count);

        var activeProfile = profile.Tenants.First(t => t.Id == tActive.Id);
        Assert.Equal(1, activeProfile.CategoryCounts["عقود"]); // Strictly 1, NOT 3!

        var pastProfile = profile.Tenants.First(t => t.Id == tPast.Id);
        Assert.Equal(2, pastProfile.CategoryCounts["عقود"]); // Strictly 2

        // Archive aggregates all docs
        Assert.Equal(3, profile.Archive.TotalDocuments);

        // HouseCard has ActiveTenantCategoryCounts isolated to active tenant
        Assert.NotNull(houseCard);
        Assert.NotNull(houseCard.ActiveTenantCategoryCounts);
        Assert.Equal(1, houseCard.ActiveTenantCategoryCounts["عقود"]); // 1 contract for active tenant
    }

    [Fact]
    public async Task BatchMoveDocumentsAsync_MovingDocumentToActiveTenant_UpdatesActiveTenantCategoryCountsInTreeAndHouses()
    {
        // Arrange: House with active tenant (no category 07) and past tenant (has category 07)
        await _repo.AddAreaAsync("AreaMove504", "M504");
        await _repo.AddHouseAsync("504", "AreaMove504");
        var tActive = await _repo.AddTenantAsync("504", "أحمد يوسف المريسل", "2021-01-20", isResident: 1);
        var tPast = await _repo.AddTenantAsync("504", "عبدالله بدر بودواس", "2010-10-31", endDate: "2021-01-19", isResident: 1);

        // Document #7 originally under past tenant
        var doc7 = await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "AreaMove504",
            HouseId = "504",
            TenantId = tPast.Id,
            Category = "07 - استقطاع إيجار",
            ArabicTitle = "كتاب استقطاع مالي",
            PrimaryDate = "2021-05-24",
            PageCount = 1
        });

        // Verify pre-move state: active tenant has 0 category 07
        var preHouses = await _repo.GetHousesAsync("AreaMove504");
        var preCard = preHouses.First(h => h.Id == "504");
        Assert.False(preCard.ActiveTenantCategoryCounts?.ContainsKey("استقطاع إيجار") == true && preCard.ActiveTenantCategoryCounts["استقطاع إيجار"] > 0);

        // Act: Move document #7 to active tenant
        var moveResult = await _repo.BatchMoveDocumentsAsync(
            "AreaMove504",
            "504",
            new[] { doc7.VaultId! },
            "07 - استقطاع إيجار",
            targetTenantId: tActive.Id
        );
        Assert.Equal(1, moveResult.MovedCount);

        // Assert: GetHouseProfileAsync shows active tenant has category 07
        var profile = await _repo.GetHouseProfileAsync("AreaMove504", "504");
        Assert.NotNull(profile);
        var activeProf = profile.Tenants.First(t => t.Id == tActive.Id);
        Assert.True(activeProf.CategoryCounts.ContainsKey("استقطاع إيجار"));
        Assert.Equal(1, activeProf.CategoryCounts["استقطاع إيجار"]);

        // Assert: GetHousesAsync (HouseCard) has ActiveTenantCategoryCounts with category 07
        var postHouses = await _repo.GetHousesAsync("AreaMove504");
        var postCard = postHouses.First(h => h.Id == "504");
        Assert.NotNull(postCard.ActiveTenantCategoryCounts);
        Assert.True(postCard.ActiveTenantCategoryCounts.ContainsKey("استقطاع إيجار"));
        Assert.Equal(1, postCard.ActiveTenantCategoryCounts["استقطاع إيجار"]);

        // Assert: GetTreeAsync has ActiveTenantCategoryCounts with category 07
        var tree = await _repo.GetTreeAsync();
        var treeArea = tree.First(a => a.Name == "AreaMove504");
        var treeHouse = treeArea.Children!.First(h => h.Id == "504");
        Assert.NotNull(treeHouse.ActiveTenantCategoryCounts);
        Assert.True(treeHouse.ActiveTenantCategoryCounts.ContainsKey("استقطاع إيجار"));
        Assert.Equal(1, treeHouse.ActiveTenantCategoryCounts["استقطاع إيجار"]);
    }

    [Fact]
    public async Task ExtractPagesAsync_SeparatesPagesIntoNewDocument_UpdatesRemainingPages_AndPreservesBatchLineage()
    {
        // Arrange
        await _repo.AddAreaAsync("AreaExtract", "EXT");
        await _repo.AddHouseAsync("H-EXT", "AreaExtract");
        var tenant = await _repo.AddTenantAsync("H-EXT", "Extract Tenant", "2024-01-01");

        var sourceVaultId = Guid.NewGuid().ToString("N");
        var doc = await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "AreaExtract",
            HouseId = "H-EXT",
            TenantId = tenant.Id,
            Category = "10 - صيانة",
            ArabicTitle = "خطاب صيانة مجمع",
            PrimaryDate = "2024-05-15",
            VaultId = sourceVaultId,
            PageCount = 4
        });

        // Act: Extract page 4 to "04 - محضر تسليم مفتاح"
        var extractReq = new ExtractPagesRequestDto
        {
            PageNumbers = new List<int> { 4 },
            TargetCategory = "04 - محضر تسليم مفتاح",
            TargetTenantId = tenant.Id,
            TargetTitle = "محضر تسليم مفتاح منفصل",
            TargetDate = "2024-05-15",
            DeleteFromSource = true
        };

        var res = await _repo.ExtractPagesAsync("AreaExtract", "H-EXT", sourceVaultId, extractReq);

        // Assert
        Assert.Equal("success", res.Status);
        Assert.Equal(sourceVaultId, res.SourceVaultId);
        Assert.Equal(3, res.SourceRemainingPages);
        Assert.False(res.SourceDeleted);
        Assert.Equal(1, res.NewPageCount);
        Assert.Equal("04 - محضر تسليم مفتاح", res.NewCategory);
        Assert.Equal("محضر تسليم مفتاح منفصل", res.NewTitle);

        // Verify source document in DB
        var sourceDoc = await _repo.GetDocumentRawAsync(sourceVaultId);
        Assert.NotNull(sourceDoc);
        Assert.Equal(3, sourceDoc.PageCount);
        Assert.Equal("10 - صيانة", sourceDoc.Category);

        // Verify new document in DB
        var newDoc = await _repo.GetDocumentRawAsync(res.NewVaultId);
        Assert.NotNull(newDoc);
        Assert.Equal(1, newDoc.PageCount);
        Assert.Equal("04 - محضر تسليم مفتاح", newDoc.Category);
        Assert.Equal(sourceDoc.BatchId, newDoc.BatchId); // Batch lineage preserved!

        // Verify pages table
        var sourcePages = await _repo.GetPagesByVaultIdAsync(sourceVaultId);
        Assert.Equal(3, sourcePages.Count);
        Assert.Equal(1, sourcePages[0].PageNumber);
        Assert.Equal(2, sourcePages[1].PageNumber);
        Assert.Equal(3, sourcePages[2].PageNumber);

        var newPages = await _repo.GetPagesByVaultIdAsync(res.NewVaultId);
        Assert.Single(newPages);
        Assert.Equal(4, newPages[0].PageNumber);
        Assert.Equal("04 - محضر تسليم مفتاح", newPages[0].Category);
    }

    [Fact]
    public async Task ExtractPagesAsync_AllPagesExtracted_DeletesSourceDocument()
    {
        // Arrange
        await _repo.AddAreaAsync("AreaExtractAll", "EXA");
        await _repo.AddHouseAsync("H-EXA", "AreaExtractAll");
        var tenant = await _repo.AddTenantAsync("H-EXA", "Extract All Tenant", "2024-01-01");

        var sourceVaultId = Guid.NewGuid().ToString("N");
        await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "AreaExtractAll",
            HouseId = "H-EXA",
            TenantId = tenant.Id,
            Category = "10 - صيانة",
            ArabicTitle = "وثيقة كاملة للنقل",
            VaultId = sourceVaultId,
            PageCount = 2
        });

        // Act: Extract both pages 1 & 2
        var extractReq = new ExtractPagesRequestDto
        {
            PageNumbers = new List<int> { 1, 2 },
            TargetCategory = "07 - استقطاع إيجار",
            DeleteFromSource = true
        };

        var res = await _repo.ExtractPagesAsync("AreaExtractAll", "H-EXA", sourceVaultId, extractReq);

        // Assert
        Assert.True(res.SourceDeleted);
        Assert.Equal(0, res.SourceRemainingPages);
        Assert.Equal(2, res.NewPageCount);

        var sourceDoc = await _repo.GetDocumentRawAsync(sourceVaultId);
        Assert.Null(sourceDoc); // Deleted cleanly

        var newDoc = await _repo.GetDocumentRawAsync(res.NewVaultId);
        Assert.NotNull(newDoc);
        Assert.Equal(2, newDoc.PageCount);
        Assert.Equal("07 - استقطاع إيجار", newDoc.Category);
    }

    [Fact]
    public async Task DeletePagesAsync_RemovesPage_UpdatesPageCountAndBatchCount()
    {
        // Arrange
        await _repo.AddAreaAsync("AreaDelPage", "DEL");
        await _repo.AddHouseAsync("H-DEL", "AreaDelPage");
        var tenant = await _repo.AddTenantAsync("H-DEL", "Delete Page Tenant", "2024-01-01");

        var sourceVaultId = Guid.NewGuid().ToString("N");
        await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "AreaDelPage",
            HouseId = "H-DEL",
            TenantId = tenant.Id,
            Category = "06 - كهرباء وماء",
            ArabicTitle = "فاتورة مع صفحة بيضاء",
            VaultId = sourceVaultId,
            PageCount = 3
        });

        // Act: Delete page 2 (e.g. blank page)
        var delReq = new DeletePagesRequestDto
        {
            PageNumbers = new List<int> { 2 }
        };

        var res = await _repo.DeletePagesAsync("AreaDelPage", "H-DEL", sourceVaultId, delReq);

        // Assert
        Assert.Equal("success", res.Status);
        Assert.Equal(2, res.RemainingPages);
        Assert.False(res.DocumentDeleted);

        var doc = await _repo.GetDocumentRawAsync(sourceVaultId);
        Assert.NotNull(doc);
        Assert.Equal(2, doc.PageCount);

        var pages = await _repo.GetPagesByVaultIdAsync(sourceVaultId);
        Assert.Equal(2, pages.Count);
        Assert.Equal(1, pages[0].PageNumber);
        Assert.Equal(3, pages[1].PageNumber);
    }

    [Fact]
    public async Task ReorderPagesAsync_UpdatesPageSequence()
    {
        // Arrange
        await _repo.AddAreaAsync("AreaReorder", "ORD");
        await _repo.AddHouseAsync("H-ORD", "AreaReorder");
        var tenant = await _repo.AddTenantAsync("H-ORD", "Reorder Tenant", "2024-01-01");

        var sourceVaultId = Guid.NewGuid().ToString("N");
        await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "AreaReorder",
            HouseId = "H-ORD",
            TenantId = tenant.Id,
            Category = "05 - عقود",
            ArabicTitle = "عقد غير مرتب",
            VaultId = sourceVaultId,
            PageCount = 3
        });

        // Act: Reorder pages to [3, 1, 2]
        var reorderReq = new ReorderPagesRequestDto
        {
            PageOrder = new List<int> { 3, 1, 2 }
        };

        var res = await _repo.ReorderPagesAsync("AreaReorder", "H-ORD", sourceVaultId, reorderReq);

        // Assert
        Assert.Equal("success", res.Status);
        Assert.Equal(new List<int> { 3, 1, 2 }, res.PageOrder);

        var pages = await _repo.GetPagesByVaultIdAsync(sourceVaultId);
        Assert.Equal(3, pages.Count);
    }

    [Fact]
    public async Task DeletePagesAsync_AllPagesDeleted_DeletesDocumentAndUnlinksFromDatabase()
    {
        // Arrange
        await _repo.AddAreaAsync("AreaDelAll", "DALL");
        await _repo.AddHouseAsync("H-DALL", "AreaDelAll");
        var tenant = await _repo.AddTenantAsync("H-DALL", "Delete All Tenant", "2024-01-01");

        var sourceVaultId = Guid.NewGuid().ToString("N");
        await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "AreaDelAll",
            HouseId = "H-DALL",
            TenantId = tenant.Id,
            Category = "06 - كهرباء وماء",
            ArabicTitle = "فاتورة كاملة للحذف",
            VaultId = sourceVaultId,
            PageCount = 2
        });

        // Act: Delete both pages 1 and 2
        var delReq = new DeletePagesRequestDto
        {
            PageNumbers = new List<int> { 1, 2 }
        };

        var res = await _repo.DeletePagesAsync("AreaDelAll", "H-DALL", sourceVaultId, delReq);

        // Assert
        Assert.Equal("success", res.Status);
        Assert.Equal(0, res.RemainingPages);
        Assert.True(res.DocumentDeleted);

        // Document should be deleted from DB
        var doc = await _repo.GetDocumentRawAsync(sourceVaultId);
        Assert.Null(doc);

        var pages = await _repo.GetPagesByVaultIdAsync(sourceVaultId);
        Assert.Empty(pages);
    }

    [Fact]
    public async Task ExtractPagesAsync_TargetTenantDifferentFromSource_ReassignsTenantCleanly()
    {
        // Arrange
        await _repo.AddAreaAsync("AreaDiffTenant", "ADT");
        await _repo.AddHouseAsync("H-ADT", "AreaDiffTenant");
        var tenant1 = await _repo.AddTenantAsync("H-ADT", "Original Tenant 1", "2023-01-01");
        var tenant2 = await _repo.AddTenantAsync("H-ADT", "Target Tenant 2", "2024-01-01");

        var sourceVaultId = Guid.NewGuid().ToString("N");
        await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "AreaDiffTenant",
            HouseId = "H-ADT",
            TenantId = tenant1.Id,
            Category = "10 - صيانة",
            ArabicTitle = "وثيقة مشتركة",
            VaultId = sourceVaultId,
            PageCount = 3
        });

        // Act: Extract page 3 to tenant2
        var extractReq = new ExtractPagesRequestDto
        {
            PageNumbers = new List<int> { 3 },
            TargetCategory = "04 - محضر تسليم مفتاح",
            TargetTenantId = tenant2.Id,
            TargetTitle = "تسليم مفتاح للمستأجر الثاني",
            DeleteFromSource = true
        };

        var res = await _repo.ExtractPagesAsync("AreaDiffTenant", "H-ADT", sourceVaultId, extractReq);

        // Assert
        Assert.Equal("success", res.Status);

        // Source document remains with tenant1
        var sourceDoc = await _repo.GetDocumentRawAsync(sourceVaultId);
        Assert.NotNull(sourceDoc);
        Assert.Equal(tenant1.Id, sourceDoc.TenantId);
        Assert.Equal(2, sourceDoc.PageCount);

        // New document assigned to tenant2
        var newDoc = await _repo.GetDocumentRawAsync(res.NewVaultId);
        Assert.NotNull(newDoc);
        Assert.Equal(tenant2.Id, newDoc.TenantId);
        Assert.Equal("04 - محضر تسليم مفتاح", newDoc.Category);
        Assert.Equal(1, newDoc.PageCount);

        var newPages = await _repo.GetPagesByVaultIdAsync(res.NewVaultId);
        Assert.Single(newPages);
        Assert.Equal(tenant2.Id, newPages[0].TenantId);
    }

    [Fact]
    public async Task ExtractPagesAsync_CustomCategoryAndDate_SetsExplicitValues()
    {
        // Arrange
        await _repo.AddAreaAsync("AreaCustomCat", "ACC");
        await _repo.AddHouseAsync("H-ACC", "AreaCustomCat");
        var tenant = await _repo.AddTenantAsync("H-ACC", "Custom Cat Tenant", "2024-01-01");

        var sourceVaultId = Guid.NewGuid().ToString("N");
        await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "AreaCustomCat",
            HouseId = "H-ACC",
            TenantId = tenant.Id,
            Category = "05 - عقود",
            ArabicTitle = "عقد أصلي",
            VaultId = sourceVaultId,
            PageCount = 2
        });

        // Act: Extract page 2 into custom folder and custom date
        var extractReq = new ExtractPagesRequestDto
        {
            PageNumbers = new List<int> { 2 },
            TargetCategory = "14 - تقارير فنية خاصة",
            TargetTitle = "تقرير فني مستخرج",
            TargetDate = "2025-08-20",
            TargetNotes = "ملاحظات الفحص الفني",
            DeleteFromSource = true
        };

        var res = await _repo.ExtractPagesAsync("AreaCustomCat", "H-ACC", sourceVaultId, extractReq);

        // Assert
        Assert.Equal("success", res.Status);
        var newDoc = await _repo.GetDocumentRawAsync(res.NewVaultId);
        Assert.NotNull(newDoc);
        Assert.Equal("14 - تقارير فنية خاصة", newDoc.Category);
        Assert.Equal("2025-08-20", newDoc.PrimaryDate);
        Assert.Equal("تقرير فني مستخرج", newDoc.ArabicTitle);
        Assert.Equal(1, newDoc.IsManual);
    }

    [Fact]
    public async Task DeletePagesAsync_DecrementsBatchPageCountInBatchesTable()
    {
        // Arrange
        await _repo.AddAreaAsync("AreaBatchParity", "ABP");
        await _repo.AddHouseAsync("H-ABP", "AreaBatchParity");
        var tenant = await _repo.AddTenantAsync("H-ABP", "Batch Parity Tenant", "2024-01-01");

        var sourceVaultId = Guid.NewGuid().ToString("N");
        await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "AreaBatchParity",
            HouseId = "H-ABP",
            TenantId = tenant.Id,
            Category = "10 - صيانة",
            ArabicTitle = "دفتر صيانة مع إشعار",
            VaultId = sourceVaultId,
            PageCount = 4
        });

        var sourceDoc = await _repo.GetDocumentRawAsync(sourceVaultId);
        Assert.NotNull(sourceDoc);
        Assert.True(sourceDoc.BatchId > 0);

        using var conn = _factory.CreateConnection();
        var initialBatchCount = await conn.QuerySingleAsync<int>(
            "SELECT page_count FROM batches WHERE id = @BatchId",
            new { BatchId = sourceDoc.BatchId });

        // Act: Delete 2 pages
        var delReq = new DeletePagesRequestDto
        {
            PageNumbers = new List<int> { 2, 4 }
        };
        var res = await _repo.DeletePagesAsync("AreaBatchParity", "H-ABP", sourceVaultId, delReq);

        // Assert
        Assert.Equal(2, res.RemainingPages);

        var finalBatchCount = await conn.QuerySingleAsync<int>(
            "SELECT page_count FROM batches WHERE id = @BatchId",
            new { BatchId = sourceDoc.BatchId });

        Assert.Equal(initialBatchCount - 2, finalBatchCount);
    }

    [Fact]
    public async Task ExtractPagesAsync_NonExistentVaultId_ThrowsKeyNotFoundException()
    {
        var extractReq = new ExtractPagesRequestDto
        {
            PageNumbers = new List<int> { 1 },
            TargetCategory = "04 - محضر تسليم مفتاح"
        };

        await Assert.ThrowsAsync<KeyNotFoundException>(() =>
            _repo.ExtractPagesAsync("NonExistentArea", "NonExistentHouse", "non_existent_vault_id", extractReq));
    }

    [Fact]
    public async Task DeletePagesAsync_NonExistentVaultId_ThrowsKeyNotFoundException()
    {
        var delReq = new DeletePagesRequestDto
        {
            PageNumbers = new List<int> { 1 }
        };

        await Assert.ThrowsAsync<KeyNotFoundException>(() =>
            _repo.DeletePagesAsync("NonExistentArea", "NonExistentHouse", "non_existent_vault_id", delReq));
    }

    [Fact]
    public async Task ExtractPagesAsync_WithDefaultAreaAndHouseInUrl_ResolvesRealAreaAndHouseFromDatabase()
    {
        // Arrange
        await _repo.AddAreaAsync("RealArea", "RA");
        await _repo.AddHouseAsync("H-Real", "RealArea");
        var tenant = await _repo.AddTenantAsync("H-Real", "Tenant Real", "2024-01-01");

        var sourceVaultId = Guid.NewGuid().ToString("N");
        await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "RealArea",
            HouseId = "H-Real",
            TenantId = tenant.Id,
            Category = "05 - عقود",
            ArabicTitle = "عقد أصلي",
            VaultId = sourceVaultId,
            PageCount = 3
        });

        // Act: Pass "default" for areaId and houseId in the method call
        var extractReq = new ExtractPagesRequestDto
        {
            PageNumbers = new List<int> { 2 },
            TargetCategory = "04 - محضر تسليم مفتاح",
            TargetTitle = "محضر مفصول",
            DeleteFromSource = true
        };

        var res = await _repo.ExtractPagesAsync("default", "default", sourceVaultId, extractReq);

        // Assert
        Assert.Equal("success", res.Status);
        var newDoc = await _repo.GetDocumentRawAsync(res.NewVaultId);
        Assert.NotNull(newDoc);
        Assert.Equal("H-Real", newDoc.HouseId);
        Assert.Equal(tenant.Id, newDoc.TenantId);
        Assert.Equal("04 - محضر تسليم مفتاح", newDoc.Category);
        Assert.Equal(1, newDoc.PageCount);

        var remainingSourceDoc = await _repo.GetDocumentRawAsync(sourceVaultId);
        Assert.NotNull(remainingSourceDoc);
        Assert.Equal("H-Real", remainingSourceDoc.HouseId);
        Assert.Equal(2, remainingSourceDoc.PageCount);
    }

    [Fact]
    public async Task ReorderPagesAsync_WithDefaultAreaAndHouseInUrl_ResolvesRealAreaAndHouseFromDatabase()
    {
        // Arrange
        await _repo.AddAreaAsync("RealArea2", "RA2");
        await _repo.AddHouseAsync("H-Real2", "RealArea2");
        var tenant = await _repo.AddTenantAsync("H-Real2", "Tenant Real 2", "2024-01-01");

        var sourceVaultId = Guid.NewGuid().ToString("N");
        await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "RealArea2",
            HouseId = "H-Real2",
            TenantId = tenant.Id,
            Category = "05 - عقود",
            ArabicTitle = "عقد ترتيب",
            VaultId = sourceVaultId,
            PageCount = 2
        });

        var reorderReq = new ReorderPagesRequestDto
        {
            PageOrder = new List<int> { 2, 1 }
        };

        var res = await _repo.ReorderPagesAsync("default", "default", sourceVaultId, reorderReq);

        Assert.Equal("success", res.Status);
        Assert.Equal(new List<int> { 2, 1 }, res.PageOrder);

        var doc = await _repo.GetDocumentRawAsync(sourceVaultId);
        Assert.NotNull(doc);
        Assert.Equal(1, doc.IsManual);
    }

    [Fact]
    public async Task ExtractPagesAsync_WithTargetTenantZeroOrNull_SafelyResolvesTenantWithoutForeignConstraintViolation()
    {
        // Arrange
        await _repo.AddAreaAsync("AreaSafeTenant", "AST");
        await _repo.AddHouseAsync("H-AST", "AreaSafeTenant");
        var tenant = await _repo.AddTenantAsync("H-AST", "Resident Tenant", "2024-01-01");

        var sourceVaultId = Guid.NewGuid().ToString("N");
        await _repo.AddManualDocumentAsync(new IngestRequestDto
        {
            AreaId = "AreaSafeTenant",
            HouseId = "H-AST",
            TenantId = tenant.Id,
            Category = "10 - صيانة",
            ArabicTitle = "صيانة عامة",
            VaultId = sourceVaultId,
            PageCount = 2
        });

        // Act: Extract with TargetTenantId = 0 (representing "كامل المنزل (عام)")
        var extractReq = new ExtractPagesRequestDto
        {
            PageNumbers = new List<int> { 1 },
            TargetCategory = "13 - رسائل متنوعة",
            TargetTenantId = 0,
            DeleteFromSource = true
        };

        var res = await _repo.ExtractPagesAsync("AreaSafeTenant", "H-AST", sourceVaultId, extractReq);

        Assert.Equal("success", res.Status);
        var newDoc = await _repo.GetDocumentRawAsync(res.NewVaultId);
        Assert.NotNull(newDoc);
        Assert.True(newDoc.TenantId > 0);
        Assert.Equal("H-AST", newDoc.HouseId);
    }

    [Fact]
    public async Task ExtractPagesAsync_WithPhysicalPdf_SlicesAndUpdatesSourceAndTargetPdfs()
    {
        var tempAreas = Path.Combine(Path.GetTempPath(), $"areas_{Guid.NewGuid():N}");
        try
        {
            var areaId = "AreaPhys";
            var houseId = "100";
            var vaultId = Guid.NewGuid().ToString("N");
            var vaultDir = Path.Combine(tempAreas, areaId, houseId, "vault");
            Directory.CreateDirectory(vaultDir);

            var pdfFile = Path.Combine(vaultDir, $"doc_{vaultId}.pdf");
            using (var doc = new PdfSharpCore.Pdf.PdfDocument())
            {
                doc.AddPage();
                doc.AddPage();
                doc.AddPage();
                doc.Save(pdfFile);
            }

            await _repo.AddAreaAsync(areaId, "AP");
            await _repo.AddHouseAsync(houseId, areaId);
            var tenant = await _repo.AddTenantAsync(houseId, "Tenant 100", "2024-01-01");
            await _repo.AddManualDocumentAsync(new IngestRequestDto
            {
                AreaId = areaId,
                HouseId = houseId,
                TenantId = tenant.Id,
                Category = "10 - صيانة",
                ArabicTitle = "وثيقة 3 صفحات",
                VaultId = vaultId,
                PageCount = 3
            });

            var extractReq = new ExtractPagesRequestDto
            {
                PageNumbers = new List<int> { 2 },
                TargetCategory = "04 - محضر تسليم مفتاح",
                TargetTenantId = tenant.Id,
                TargetTitle = "صفحة منفصلة",
                DeleteFromSource = true
            };

            var res = await _repo.ExtractPagesAsync(areaId, houseId, vaultId, extractReq, tempAreas);

            Assert.Equal("success", res.Status);

            // Check source PDF
            Assert.True(File.Exists(pdfFile));
            using (var srcPdf = PdfSharpCore.Pdf.IO.PdfReader.Open(pdfFile, PdfSharpCore.Pdf.IO.PdfDocumentOpenMode.Import))
            {
                Assert.Equal(2, srcPdf.PageCount);
            }

            // Check extracted PDF
            var newPdfFile = Path.Combine(vaultDir, $"doc_{res.NewVaultId}.pdf");
            Assert.True(File.Exists(newPdfFile));
            using (var newPdf = PdfSharpCore.Pdf.IO.PdfReader.Open(newPdfFile, PdfSharpCore.Pdf.IO.PdfDocumentOpenMode.Import))
            {
                Assert.Equal(1, newPdf.PageCount);
            }
        }
        finally
        {
            if (Directory.Exists(tempAreas))
            {
                try { Directory.Delete(tempAreas, true); } catch { }
            }
        }
    }

    [Fact]
    public async Task ExtractPagesAsync_WithPhysicalPdf_CopyMode_KeepsSourcePdfAndCreatesTargetPdf()
    {
        var tempAreas = Path.Combine(Path.GetTempPath(), $"areas_{Guid.NewGuid():N}");
        try
        {
            var areaId = "AreaPhysCopy";
            var houseId = "101";
            var vaultId = Guid.NewGuid().ToString("N");
            var vaultDir = Path.Combine(tempAreas, areaId, houseId, "vault");
            Directory.CreateDirectory(vaultDir);

            var pdfFile = Path.Combine(vaultDir, $"doc_{vaultId}.pdf");
            using (var doc = new PdfSharpCore.Pdf.PdfDocument())
            {
                doc.AddPage();
                doc.AddPage();
                doc.AddPage();
                doc.Save(pdfFile);
            }

            await _repo.AddAreaAsync(areaId, "APC");
            await _repo.AddHouseAsync(houseId, areaId);
            var tenant = await _repo.AddTenantAsync(houseId, "Tenant 101", "2024-01-01");
            await _repo.AddManualDocumentAsync(new IngestRequestDto
            {
                AreaId = areaId,
                HouseId = houseId,
                TenantId = tenant.Id,
                Category = "05 - عقود",
                ArabicTitle = "عقد أصلي 3 صفحات",
                VaultId = vaultId,
                PageCount = 3
            });

            var extractReq = new ExtractPagesRequestDto
            {
                PageNumbers = new List<int> { 1, 2 },
                TargetCategory = "02 - بيانات شخصية",
                TargetTenantId = tenant.Id,
                TargetTitle = "نسخة صفحتين",
                DeleteFromSource = false // COPY MODE
            };

            var res = await _repo.ExtractPagesAsync(areaId, houseId, vaultId, extractReq, tempAreas);

            Assert.Equal("success", res.Status);
            Assert.Equal(3, res.SourceRemainingPages); // Source unchanged

            // Check source PDF is intact (still 3 pages)
            Assert.True(File.Exists(pdfFile));
            using (var srcPdf = PdfSharpCore.Pdf.IO.PdfReader.Open(pdfFile, PdfSharpCore.Pdf.IO.PdfDocumentOpenMode.Import))
            {
                Assert.Equal(3, srcPdf.PageCount);
            }

            // Check source document in DB is intact
            var srcDoc = await _repo.GetDocumentRawAsync(vaultId);
            Assert.NotNull(srcDoc);
            Assert.Equal(3, srcDoc.PageCount);

            // Check new copied PDF exists with 2 pages
            var newPdfFile = Path.Combine(vaultDir, $"doc_{res.NewVaultId}.pdf");
            Assert.True(File.Exists(newPdfFile));
            using (var newPdf = PdfSharpCore.Pdf.IO.PdfReader.Open(newPdfFile, PdfSharpCore.Pdf.IO.PdfDocumentOpenMode.Import))
            {
                Assert.Equal(2, newPdf.PageCount);
            }

            // Check new document in DB has 2 pages
            var newDoc = await _repo.GetDocumentRawAsync(res.NewVaultId!);
            Assert.NotNull(newDoc);
            Assert.Equal(2, newDoc.PageCount);
        }
        finally
        {
            if (Directory.Exists(tempAreas))
            {
                try { Directory.Delete(tempAreas, true); } catch { }
            }
        }
    }

    [Fact]
    public async Task DeletePagesAsync_WithPhysicalPdf_RemovesPagesFromDiskPdf()
    {
        var tempAreas = Path.Combine(Path.GetTempPath(), $"areas_{Guid.NewGuid():N}");
        try
        {
            var areaId = "AreaPhysDel";
            var houseId = "102";
            var vaultId = Guid.NewGuid().ToString("N");
            var vaultDir = Path.Combine(tempAreas, areaId, houseId, "vault");
            Directory.CreateDirectory(vaultDir);

            var pdfFile = Path.Combine(vaultDir, $"doc_{vaultId}.pdf");
            using (var doc = new PdfSharpCore.Pdf.PdfDocument())
            {
                doc.AddPage();
                doc.AddPage();
                doc.AddPage();
                doc.AddPage();
                doc.Save(pdfFile);
            }

            await _repo.AddAreaAsync(areaId, "APD");
            await _repo.AddHouseAsync(houseId, areaId);
            var tenant = await _repo.AddTenantAsync(houseId, "Tenant 102", "2024-01-01");
            await _repo.AddManualDocumentAsync(new IngestRequestDto
            {
                AreaId = areaId,
                HouseId = houseId,
                TenantId = tenant.Id,
                Category = "06 - كهرباء وماء",
                ArabicTitle = "فاتورة 4 صفحات",
                VaultId = vaultId,
                PageCount = 4
            });

            var deleteReq = new DeletePagesRequestDto
            {
                PageNumbers = new List<int> { 2, 4 }
            };

            var res = await _repo.DeletePagesAsync(areaId, houseId, vaultId, deleteReq, tempAreas);

            Assert.Equal("success", res.Status);
            Assert.Equal(2, res.RemainingPages);
            Assert.False(res.DocumentDeleted);

            // Check disk PDF now has 2 pages
            Assert.True(File.Exists(pdfFile));
            using (var updatedPdf = PdfSharpCore.Pdf.IO.PdfReader.Open(pdfFile, PdfSharpCore.Pdf.IO.PdfDocumentOpenMode.Import))
            {
                Assert.Equal(2, updatedPdf.PageCount);
            }

            // Check metadata in DB
            var meta = await _repo.GetDocumentRawAsync(vaultId);
            Assert.NotNull(meta);
            Assert.Equal(2, meta.PageCount);
        }
        finally
        {
            if (Directory.Exists(tempAreas))
            {
                try { Directory.Delete(tempAreas, true); } catch { }
            }
        }
    }

    [Fact]
    public async Task DeletePagesAsync_WithPhysicalPdf_AllPagesDeleted_RemovesPdfFromDisk()
    {
        var tempAreas = Path.Combine(Path.GetTempPath(), $"areas_{Guid.NewGuid():N}");
        try
        {
            var areaId = "AreaPhysDelAll";
            var houseId = "103";
            var vaultId = Guid.NewGuid().ToString("N");
            var vaultDir = Path.Combine(tempAreas, areaId, houseId, "vault");
            Directory.CreateDirectory(vaultDir);

            var pdfFile = Path.Combine(vaultDir, $"doc_{vaultId}.pdf");
            using (var doc = new PdfSharpCore.Pdf.PdfDocument())
            {
                doc.AddPage();
                doc.AddPage();
                doc.Save(pdfFile);
            }

            await _repo.AddAreaAsync(areaId, "APDA");
            await _repo.AddHouseAsync(houseId, areaId);
            var tenant = await _repo.AddTenantAsync(houseId, "Tenant 103", "2024-01-01");
            await _repo.AddManualDocumentAsync(new IngestRequestDto
            {
                AreaId = areaId,
                HouseId = houseId,
                TenantId = tenant.Id,
                Category = "07 - استقطاع إيجار",
                ArabicTitle = "استقطاع صفحتين",
                VaultId = vaultId,
                PageCount = 2
            });

            var deleteReq = new DeletePagesRequestDto
            {
                PageNumbers = new List<int> { 1, 2 }
            };

            var res = await _repo.DeletePagesAsync(areaId, houseId, vaultId, deleteReq, tempAreas);

            Assert.Equal("success", res.Status);
            Assert.Equal(0, res.RemainingPages);
            Assert.True(res.DocumentDeleted);

            // Check disk PDF is removed
            Assert.False(File.Exists(pdfFile));

            // Check document in DB is removed
            var meta = await _repo.GetDocumentRawAsync(vaultId);
            Assert.Null(meta);
        }
        finally
        {
            if (Directory.Exists(tempAreas))
            {
                try { Directory.Delete(tempAreas, true); } catch { }
            }
        }
    }
}



