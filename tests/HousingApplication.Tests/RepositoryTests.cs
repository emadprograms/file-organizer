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
        Assert.Contains("فترة الإيجار: 2015", pastItem.DurationStrAr);

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

        // Act: Update title, category, tenant, and notes
        var updateResult = await _repo.UpdateDocumentAsync(
            ingest.VaultId!,
            arabicTitle: "عنوان معدل جديد",
            category: "06 - كهرباء وماء",
            tenantId: t2.Id,
            notes: "تم التعديل بواسطة النظام"
        );

        // Assert
        Assert.NotNull(updateResult);
        Assert.Equal("عنوان معدل جديد", updateResult.ArabicTitle);
        Assert.Equal("06 - كهرباء وماء", updateResult.Category);
        Assert.Equal(t2.Id, updateResult.TenantId);
        Assert.Equal("مستأجر 2", updateResult.TenantName);

        // Assert pages also synced
        var pages = await _repo.GetPagesByVaultIdAsync(ingest.VaultId!);
        Assert.All(pages, p =>
        {
            Assert.Equal(t2.Id, p.TenantId);
            Assert.Equal("06 - كهرباء وماء", p.FineCategory);
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
            await conn.ExecuteAsync("UPDATE documents SET is_manual = 0, tenant_id = @ApplicantId WHERE vault_id = @VaultId;",
                new { ApplicantId = applicant.Id, VaultId = vaultId });
            await conn.ExecuteAsync("UPDATE pages SET tenant_id = @ApplicantId WHERE vault_id = @VaultId;",
                new { ApplicantId = applicant.Id, VaultId = vaultId });
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
}
