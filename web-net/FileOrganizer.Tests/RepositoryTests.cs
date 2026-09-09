using FileOrganizer.Web.Common;
using FileOrganizer.Web.Data;
using FileOrganizer.Web.Models;
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
}
