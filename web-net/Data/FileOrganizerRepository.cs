using System.Data;
using System.Text.RegularExpressions;
using Dapper;
using FileOrganizer.Web.Common;
using FileOrganizer.Web.Models;
using Microsoft.Data.Sqlite;

using Microsoft.Extensions.Configuration;

namespace FileOrganizer.Web.Data;

public class FileOrganizerRepository : IFileOrganizerRepository
{
    private readonly ISqliteDbConnectionFactory _connectionFactory;
    private readonly IConfiguration? _configuration;

    public FileOrganizerRepository(ISqliteDbConnectionFactory connectionFactory, IConfiguration? configuration = null)
    {
        _connectionFactory = connectionFactory;
        _configuration = configuration;
    }

    public async Task EnsureSchemaAsync()
    {
        await using var conn = await _connectionFactory.CreateConnectionAsync();
        await DatabaseInitializer.InitializeSchemaAsync(conn);

        try
        {
            await conn.ExecuteAsync("ALTER TABLE documents ADD COLUMN is_timeline_visible INTEGER DEFAULT 1;");
        }
        catch (SqliteException) { }
    }

    public async Task<IReadOnlyList<TreeAreaDto>> GetTreeAsync(bool includeCategories = false, bool includeTimeline = false)
    {
        await using var conn = await _connectionFactory.CreateConnectionAsync();

        var areas = (await conn.QueryAsync<Area>("SELECT id, code FROM areas ORDER BY id;")).ToList();
        var houses = (await conn.QueryAsync<House>("SELECT id, area_id AS AreaId FROM houses ORDER BY id;")).ToList();
        var tenants = (await conn.QueryAsync<Tenant>(@"
            SELECT id, house_id AS HouseId, name, start_date AS StartDate, end_date AS EndDate 
            FROM tenants 
            ORDER BY (CASE WHEN end_date IS NULL OR end_date = '' OR LOWER(end_date) = 'present' THEN 1 ELSE 0 END) DESC, 
                     start_date DESC, id DESC;")).ToList();

        var docCounts = (await conn.QueryAsync<(string HouseId, string? Category, int DocCount)>(@"
            SELECT house_id AS HouseId, category AS Category, COUNT(*) AS DocCount 
            FROM documents 
            GROUP BY house_id, category;")).ToList();

        var timelineDocs = includeTimeline
            ? (await conn.QueryAsync<(string VaultId, string HouseId, string? PrimaryDate, string? ArabicTitle, string? Category)>(@"
                SELECT vault_id AS VaultId, house_id AS HouseId, primary_date AS PrimaryDate, arabic_title AS ArabicTitle, category AS Category 
                FROM documents 
                ORDER BY primary_date DESC;")).ToList()
            : null;

        var housesByArea = houses.GroupBy(h => h.AreaId).ToDictionary(g => g.Key, g => g.ToList());
        var tenantsByHouse = tenants.GroupBy(t => t.HouseId).ToDictionary(g => g.Key, g => g.ToList());

        var catCountsByHouse = new Dictionary<string, Dictionary<string, int>>();
        var totalDocsByHouse = new Dictionary<string, int>();

        foreach (var dc in docCounts)
        {
            totalDocsByHouse[dc.HouseId] = totalDocsByHouse.GetValueOrDefault(dc.HouseId) + dc.DocCount;
            if (!string.IsNullOrWhiteSpace(dc.Category))
            {
                var cleanCat = Constants.CleanCategoryName(dc.Category);
                if (!catCountsByHouse.TryGetValue(dc.HouseId, out var catDict))
                {
                    catDict = new Dictionary<string, int>();
                    catCountsByHouse[dc.HouseId] = catDict;
                }
                catDict[cleanCat] = catDict.GetValueOrDefault(cleanCat) + dc.DocCount;
            }
        }

        var currentYear = DateTime.Now.Year;
        var todayStr = DateTime.Today.ToString("yyyy-MM-dd");
        var result = new List<TreeAreaDto>();

        foreach (var area in areas)
        {
            var areaHouses = housesByArea.GetValueOrDefault(area.Id, new List<House>());
            // Natural sort houses by numeric prefix if available
            areaHouses.Sort((a, b) =>
            {
                var m1 = Regex.Match(a.Id, @"(\d+)");
                var m2 = Regex.Match(b.Id, @"(\d+)");
                if (m1.Success && m2.Success)
                {
                    var n1 = int.Parse(m1.Groups[1].Value);
                    var n2 = int.Parse(m2.Groups[1].Value);
                    var cmp = n1.CompareTo(n2);
                    if (cmp != 0) return cmp;
                }
                return string.Compare(a.Id, b.Id, StringComparison.OrdinalIgnoreCase);
            });

            var houseNodes = new List<TreeHouseDto>();

            foreach (var house in areaHouses)
            {
                var hTenants = tenantsByHouse.GetValueOrDefault(house.Id, new List<Tenant>());

                // Find active tenant
                Tenant? activeTenant = hTenants.FirstOrDefault(t =>
                    string.IsNullOrEmpty(t.EndDate) ||
                    t.EndDate.ToLowerInvariant() == "present" ||
                    string.Compare(t.EndDate, todayStr, StringComparison.Ordinal) >= 0);

                if (activeTenant == null && house.Id.Contains(" - "))
                {
                    var cand = house.Id.Split(" - ", 2)[1].Trim();
                    activeTenant = hTenants.FirstOrDefault(t => t.Name == cand);
                }

                if (activeTenant == null && hTenants.Count > 0)
                {
                    activeTenant = hTenants[0];
                }

                string? houseDurationCat = null;
                string? houseSubtitle = null;
                string? activeTenantName = null;

                if (activeTenant != null)
                {
                    activeTenantName = activeTenant.Name;
                    var mYear = Regex.Match(activeTenant.StartDate, @"(\d{4})");
                    if (mYear.Success)
                    {
                        var startYear = int.Parse(mYear.Groups[1].Value);
                        var duration = currentYear - startYear;
                        if (duration < 5)
                            houseDurationCat = "short";
                        else if (duration < 10)
                            houseDurationCat = "medium";
                        else
                            houseDurationCat = "long";

                        houseSubtitle = $"Since {startYear} ({duration}y)";
                    }
                }
                else if (hTenants.Count > 0)
                {
                    var latest = hTenants[0];
                    var sStr = latest.StartDate.Length >= 4 ? latest.StartDate[..4] : "";
                    var eStr = (!string.IsNullOrEmpty(latest.EndDate) && latest.EndDate.Length >= 4) ? latest.EndDate[..4] : "";
                    if (!string.IsNullOrEmpty(sStr) && !string.IsNullOrEmpty(eStr) && sStr != eStr)
                        houseSubtitle = $"{sStr} - {eStr}";
                    else if (!string.IsNullOrEmpty(sStr))
                        houseSubtitle = sStr;
                }

                var tenantNodes = new List<TreeTenantDto>();
                foreach (var t in hTenants)
                {
                    var sM = Regex.Match(t.StartDate ?? "", @"(\d{4})");
                    var eM = Regex.Match(t.EndDate ?? "", @"(\d{4})");
                    int? sY = sM.Success ? int.Parse(sM.Groups[1].Value) : null;
                    int? eY = eM.Success ? int.Parse(eM.Groups[1].Value) : null;

                    var isActive = (activeTenant != null && t.Id == activeTenant.Id);
                    string? tDurCat = null;
                    string? tSub = null;

                    if (sY.HasValue)
                    {
                        if (isActive)
                        {
                            var dur = currentYear - sY.Value;
                            tDurCat = dur < 5 ? "short" : (dur < 10 ? "medium" : "long");
                            tSub = $"{sY.Value} - Present";
                        }
                        else if (eY.HasValue && eY.Value != sY.Value)
                        {
                            tSub = $"{sY.Value} - {eY.Value}";
                        }
                        else
                        {
                            tSub = $"{sY.Value}";
                        }
                    }

                    tenantNodes.Add(new TreeTenantDto
                    {
                        Id = $"{house.Id}_{t.Name}",
                        Name = t.Name,
                        Subtitle = tSub,
                        DurationCategory = tDurCat,
                        Type = "tenant"
                    });
                }

                var hCatCounts = catCountsByHouse.GetValueOrDefault(house.Id, new Dictionary<string, int>());
                var hTotalDocs = totalDocsByHouse.GetValueOrDefault(house.Id, 0);

                houseNodes.Add(new TreeHouseDto
                {
                    Id = house.Id,
                    Name = house.Id,
                    Type = "house",
                    Subtitle = houseSubtitle,
                    DurationCategory = houseDurationCat,
                    CurrentTenant = activeTenantName,
                    TotalDocuments = hTotalDocs,
                    CategoryCounts = hCatCounts,
                    Children = tenantNodes
                });
            }

            result.Add(new TreeAreaDto
            {
                Id = $"area_{area.Id}",
                Name = area.Id,
                Type = "area",
                Children = houseNodes
            });
        }

        return result;
    }

    public async Task<IReadOnlyList<HouseCardDto>> GetHousesAsync(string? areaId = null)
    {
        await using var conn = await _connectionFactory.CreateConnectionAsync();

        string sqlHouses = string.IsNullOrWhiteSpace(areaId)
            ? "SELECT id, area_id AS AreaId FROM houses ORDER BY id;"
            : "SELECT id, area_id AS AreaId FROM houses WHERE area_id = @AreaId ORDER BY id;";

        var houses = (await conn.QueryAsync<House>(sqlHouses, new { AreaId = areaId })).ToList();
        var houseIds = houses.Select(h => h.Id).ToList();
        if (houseIds.Count == 0)
            return Array.Empty<HouseCardDto>();

        var tenants = (await conn.QueryAsync<Tenant>(@"
            SELECT id, house_id AS HouseId, name, start_date AS StartDate, end_date AS EndDate 
            FROM tenants 
            ORDER BY (CASE WHEN end_date IS NULL OR end_date = '' OR LOWER(end_date) = 'present' THEN 1 ELSE 0 END) DESC, 
                     start_date DESC, id DESC;")).ToList();

        var docCounts = (await conn.QueryAsync<(string HouseId, string? Category, int DocCount)>(@"
            SELECT house_id AS HouseId, category AS Category, COUNT(*) AS DocCount 
            FROM documents 
            GROUP BY house_id, category;")).ToList();

        var tenantsByHouse = tenants.GroupBy(t => t.HouseId).ToDictionary(g => g.Key, g => g.ToList());
        var catCountsByHouse = new Dictionary<string, Dictionary<string, int>>();
        var totalDocsByHouse = new Dictionary<string, int>();

        foreach (var dc in docCounts)
        {
            totalDocsByHouse[dc.HouseId] = totalDocsByHouse.GetValueOrDefault(dc.HouseId) + dc.DocCount;
            if (!string.IsNullOrWhiteSpace(dc.Category))
            {
                var cleanCat = Constants.CleanCategoryName(dc.Category);
                if (!catCountsByHouse.TryGetValue(dc.HouseId, out var catDict))
                {
                    catDict = new Dictionary<string, int>();
                    catCountsByHouse[dc.HouseId] = catDict;
                }
                catDict[cleanCat] = catDict.GetValueOrDefault(cleanCat) + dc.DocCount;
            }
        }

        var currentYear = DateTime.Now.Year;
        var todayStr = DateTime.Today.ToString("yyyy-MM-dd");
        var result = new List<HouseCardDto>();

        foreach (var h in houses)
        {
            var hTenants = tenantsByHouse.GetValueOrDefault(h.Id, new List<Tenant>());

            Tenant? activeTenant = hTenants.FirstOrDefault(t =>
                string.IsNullOrEmpty(t.EndDate) ||
                t.EndDate.ToLowerInvariant() == "present" ||
                string.Compare(t.EndDate, todayStr, StringComparison.Ordinal) >= 0);

            if (activeTenant == null && h.Id.Contains(" - "))
            {
                var cand = h.Id.Split(" - ", 2)[1].Trim();
                activeTenant = hTenants.FirstOrDefault(t => t.Name == cand);
            }

            if (activeTenant == null && hTenants.Count > 0)
            {
                activeTenant = hTenants[0];
            }

            int? tenureDuration = null;
            string? durationCategory = null;
            string? tenureColor = null;
            string? subtitle = null;
            string? activeTenantName = null;

            if (activeTenant != null)
            {
                activeTenantName = activeTenant.Name;
                var mYear = Regex.Match(activeTenant.StartDate, @"(\d{4})");
                if (mYear.Success)
                {
                    var startYear = int.Parse(mYear.Groups[1].Value);
                    var duration = Math.Max(currentYear - startYear, 0);
                    tenureDuration = duration;

                    if (duration < 5)
                    {
                        durationCategory = "short";
                        tenureColor = "green";
                    }
                    else if (duration < 10)
                    {
                        durationCategory = "medium";
                        tenureColor = "yellow";
                    }
                    else
                    {
                        durationCategory = "long";
                        tenureColor = "red";
                    }

                    subtitle = $"Since {startYear} ({duration}y)";
                }
            }
            else if (hTenants.Count > 0)
            {
                var latest = hTenants[0];
                var sStr = latest.StartDate.Length >= 4 ? latest.StartDate[..4] : "";
                var eStr = (!string.IsNullOrEmpty(latest.EndDate) && latest.EndDate.Length >= 4) ? latest.EndDate[..4] : "";
                if (!string.IsNullOrEmpty(sStr) && !string.IsNullOrEmpty(eStr) && sStr != eStr)
                    subtitle = $"{sStr} - {eStr}";
                else if (!string.IsNullOrEmpty(sStr))
                    subtitle = sStr;
            }

            result.Add(new HouseCardDto
            {
                Id = h.Id,
                Name = h.Id,
                AreaId = h.AreaId,
                CurrentTenant = activeTenantName,
                TenureDurationYears = tenureDuration,
                DurationCategory = durationCategory,
                TenureColor = tenureColor,
                Subtitle = subtitle,
                TotalDocuments = totalDocsByHouse.GetValueOrDefault(h.Id, 0),
                CategoryCounts = catCountsByHouse.GetValueOrDefault(h.Id, new Dictionary<string, int>())
            });
        }

        return result;
    }

    public async Task<HouseProfileDto?> GetHouseProfileAsync(string areaId, string houseId)
    {
        await using var conn = await _connectionFactory.CreateConnectionAsync();

        var cleanHouseId = TextUtils.ExtractHouseNumber(houseId);

        var houseRow = await conn.QueryFirstOrDefaultAsync<House>(@"
            SELECT id, area_id AS AreaId 
            FROM houses 
            WHERE id = @HouseId OR id = @CleanHouseId;",
            new { HouseId = houseId, CleanHouseId = cleanHouseId });

        if (houseRow == null)
            return null;

        var dbHouseId = houseRow.Id;

        var tenants = (await conn.QueryAsync<Tenant>(@"
            SELECT id, house_id AS HouseId, name, start_date AS StartDate, end_date AS EndDate 
            FROM tenants 
            WHERE house_id = @DbHouseId
            ORDER BY start_date ASC, id ASC;",
            new { DbHouseId = dbHouseId })).ToList();

        var docs = (await conn.QueryAsync<Document>(@"
            SELECT vault_id AS VaultId, house_id AS HouseId, tenant_id AS TenantId, batch_id AS BatchId,
                   primary_date AS PrimaryDate, arabic_title AS ArabicTitle, category AS Category,
                   page_count AS PageCount, is_manual AS IsManual, notes AS Notes
            FROM documents 
            WHERE house_id = @DbHouseId;",
            new { DbHouseId = dbHouseId })).ToList();

        var batches = (await conn.QueryAsync<Batch>(@"
            SELECT id, page_count AS PageCount 
            FROM batches 
            WHERE house_id = @DbHouseId;",
            new { DbHouseId = dbHouseId })).ToList();

        var tenantDocCounts = new Dictionary<int, int>();
        var tenantCatSets = new Dictionary<int, HashSet<string>>();

        foreach (var d in docs)
        {
            tenantDocCounts[d.TenantId] = tenantDocCounts.GetValueOrDefault(d.TenantId) + 1;
            if (!tenantCatSets.TryGetValue(d.TenantId, out var cSet))
            {
                cSet = new HashSet<string>();
                tenantCatSets[d.TenantId] = cSet;
            }
            if (!string.IsNullOrEmpty(d.Category))
            {
                cSet.Add(d.Category);
            }
        }

        var tenantProfiles = new List<HouseTenantProfileDto>();
        Tenant? activeTenant = null;

        foreach (var t in tenants)
        {
            var isActive = string.IsNullOrEmpty(t.EndDate) ||
                           t.EndDate.ToLowerInvariant() == "present" ||
                           string.Compare(t.EndDate, DateTime.Today.ToString("yyyy-MM-dd"), StringComparison.Ordinal) >= 0;

            if (isActive && activeTenant == null)
            {
                activeTenant = t;
            }

            var (_, durStr) = TextUtils.FormatArabicDuration(t.StartDate, t.EndDate);

            tenantProfiles.Add(new HouseTenantProfileDto
            {
                Id = t.Id,
                Name = t.Name,
                StartDate = t.StartDate,
                EndDate = t.EndDate,
                IsActive = isActive,
                DurationStrAr = durStr,
                DocumentCount = tenantDocCounts.GetValueOrDefault(t.Id, 0),
                CategoryCount = tenantCatSets.TryGetValue(t.Id, out var set) ? set.Count : 0
            });
        }

        // Active first, then by start date descending
        tenantProfiles.Sort((a, b) =>
        {
            if (a.IsActive != b.IsActive) return b.IsActive.CompareTo(a.IsActive);
            return string.Compare(b.StartDate, a.StartDate, StringComparison.Ordinal);
        });

        var validDates = docs
            .Select(d => d.PrimaryDate)
            .Where(p => !string.IsNullOrEmpty(p) && !p.Equals("NONE", StringComparison.OrdinalIgnoreCase))
            .ToList();

        string? oldestDate = validDates.Count > 0 ? validDates.Min() : null;
        string? newestDate = validDates.Count > 0 ? validDates.Max() : null;
        var (tsYears, tsStr) = TextUtils.FormatArabicTimespan(oldestDate, newestDate);

        var catCounts = new Dictionary<string, int>();
        int totalPages = 0;
        foreach (var d in docs)
        {
            var catFormatted = Constants.FormatCategoryWithPrefix(d.Category);
            catCounts[catFormatted] = catCounts.GetValueOrDefault(catFormatted) + 1;
            totalPages += (d.PageCount > 0 ? d.PageCount : 1);
        }

        var catItems = catCounts
            .OrderByDescending(kv => kv.Value)
            .Select(kv => new CategoryBreakdownItemDto
            {
                Category = kv.Key,
                DocumentCount = kv.Value
            })
            .ToList();

        var archive = new HouseArchiveProfileDto
        {
            TotalDocuments = docs.Count,
            TotalPages = totalPages > 0 ? totalPages : batches.Sum(b => b.PageCount),
            BatchCount = batches.Count,
            OldestDate = oldestDate,
            NewestDate = newestDate,
            TimespanYears = tsYears,
            TimespanStrAr = tsStr,
            Categories = catItems
        };

        return new HouseProfileDto
        {
            HouseId = dbHouseId,
            AreaId = areaId,
            ActiveResident = activeTenant?.Name ?? tenantProfiles.FirstOrDefault()?.Name,
            Tenants = tenantProfiles,
            Archive = archive
        };
    }

    public async Task<IReadOnlyList<TimelineItemDto>> GetTimelineAsync(string areaId, string houseId, string? tenantName = null)
    {
        await using var conn = await _connectionFactory.CreateConnectionAsync();
        var cleanHouseId = TextUtils.ExtractHouseNumber(houseId);

        const string sql = @"
            SELECT d.vault_id AS VaultId,
                   COALESCE(t.name, '') AS PrimaryTenant,
                   d.tenant_id AS TenantId,
                   d.primary_date AS PrimaryDate,
                   COALESCE(d.arabic_title, '') AS BriefArabicTitle,
                   COALESCE(d.category, '') AS Category,
                   COALESCE(d.is_manual, 0) AS IsManual,
                   COALESCE(d.is_timeline_visible, 1) AS IsTimelineVisible,
                   d.notes AS Notes
            FROM documents d
            LEFT JOIN tenants t ON d.tenant_id = t.id
            WHERE (d.house_id = @HouseId OR d.house_id = @CleanHouseId)
              AND (d.is_timeline_visible IS NULL OR d.is_timeline_visible = 1)
              AND (@TenantName IS NULL OR t.name = @TenantName)
            ORDER BY d.primary_date DESC, d.created_at DESC;";

        var rows = await conn.QueryAsync<(
            string VaultId,
            string PrimaryTenant,
            int? TenantId,
            string? PrimaryDate,
            string BriefArabicTitle,
            string? Category,
            int IsManual,
            int IsTimelineVisible,
            string? Notes
        )>(sql, new { HouseId = houseId, CleanHouseId = cleanHouseId, TenantName = tenantName });

        return rows.Select(r => new TimelineItemDto
        {
            VaultId = r.VaultId,
            PrimaryTenant = r.PrimaryTenant,
            TenantId = r.TenantId,
            Dates = string.IsNullOrEmpty(r.PrimaryDate) ? new List<string>() : new List<string> { r.PrimaryDate },
            BriefArabicTitle = r.BriefArabicTitle,
            Category = r.Category,
            IsManual = r.IsManual,
            IsTimelineVisible = r.IsTimelineVisible,
            Notes = r.Notes
        }).ToList();
    }

    public async Task<IReadOnlyList<CategoryFolderDto>> GetCategoriesAsync(string areaId, string houseId)
    {
        await using var conn = await _connectionFactory.CreateConnectionAsync();
        var cleanHouseId = TextUtils.ExtractHouseNumber(houseId);

        const string sql = @"
            SELECT d.vault_id AS VaultId,
                   d.primary_date AS PrimaryDate,
                   d.arabic_title AS ArabicTitle,
                   d.category AS Category,
                   d.page_count AS PageCount,
                   d.is_manual AS IsManual,
                   d.tenant_id AS TenantId,
                   d.notes AS Notes,
                   COALESCE(t.name, '') AS TenantName,
                   COALESCE(b.filename, 'doc_' || d.vault_id || '.pdf') AS BatchFilename
            FROM documents d
            LEFT JOIN tenants t ON d.tenant_id = t.id
            LEFT JOIN batches b ON d.batch_id = b.id
            WHERE d.house_id = @HouseId OR d.house_id = @CleanHouseId
            ORDER BY d.category ASC, d.primary_date DESC;";

        var rows = (await conn.QueryAsync<(
            string VaultId,
            string? PrimaryDate,
            string? ArabicTitle,
            string? Category,
            int PageCount,
            int IsManual,
            int? TenantId,
            string? Notes,
            string TenantName,
            string BatchFilename
        )>(sql, new { HouseId = houseId, CleanHouseId = cleanHouseId })).ToList();

        var categories = new Dictionary<(string Tenant, string Category), List<VaultFileDto>>();

        foreach (var r in rows)
        {
            var formattedCat = Constants.FormatCategoryWithPrefix(r.Category);
            var key = (r.TenantName, formattedCat);

            if (!categories.TryGetValue(key, out var list))
            {
                list = new List<VaultFileDto>();
                categories[key] = list;
            }

            list.Add(new VaultFileDto
            {
                VaultId = r.VaultId,
                Filename = r.BatchFilename,
                StartPage = 1,
                EndPage = r.PageCount > 0 ? r.PageCount : 1,
                Date = r.PrimaryDate ?? string.Empty,
                Tenant = r.TenantName,
                TenantId = r.TenantId,
                Category = formattedCat,
                BriefArabicTitle = r.ArabicTitle,
                IsManual = r.IsManual,
                Notes = r.Notes
            });
        }

        return categories.Select(kv => new CategoryFolderDto
        {
            Tenant = kv.Key.Tenant,
            Name = kv.Key.Category,
            DocumentCount = kv.Value.Count,
            Documents = kv.Value
        }).OrderBy(c => c.Tenant).ThenBy(c => c.Name).ToList();
    }

    public async Task<IReadOnlyList<TenantDto>> GetTenantsAsync(string houseId)
    {
        await using var conn = await _connectionFactory.CreateConnectionAsync();
        var cleanHouseId = TextUtils.ExtractHouseNumber(houseId);

        const string sql = @"
            SELECT id AS Id, name AS Name, start_date AS StartDate, end_date AS EndDate, house_id AS HouseId
            FROM tenants
            WHERE house_id = @HouseId OR house_id = @CleanHouseId
            ORDER BY (CASE WHEN end_date IS NULL OR end_date = '' OR LOWER(end_date) = 'present' THEN 1 ELSE 0 END) DESC, 
                     start_date DESC, id DESC;";

        var rows = (await conn.QueryAsync<TenantDto>(sql, new { HouseId = houseId, CleanHouseId = cleanHouseId })).ToList();

        // Deduplicate by tenant name (preserve active / latest)
        var seenNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var deduped = new List<TenantDto>();
        foreach (var t in rows)
        {
            if (seenNames.Add(t.Name.Trim()))
            {
                deduped.Add(t);
            }
        }

        return deduped;
    }

    public async Task<IReadOnlyList<SearchResultDto>> SearchAsync(string query, int limit = 50)
    {
        if (string.IsNullOrWhiteSpace(query))
            return Array.Empty<SearchResultDto>();

        var q = query.Trim().ToLowerInvariant();
        var likeQ = $"%{q}%";
        await using var conn = await _connectionFactory.CreateConnectionAsync();

        var results = new List<SearchResultDto>();

        // 1. Houses matching q
        const string sqlHouses = @"
            SELECT h.id AS Id, h.area_id AS AreaId,
                   (SELECT COUNT(*) FROM documents WHERE house_id = h.id) AS DocCount,
                   (SELECT name FROM tenants WHERE house_id = h.id AND (end_date IS NULL OR end_date = '' OR LOWER(end_date) = 'present') ORDER BY start_date DESC LIMIT 1) AS CurrentTenant
            FROM houses h
            WHERE LOWER(h.id) LIKE @LikeQ OR LOWER(h.area_id) LIKE @LikeQ
            ORDER BY h.id;";

        var houseRows = await conn.QueryAsync<(string Id, string AreaId, int DocCount, string? CurrentTenant)>(sqlHouses, new { LikeQ = likeQ });
        foreach (var hr in houseRows)
        {
            var subParts = new List<string> { hr.AreaId };
            if (!string.IsNullOrEmpty(hr.CurrentTenant))
                subParts.Add(hr.CurrentTenant);
            subParts.Add($"{hr.DocCount} Documents");

            results.Add(new SearchResultDto
            {
                Id = hr.Id,
                Type = "house",
                Title = $"House {hr.Id}",
                Subtitle = string.Join(" • ", subParts),
                Url = $"/#/area/{hr.AreaId}/house/{hr.Id}",
                AreaId = hr.AreaId,
                HouseId = hr.Id,
                TenantName = hr.CurrentTenant,
                ExtraInfo = $"{hr.DocCount} Docs"
            });
        }

        // 2. Tenants matching q
        const string sqlTenants = @"
            SELECT t.id AS Id, t.name AS Name, t.start_date AS StartDate, t.end_date AS EndDate, t.house_id AS HouseId, h.area_id AS AreaId
            FROM tenants t
            JOIN houses h ON t.house_id = h.id
            ORDER BY t.start_date DESC;";

        var tenantRows = await conn.QueryAsync<(int Id, string Name, string StartDate, string? EndDate, string HouseId, string AreaId)>(sqlTenants);
        var qPhonetic = TextUtils.PhoneticNormalize(q);

        foreach (var t in tenantRows)
        {
            var tLower = t.Name.ToLowerInvariant();
            var tPhonetic = TextUtils.PhoneticNormalize(tLower);
            var isMatch = false;

            if (tLower.Contains(q) || t.HouseId.ToLowerInvariant().Contains(q))
            {
                isMatch = true;
            }
            else if (!string.IsNullOrEmpty(qPhonetic) && tPhonetic.Replace(" ", "").Contains(qPhonetic.Replace(" ", "")))
            {
                isMatch = true;
            }
            else if (TextUtils.Similarity(tLower, q) >= 0.7 ||
                     (!string.IsNullOrEmpty(qPhonetic) && TextUtils.Similarity(tPhonetic, qPhonetic) >= 0.7))
            {
                isMatch = true;
            }

            if (isMatch)
            {
                var sYr = t.StartDate.Length >= 4 ? t.StartDate[..4] : "";
                var eYr = (string.IsNullOrEmpty(t.EndDate) || t.EndDate.ToLowerInvariant() == "present") ? "Present" : (t.EndDate.Length >= 4 ? t.EndDate[..4] : "");
                var tenureStr = !string.IsNullOrEmpty(sYr) ? $"{sYr} - {eYr}" : "";
                var subLabel = !string.IsNullOrEmpty(tenureStr)
                    ? $"House {t.HouseId} ({tenureStr}) • {t.AreaId}"
                    : $"House {t.HouseId} • {t.AreaId}";

                results.Add(new SearchResultDto
                {
                    Id = $"{t.HouseId}_{t.Name}",
                    Type = "tenant",
                    Title = t.Name,
                    Subtitle = subLabel,
                    Url = $"/#/area/{t.AreaId}/house/{t.HouseId}",
                    AreaId = t.AreaId,
                    HouseId = t.HouseId,
                    TenantName = t.Name,
                    ExtraInfo = tenureStr
                });
            }
        }

        // 3. Documents matching q (title, category, notes, page explanation, page subject)
        const string sqlDocs = @"
            SELECT DISTINCT d.vault_id AS VaultId, d.arabic_title AS ArabicTitle, d.category AS Category,
                   d.primary_date AS PrimaryDate, d.is_manual AS IsManual, d.house_id AS HouseId,
                   h.area_id AS AreaId, t.name AS TenantName
            FROM documents d
            JOIN houses h ON d.house_id = h.id
            LEFT JOIN tenants t ON d.tenant_id = t.id
            LEFT JOIN pages p ON (p.vault_id = d.vault_id OR (p.vault_id IS NULL AND p.batch_id = d.batch_id))
            WHERE LOWER(COALESCE(d.arabic_title, '')) LIKE @LikeQ
               OR LOWER(COALESCE(d.category, '')) LIKE @LikeQ
               OR LOWER(COALESCE(d.notes, '')) LIKE @LikeQ
               OR LOWER(COALESCE(p.content_explanation, '')) LIKE @LikeQ
               OR LOWER(COALESCE(p.subject, '')) LIKE @LikeQ
            ORDER BY d.primary_date DESC;";

        var docRows = await conn.QueryAsync<(
            string VaultId,
            string? ArabicTitle,
            string? Category,
            string? PrimaryDate,
            int IsManual,
            string HouseId,
            string AreaId,
            string? TenantName
        )>(sqlDocs, new { LikeQ = likeQ });

        foreach (var d in docRows)
        {
            var title = !string.IsNullOrEmpty(d.ArabicTitle) ? d.ArabicTitle : (!string.IsNullOrEmpty(d.Category) ? d.Category : "Document");
            var cat = !string.IsNullOrEmpty(d.Category) ? d.Category : "Uncategorized";
            var tName = !string.IsNullOrEmpty(d.TenantName) ? d.TenantName : "No Tenant";
            var pathStr = $"{d.AreaId} › House {d.HouseId} › {tName} › {cat}";

            results.Add(new SearchResultDto
            {
                Id = $"{d.HouseId}_doc_{d.VaultId}",
                Type = "document",
                Title = title,
                Subtitle = pathStr,
                Url = $"/#/area/{d.AreaId}/house/{d.HouseId}",
                AreaId = d.AreaId,
                HouseId = d.HouseId,
                TenantName = d.TenantName,
                Category = cat,
                Date = d.PrimaryDate,
                VaultId = d.VaultId,
                IsManual = d.IsManual
            });
        }

        // Deduplicate results by ID
        var seenIds = new HashSet<string>();
        var uniqueResults = new List<SearchResultDto>();
        foreach (var r in results)
        {
            if (seenIds.Add(r.Id))
            {
                uniqueResults.Add(r);
                if (uniqueResults.Count >= limit)
                    break;
            }
        }

        return uniqueResults;
    }

    public async Task<DocumentDetailsDto?> GetDocumentByVaultIdAsync(string vaultId, string? areasRoot = null)
    {
        await using var conn = await _connectionFactory.CreateConnectionAsync();

        const string sqlDoc = @"
            SELECT 
                d.vault_id AS VaultId,
                d.house_id AS HouseId,
                d.category AS Category,
                d.primary_date AS PrimaryDate,
                d.arabic_title AS ArabicTitle,
                d.page_count AS PageCount,
                d.is_manual AS IsManual,
                d.notes AS Notes,
                d.created_at AS CreatedAt,
                d.batch_id AS BatchId,
                t.id AS TenantId,
                t.name AS TenantName,
                t.start_date AS TenantStartDate,
                t.end_date AS TenantEndDate,
                b.filename AS BatchFilename,
                b.file_path AS BatchFilePath,
                h.area_id AS AreaId
            FROM documents d
            LEFT JOIN tenants t ON d.tenant_id = t.id
            LEFT JOIN batches b ON d.batch_id = b.id
            LEFT JOIN houses h ON d.house_id = h.id
            WHERE d.vault_id = @VaultId;";

        var doc = await conn.QueryFirstOrDefaultAsync<DocumentDetailsDto>(sqlDoc, new { VaultId = vaultId });
        if (doc == null)
            return null;

        const string sqlPages = @"
            SELECT page_number AS PageNumber, subject AS Subject, sender AS Sender, receiver AS Receiver,
                   content_explanation AS ContentExplanation, raw_date AS RawDate, fine_category AS FineCategory
            FROM pages
            WHERE vault_id = @VaultId
            ORDER BY page_number ASC;";

        var pages = (await conn.QueryAsync<PageItemDto>(sqlPages, new { VaultId = vaultId })).ToList();

        // Determine physical path on disk if areasRoot is available
        string? physicalPath = null;
        if (!string.IsNullOrEmpty(areasRoot) && !string.IsNullOrEmpty(doc.AreaId) && !string.IsNullOrEmpty(doc.HouseId))
        {
            var candidates = new[]
            {
                Path.Combine(areasRoot, doc.AreaId, doc.HouseId, "vault", $"doc_{vaultId}.pdf"),
                Path.Combine(areasRoot, doc.AreaId, doc.HouseId, "vault", $"{vaultId}.pdf")
            };

            foreach (var cand in candidates)
            {
                if (File.Exists(cand))
                {
                    physicalPath = cand;
                    break;
                }
            }

            if (physicalPath == null && !string.IsNullOrEmpty(doc.BatchFilePath))
            {
                var batchCand = Path.Combine(areasRoot, doc.AreaId, doc.HouseId, doc.BatchFilePath);
                if (File.Exists(batchCand)) physicalPath = batchCand;
                else
                {
                    var cleanH = TextUtils.ExtractHouseNumber(doc.HouseId);
                    var cleanBatchCand = Path.Combine(areasRoot, doc.AreaId, cleanH, doc.BatchFilePath);
                    if (File.Exists(cleanBatchCand)) physicalPath = cleanBatchCand;
                }
            }

            physicalPath ??= candidates[0];
        }

        return doc with
        {
            PhysicalPath = physicalPath,
            Pages = pages
        };
    }

    public async Task<IngestResponseDto> AddManualDocumentAsync(IngestRequestDto request)
    {
        await using var conn = await _connectionFactory.CreateConnectionAsync();
        await using var tx = await conn.BeginTransactionAsync();

        var cleanHouseId = TextUtils.ExtractHouseNumber(request.HouseId);
        var category = Constants.FormatCategoryWithPrefix(request.Category);
        var vaultId = !string.IsNullOrEmpty(request.VaultId) ? request.VaultId : Guid.NewGuid().ToString("N");
        var filename = !string.IsNullOrEmpty(request.SourcePdfFilename)
            ? request.SourcePdfFilename
            : $"manual_{DateTime.UtcNow:yyyyMMddHHmmss}.pdf";

        // 1. Ensure Area and House exist in DB
        await conn.ExecuteAsync("INSERT OR IGNORE INTO areas (id) VALUES (@AreaId);",
            new { AreaId = request.AreaId }, tx);
        await conn.ExecuteAsync("INSERT OR IGNORE INTO houses (id, area_id) VALUES (@HouseId, @AreaId);",
            new { HouseId = cleanHouseId, AreaId = request.AreaId }, tx);

        // 2. Validate tenant
        var tenant = await conn.QueryFirstOrDefaultAsync<Tenant>(
            "SELECT id, house_id AS HouseId, name FROM tenants WHERE id = @TenantId;",
            new { TenantId = request.TenantId }, tx);

        if (tenant == null)
            throw new ArgumentException($"Tenant with ID {request.TenantId} does not exist.");

        if (tenant.HouseId != cleanHouseId && tenant.HouseId != request.HouseId)
            throw new ArgumentException($"Tenant {request.TenantId} belongs to house '{tenant.HouseId}', not '{cleanHouseId}'.");

        // 3. Create batch record
        var batchInsertSql = @"
            INSERT INTO batches (house_id, filename, file_path, page_count, status)
            VALUES (@HouseId, @Filename, @FilePath, @PageCount, 'completed');
            SELECT last_insert_rowid();";

        var batchId = await conn.ExecuteScalarAsync<int>(batchInsertSql, new
        {
            HouseId = cleanHouseId,
            Filename = filename,
            FilePath = $"batches/{filename}",
            PageCount = request.PageCount
        }, tx);

        var targetBatchFilename = $"batch_{batchId}_{filename}";
        var targetBatchRel = $"batches/{targetBatchFilename}";
        await conn.ExecuteAsync("UPDATE batches SET filename = @Filename, file_path = @FilePath WHERE id = @BatchId;",
            new { Filename = targetBatchFilename, FilePath = targetBatchRel, BatchId = batchId }, tx);

        // 4. Physical file copy if source file provided
        if (!string.IsNullOrEmpty(request.SourcePdfPath) && File.Exists(request.SourcePdfPath))
        {
            var areasRoot = request.AreasRoot ?? "areas";
            var houseDir = Path.Combine(areasRoot, request.AreaId, cleanHouseId);
            var batchesDir = Path.Combine(houseDir, "batches");
            var vaultDir = Path.Combine(houseDir, "vault");

            Directory.CreateDirectory(batchesDir);
            Directory.CreateDirectory(vaultDir);

            var targetBatchPath = Path.Combine(batchesDir, targetBatchFilename);
            var targetVaultPath = Path.Combine(vaultDir, $"doc_{vaultId}.pdf");

            try
            {
                File.Copy(request.SourcePdfPath, targetBatchPath, overwrite: true);
                File.Copy(request.SourcePdfPath, targetVaultPath, overwrite: true);
            }
            catch (Exception)
            {
                // In non-filesystem / in-memory environments, ignore file copy error
            }
        }

        // 5. Insert document with is_manual = 1
        const string docInsertSql = @"
            INSERT INTO documents (
                vault_id, house_id, tenant_id, batch_id, primary_date,
                arabic_title, category, page_count, is_manual, notes
            ) VALUES (
                @VaultId, @HouseId, @TenantId, @BatchId, @PrimaryDate,
                @ArabicTitle, @Category, @PageCount, 1, @Notes
            );";

        await conn.ExecuteAsync(docInsertSql, new
        {
            VaultId = vaultId,
            HouseId = cleanHouseId,
            TenantId = request.TenantId,
            BatchId = batchId,
            PrimaryDate = request.PrimaryDate,
            ArabicTitle = request.ArabicTitle,
            Category = category,
            PageCount = request.PageCount,
            Notes = request.Notes
        }, tx);

        // 6. Relational page inheritance for all pages 1..N
        const string pageInsertSql = @"
            INSERT INTO pages (
                batch_id, page_number, house_id, category, content_explanation,
                subject, is_continuation, tenant_id, resolved_date,
                fine_category, fine_category_reason, vault_id
            ) VALUES (
                @BatchId, @PageNumber, @HouseId, @Category, @ContentExplanation,
                @Subject, @IsContinuation, @TenantId, @ResolvedDate,
                @FineCategory, 'Manually verified by user', @VaultId
            );";

        for (int pNum = 1; pNum <= request.PageCount; pNum++)
        {
            await conn.ExecuteAsync(pageInsertSql, new
            {
                BatchId = batchId,
                PageNumber = pNum,
                HouseId = cleanHouseId,
                Category = category,
                ContentExplanation = $"Page {pNum} of {request.ArabicTitle}",
                Subject = (pNum == 1) ? request.ArabicTitle : null,
                IsContinuation = pNum > 1,
                TenantId = request.TenantId,
                ResolvedDate = request.PrimaryDate,
                FineCategory = category,
                VaultId = vaultId
            }, tx);
        }

        await tx.CommitAsync();

        return new IngestResponseDto
        {
            Status = "success",
            Mode = request.Mode ?? "manual",
            VaultId = vaultId,
            VaultIds = new List<string> { vaultId },
            BatchId = batchId,
            PageCount = request.PageCount,
            DocumentsCreated = 1,
            HouseId = cleanHouseId,
            AreaId = request.AreaId,
            Message = $"Document '{request.ArabicTitle}' manually ingested into house '{cleanHouseId}'.",
            IsManual = 1
        };
    }

    public async Task<DocumentActionResponseDto?> UpdateDocumentAsync(
        string vaultId,
        string? arabicTitle = null,
        string? category = null,
        int? tenantId = null,
        string? primaryDate = null,
        int? isManual = 1,
        string? notes = null)
    {
        await using var conn = await _connectionFactory.CreateConnectionAsync();
        await using var tx = await conn.BeginTransactionAsync();

        var existing = await conn.QueryFirstOrDefaultAsync<Document>(
            "SELECT vault_id AS VaultId, house_id AS HouseId, tenant_id AS TenantId, category AS Category, arabic_title AS ArabicTitle, is_manual AS IsManual FROM documents WHERE vault_id = @VaultId;",
            new { VaultId = vaultId }, tx);

        if (existing == null)
            return null;

        var updates = new List<string>();
        var parameters = new DynamicParameters();
        parameters.Add("VaultId", vaultId);

        string? resolvedCategory = null;
        if (category != null)
        {
            resolvedCategory = Constants.FormatCategoryWithPrefix(category);
            updates.Add("category = @Category");
            parameters.Add("Category", resolvedCategory);
        }

        if (arabicTitle != null)
        {
            updates.Add("arabic_title = @ArabicTitle");
            parameters.Add("ArabicTitle", arabicTitle.Trim());
        }

        if (tenantId.HasValue)
        {
            updates.Add("tenant_id = @TenantId");
            parameters.Add("TenantId", tenantId.Value);
        }

        if (primaryDate != null)
        {
            updates.Add("primary_date = @PrimaryDate");
            parameters.Add("PrimaryDate", primaryDate);
        }

        if (isManual.HasValue)
        {
            updates.Add("is_manual = @IsManual");
            parameters.Add("IsManual", isManual.Value);
        }

        if (notes != null)
        {
            updates.Add("notes = @Notes");
            parameters.Add("Notes", notes.Trim());
        }

        if (updates.Count > 0)
        {
            var updateSql = $"UPDATE documents SET {string.Join(", ", updates)} WHERE vault_id = @VaultId;";
            await conn.ExecuteAsync(updateSql, parameters, tx);
        }

        // Keep pages in sync
        if (tenantId.HasValue)
        {
            await conn.ExecuteAsync("UPDATE pages SET tenant_id = @TenantId WHERE vault_id = @VaultId;",
                new { TenantId = tenantId.Value, VaultId = vaultId }, tx);
        }

        if (resolvedCategory != null)
        {
            await conn.ExecuteAsync("UPDATE pages SET fine_category = @Category WHERE vault_id = @VaultId;",
                new { Category = resolvedCategory, VaultId = vaultId }, tx);
        }

        // Fetch updated tenant name
        var updatedTenantId = tenantId ?? existing.TenantId;
        var tenantName = await conn.QueryFirstOrDefaultAsync<string>(
            "SELECT name FROM tenants WHERE id = @TenantId;",
            new { TenantId = updatedTenantId }, tx);

        await tx.CommitAsync();

        return new DocumentActionResponseDto
        {
            Status = "success",
            VaultId = vaultId,
            ArabicTitle = arabicTitle?.Trim() ?? existing.ArabicTitle,
            Category = resolvedCategory ?? existing.Category,
            TenantId = updatedTenantId,
            TenantName = tenantName,
            IsManual = isManual ?? existing.IsManual
        };
    }

    public async Task<DocumentActionResponseDto?> CopyDocumentAsync(
        string vaultId,
        string? targetCategory = null,
        int? targetTenantId = null,
        string? targetTitle = null,
        string? newVaultId = null,
        string? areasRoot = null)
    {
        await using var conn = await _connectionFactory.CreateConnectionAsync();
        await using var tx = await conn.BeginTransactionAsync();

        var src = await conn.QueryFirstOrDefaultAsync<Document>(@"
            SELECT vault_id AS VaultId, house_id AS HouseId, tenant_id AS TenantId, batch_id AS BatchId,
                   primary_date AS PrimaryDate, arabic_title AS ArabicTitle, category AS Category,
                   page_count AS PageCount, is_manual AS IsManual, notes AS Notes
            FROM documents 
            WHERE vault_id = @VaultId;",
            new { VaultId = vaultId }, tx);

        if (src == null)
            return null;

        var resolvedNewVaultId = !string.IsNullOrEmpty(newVaultId) ? newVaultId : Guid.NewGuid().ToString("N");
        var resolvedCategory = targetCategory != null
            ? Constants.FormatCategoryWithPrefix(targetCategory)
            : src.Category;
        var resolvedTenantId = targetTenantId ?? src.TenantId;
        var resolvedTitle = targetTitle ?? src.ArabicTitle;

        // Physical file copy if areasRoot is available
        if (!string.IsNullOrEmpty(areasRoot))
        {
            var areaId = await conn.QueryFirstOrDefaultAsync<string>(
                "SELECT area_id FROM houses WHERE id = @HouseId;",
                new { HouseId = src.HouseId }, tx);

            if (!string.IsNullOrEmpty(areaId))
            {
                var vaultDir = Path.Combine(areasRoot, areaId, src.HouseId, "vault");
                var srcVaultFile = Path.Combine(vaultDir, $"doc_{vaultId}.pdf");
                var destVaultFile = Path.Combine(vaultDir, $"doc_{resolvedNewVaultId}.pdf");

                if (File.Exists(srcVaultFile))
                {
                    try
                    {
                        File.Copy(srcVaultFile, destVaultFile, overwrite: true);
                    }
                    catch (Exception)
                    {
                        // Ignore file copy failures in restricted environments
                    }
                }
            }
        }

        // Insert new document record with is_manual = 1 and is_timeline_visible = 0
        const string copySql = @"
            INSERT INTO documents (
                vault_id, house_id, tenant_id, batch_id, primary_date,
                arabic_title, category, page_count, is_manual, notes, is_timeline_visible
            ) VALUES (
                @VaultId, @HouseId, @TenantId, @BatchId, @PrimaryDate,
                @ArabicTitle, @Category, @PageCount, 1, @Notes, 0
            );";

        await conn.ExecuteAsync(copySql, new
        {
            VaultId = resolvedNewVaultId,
            HouseId = src.HouseId,
            TenantId = resolvedTenantId,
            BatchId = src.BatchId,
            PrimaryDate = src.PrimaryDate,
            ArabicTitle = resolvedTitle,
            Category = resolvedCategory,
            PageCount = src.PageCount,
            Notes = src.Notes
        }, tx);

        var tenantName = await conn.QueryFirstOrDefaultAsync<string>(
            "SELECT name FROM tenants WHERE id = @TenantId;",
            new { TenantId = resolvedTenantId }, tx);

        await tx.CommitAsync();

        return new DocumentActionResponseDto
        {
            Status = "success",
            VaultId = resolvedNewVaultId,
            ArabicTitle = resolvedTitle,
            Category = resolvedCategory,
            TenantId = resolvedTenantId,
            TenantName = tenantName,
            IsManual = 1
        };
    }

    public async Task<CreateHouseResponseDto> CreateHouseAsync(
        string areaId,
        string houseId,
        string? initialTenantName = null,
        string? startDate = null,
        string? areasRoot = null)
    {
        var cleanHouseId = houseId?.Trim() ?? string.Empty;
        var cleanAreaId = areaId?.Trim() ?? string.Empty;

        if (string.IsNullOrWhiteSpace(cleanHouseId))
        {
            throw new ArgumentException("House ID is required and cannot be empty.");
        }
        if (string.IsNullOrWhiteSpace(cleanAreaId))
        {
            throw new ArgumentException("Area ID is required and cannot be empty.");
        }

        await using var conn = await _connectionFactory.CreateConnectionAsync();

        // Check if house already exists
        var existingHouse = await conn.QueryFirstOrDefaultAsync<House>(
            "SELECT id AS Id, area_id AS AreaId FROM houses WHERE id = @Id;",
            new { Id = cleanHouseId });

        if (existingHouse != null)
        {
            throw new InvalidOperationException($"House '{cleanHouseId}' already exists in area '{existingHouse.AreaId}'.");
        }

        // Ensure area exists (or add if not exists)
        var existingArea = await conn.QueryFirstOrDefaultAsync<Area>(
            "SELECT id AS Id, code AS Code FROM areas WHERE id = @Id;",
            new { Id = cleanAreaId });

        if (existingArea == null)
        {
            await conn.ExecuteAsync("INSERT OR IGNORE INTO areas (id, code) VALUES (@Id, @Code);", new { Id = cleanAreaId, Code = (string?)null });
        }

        // Register house
        await conn.ExecuteAsync("INSERT INTO houses (id, area_id) VALUES (@Id, @AreaId);", new { Id = cleanHouseId, AreaId = cleanAreaId });

        // Optional initial tenant
        int? tenantId = null;
        if (!string.IsNullOrWhiteSpace(initialTenantName))
        {
            var cleanTenantName = initialTenantName.Trim();
            var sDate = !string.IsNullOrWhiteSpace(startDate) ? startDate.Trim() : DateTime.Today.ToString("yyyy-MM-dd");

            tenantId = await conn.ExecuteScalarAsync<int>(@"
                INSERT INTO tenants (house_id, name, start_date)
                VALUES (@HouseId, @Name, @StartDate);
                SELECT last_insert_rowid();",
                new { HouseId = cleanHouseId, Name = cleanTenantName, StartDate = sDate });
        }

        // Directory scaffolding
        if (!string.IsNullOrWhiteSpace(areasRoot))
        {
            var batchesDir = Path.Combine(areasRoot, cleanAreaId, cleanHouseId, "batches");
            var vaultDir = Path.Combine(areasRoot, cleanAreaId, cleanHouseId, "vault");
            Directory.CreateDirectory(batchesDir);
            Directory.CreateDirectory(vaultDir);
        }

        return new CreateHouseResponseDto
        {
            Status = "success",
            AreaId = cleanAreaId,
            HouseId = cleanHouseId,
            TenantId = tenantId,
            Message = $"House '{cleanHouseId}' registered successfully in area '{cleanAreaId}'."
        };
    }

    // Seeding & testing helpers
    public async Task<Area> AddAreaAsync(string areaId, string? code = null)
    {
        await using var conn = await _connectionFactory.CreateConnectionAsync();
        await conn.ExecuteAsync("INSERT OR REPLACE INTO areas (id, code) VALUES (@Id, @Code);", new { Id = areaId, Code = code });
        return new Area { Id = areaId, Code = code };
    }

    public async Task<House> AddHouseAsync(string houseId, string areaId)
    {
        await using var conn = await _connectionFactory.CreateConnectionAsync();
        await conn.ExecuteAsync("INSERT OR REPLACE INTO houses (id, area_id) VALUES (@Id, @AreaId);", new { Id = houseId, AreaId = areaId });
        return new House { Id = houseId, AreaId = areaId };
    }

    public async Task<Tenant> AddTenantAsync(string houseId, string name, string startDate, string? endDate = null)
    {
        await using var conn = await _connectionFactory.CreateConnectionAsync();
        var id = await conn.ExecuteScalarAsync<int>(@"
            INSERT INTO tenants (house_id, name, start_date, end_date) 
            VALUES (@HouseId, @Name, @StartDate, @EndDate);
            SELECT last_insert_rowid();",
            new { HouseId = houseId, Name = name, StartDate = startDate, EndDate = endDate });

        return new Tenant
        {
            Id = id,
            HouseId = houseId,
            Name = name,
            StartDate = startDate,
            EndDate = endDate
        };
    }

    public async Task<Document?> GetDocumentRawAsync(string vaultId)
    {
        await using var conn = await _connectionFactory.CreateConnectionAsync();
        return await conn.QueryFirstOrDefaultAsync<Document>(@"
            SELECT vault_id AS VaultId, house_id AS HouseId, tenant_id AS TenantId, batch_id AS BatchId,
                   primary_date AS PrimaryDate, arabic_title AS ArabicTitle, category AS Category,
                   page_count AS PageCount, is_manual AS IsManual, notes AS Notes,
                   is_timeline_visible AS IsTimelineVisible, created_at AS CreatedAt
            FROM documents 
            WHERE vault_id = @VaultId;",
            new { VaultId = vaultId });
    }

    public async Task<IReadOnlyList<Page>> GetPagesByVaultIdAsync(string vaultId)
    {
        await using var conn = await _connectionFactory.CreateConnectionAsync();
        var pages = await conn.QueryAsync<Page>(@"
            SELECT id, batch_id AS BatchId, page_number AS PageNumber, house_id AS HouseId,
                   category, content_explanation AS ContentExplanation,
                   expected_tenant_name AS ExpectedTenantName, expected_house_number AS ExpectedHouseNumber,
                   raw_date AS RawDate, sender, receiver, subject,
                   is_continuation AS IsContinuation, tenant_id AS TenantId,
                   resolved_date AS ResolvedDate, fine_category AS FineCategory,
                   fine_category_reason AS FineCategoryReason, vault_id AS VaultId
            FROM pages
            WHERE vault_id = @VaultId
            ORDER BY page_number ASC;",
            new { VaultId = vaultId });

        return pages.ToList();
    }

    private static readonly HashSet<string> AllowedDbTables = new(StringComparer.OrdinalIgnoreCase)
    {
        "areas", "houses", "tenants", "batches", "pages", "documents"
    };

    public Task<DocumentDetailsDto?> GetDocumentDetailsAsync(string vaultId, string? areasRoot = null)
        => GetDocumentByVaultIdAsync(vaultId, areasRoot);

    public async Task<DocumentActionResponseDto?> ResetDocumentLockAsync(string vaultId)
    {
        await using var conn = await _connectionFactory.CreateConnectionAsync();
        var existing = await conn.QueryFirstOrDefaultAsync<Document>(
            "SELECT vault_id AS VaultId, house_id AS HouseId, tenant_id AS TenantId, category AS Category, arabic_title AS ArabicTitle, is_manual AS IsManual FROM documents WHERE vault_id = @VaultId;",
            new { VaultId = vaultId });

        if (existing == null)
            return null;

        await conn.ExecuteAsync("UPDATE documents SET is_manual = 0 WHERE vault_id = @VaultId;", new { VaultId = vaultId });

        var tenantName = await conn.QueryFirstOrDefaultAsync<string>(
            "SELECT name FROM tenants WHERE id = @TenantId;",
            new { TenantId = existing.TenantId });

        return new DocumentActionResponseDto
        {
            Status = "success",
            VaultId = vaultId,
            ArabicTitle = existing.ArabicTitle,
            Category = existing.Category,
            TenantId = existing.TenantId,
            TenantName = tenantName,
            IsManual = 0
        };
    }

    public async Task<DocumentActionResponseDto?> UpdateDocumentNotesAsync(string vaultId, string notes)
    {
        await using var conn = await _connectionFactory.CreateConnectionAsync();
        var existing = await conn.QueryFirstOrDefaultAsync<Document>(
            "SELECT vault_id AS VaultId, house_id AS HouseId, tenant_id AS TenantId, category AS Category, arabic_title AS ArabicTitle, is_manual AS IsManual FROM documents WHERE vault_id = @VaultId;",
            new { VaultId = vaultId });

        if (existing == null)
            return null;

        await conn.ExecuteAsync("UPDATE documents SET notes = @Notes WHERE vault_id = @VaultId;",
            new { VaultId = vaultId, Notes = notes.Trim() });

        var tenantName = await conn.QueryFirstOrDefaultAsync<string>(
            "SELECT name FROM tenants WHERE id = @TenantId;",
            new { TenantId = existing.TenantId });

        return new DocumentActionResponseDto
        {
            Status = "success",
            VaultId = vaultId,
            ArabicTitle = existing.ArabicTitle,
            Category = existing.Category,
            TenantId = existing.TenantId,
            TenantName = tenantName,
            IsManual = existing.IsManual
        };
    }

    public async Task<DocumentActionResponseDto?> UpdateDocumentTenantAsync(string vaultId, int tenantId)
    {
        return await UpdateDocumentAsync(vaultId, tenantId: tenantId, isManual: 1);
    }

    public async Task<bool> DeleteDocumentAsync(string areaId, string houseId, string vaultId, string? areasRoot = null)
    {
        var resolvedAreasRoot = !string.IsNullOrEmpty(areasRoot)
            ? areasRoot
            : (_configuration?["AREAS_ROOT_PATH"] ?? Environment.GetEnvironmentVariable("AREAS_ROOT_PATH") ?? "../areas");

        var cleanHouseId = houseId.Contains(" - ") ? houseId.Split(" - ")[0].Trim() : houseId.Trim();

        var possiblePaths = new[]
        {
            Path.Combine(resolvedAreasRoot, areaId, houseId, "vault", $"doc_{vaultId}.pdf"),
            Path.Combine(resolvedAreasRoot, areaId, cleanHouseId, "vault", $"doc_{vaultId}.pdf"),
            Path.Combine(resolvedAreasRoot, areaId, houseId, "vault", $"{vaultId}.pdf"),
            Path.Combine(resolvedAreasRoot, areaId, cleanHouseId, "vault", $"{vaultId}.pdf"),
        };

        foreach (var p in possiblePaths)
        {
            if (File.Exists(p))
            {
                try
                {
                    File.Delete(p);
                }
                catch (Exception)
                {
                    // Ignore physical file deletion error
                }
            }
        }

        await using var conn = await _connectionFactory.CreateConnectionAsync();
        await using var tx = await conn.BeginTransactionAsync();

        const string deletePagesSql = "DELETE FROM pages WHERE vault_id = @VaultId;";
        await conn.ExecuteAsync(deletePagesSql, new { VaultId = vaultId }, tx);

        const string deleteDocSql = "DELETE FROM documents WHERE vault_id = @VaultId;";
        var rows = await conn.ExecuteAsync(deleteDocSql, new { VaultId = vaultId }, tx);

        await tx.CommitAsync();

        return rows > 0;
    }

    public async Task<BatchDeleteResponseDto> BatchDeleteDocumentsAsync(
        string areaId,
        string houseId,
        IEnumerable<string> vaultIds,
        string? areasRoot = null)
    {
        var resolvedAreasRoot = !string.IsNullOrEmpty(areasRoot)
            ? areasRoot
            : (_configuration?["AREAS_ROOT_PATH"] ?? Environment.GetEnvironmentVariable("AREAS_ROOT_PATH") ?? "../areas");

        var cleanHouseId = houseId.Contains(" - ") ? houseId.Split(" - ")[0].Trim() : houseId.Trim();

        var deletedIds = new List<string>();

        await using var conn = await _connectionFactory.CreateConnectionAsync();
        await using var tx = await conn.BeginTransactionAsync();

        foreach (var vaultId in vaultIds)
        {
            var possiblePaths = new[]
            {
                Path.Combine(resolvedAreasRoot, areaId, houseId, "vault", $"doc_{vaultId}.pdf"),
                Path.Combine(resolvedAreasRoot, areaId, cleanHouseId, "vault", $"doc_{vaultId}.pdf"),
                Path.Combine(resolvedAreasRoot, areaId, houseId, "vault", $"{vaultId}.pdf"),
                Path.Combine(resolvedAreasRoot, areaId, cleanHouseId, "vault", $"{vaultId}.pdf"),
            };

            foreach (var p in possiblePaths)
            {
                if (File.Exists(p))
                {
                    try
                    {
                        File.Delete(p);
                    }
                    catch (Exception)
                    {
                        // Ignore physical file deletion error
                    }
                }
            }

            const string deletePagesSql = "DELETE FROM pages WHERE vault_id = @VaultId;";
            await conn.ExecuteAsync(deletePagesSql, new { VaultId = vaultId }, tx);

            const string deleteDocSql = "DELETE FROM documents WHERE vault_id = @VaultId;";
            var rows = await conn.ExecuteAsync(deleteDocSql, new { VaultId = vaultId }, tx);

            if (rows > 0)
            {
                deletedIds.Add(vaultId);
            }
        }

        await tx.CommitAsync();

        return new BatchDeleteResponseDto
        {
            Status = "success",
            DeletedCount = deletedIds.Count,
            VaultIds = deletedIds
        };
    }

    public async Task<BatchMoveResponseDto> BatchMoveDocumentsAsync(
        string areaId,
        string houseId,
        IEnumerable<string> vaultIds,
        string targetCategory)
    {
        var formattedCategory = Constants.FormatCategoryWithPrefix(targetCategory);

        await using var conn = await _connectionFactory.CreateConnectionAsync();
        await using var tx = await conn.BeginTransactionAsync();

        var movedIds = new List<string>();
        foreach (var vaultId in vaultIds)
        {
            var rows = await conn.ExecuteAsync(
                "UPDATE documents SET category = @Category, is_manual = 1 WHERE vault_id = @VaultId;",
                new { Category = formattedCategory, VaultId = vaultId },
                tx);

            if (rows > 0)
            {
                movedIds.Add(vaultId);
            }
        }

        await tx.CommitAsync();

        return new BatchMoveResponseDto
        {
            Status = "success",
            MovedCount = movedIds.Count,
            TargetCategory = formattedCategory,
            VaultIds = movedIds
        };
    }

    public async Task<BatchCopyResponseDto> BatchCopyDocumentsAsync(
        string areaId,
        string houseId,
        IEnumerable<string> vaultIds,
        string targetCategory,
        string? areasRoot = null)
    {
        var resolvedAreasRoot = !string.IsNullOrEmpty(areasRoot)
            ? areasRoot
            : (_configuration?["AREAS_ROOT_PATH"] ?? Environment.GetEnvironmentVariable("AREAS_ROOT_PATH") ?? "../areas");

        var cleanHouseId = houseId.Contains(" - ") ? houseId.Split(" - ")[0].Trim() : houseId.Trim();
        var formattedCategory = Constants.FormatCategoryWithPrefix(targetCategory);

        await using var conn = await _connectionFactory.CreateConnectionAsync();
        await using var tx = await conn.BeginTransactionAsync();

        var newVaultIds = new List<string>();

        foreach (var vaultId in vaultIds)
        {
            var src = await conn.QueryFirstOrDefaultAsync<Document>(@"
                SELECT vault_id AS VaultId, house_id AS HouseId, tenant_id AS TenantId, batch_id AS BatchId,
                       primary_date AS PrimaryDate, arabic_title AS ArabicTitle, category AS Category,
                       page_count AS PageCount, is_manual AS IsManual, notes AS Notes
                FROM documents 
                WHERE vault_id = @VaultId;",
                new { VaultId = vaultId }, tx);

            if (src == null)
                continue;

            var newVaultId = Guid.NewGuid().ToString("N");

            // Copy physical file if present
            var batchFilePath = await conn.QueryFirstOrDefaultAsync<string>(
                "SELECT file_path FROM batches WHERE id = @BatchId;",
                new { BatchId = src.BatchId }, tx);

            var possiblePaths = new List<string>
            {
                Path.Combine(resolvedAreasRoot, areaId, houseId, "vault", $"doc_{vaultId}.pdf"),
                Path.Combine(resolvedAreasRoot, areaId, cleanHouseId, "vault", $"doc_{vaultId}.pdf"),
                Path.Combine(resolvedAreasRoot, areaId, houseId, "vault", $"{vaultId}.pdf"),
                Path.Combine(resolvedAreasRoot, areaId, cleanHouseId, "vault", $"{vaultId}.pdf"),
            };
            if (!string.IsNullOrEmpty(batchFilePath))
            {
                possiblePaths.Add(Path.Combine(resolvedAreasRoot, areaId, src.HouseId, batchFilePath));
                possiblePaths.Add(Path.Combine(resolvedAreasRoot, areaId, cleanHouseId, batchFilePath));
            }

            var targetVaultDir = Path.Combine(resolvedAreasRoot, areaId, src.HouseId, "vault");
            if (!Directory.Exists(targetVaultDir))
            {
                var altDir = Path.Combine(resolvedAreasRoot, areaId, cleanHouseId, "vault");
                if (Directory.Exists(altDir)) targetVaultDir = altDir;
            }

            try
            {
                Directory.CreateDirectory(targetVaultDir);
                var destPath = Path.Combine(targetVaultDir, $"doc_{newVaultId}.pdf");
                foreach (var p in possiblePaths)
                {
                    if (File.Exists(p))
                    {
                        File.Copy(p, destPath, overwrite: true);
                        break;
                    }
                }
            }
            catch (Exception)
            {
                // Ignore physical file copy error
            }

            const string insertSql = @"
                INSERT INTO documents (
                    vault_id, house_id, tenant_id, batch_id, primary_date,
                    arabic_title, category, page_count, is_manual, notes, is_timeline_visible
                ) VALUES (
                    @VaultId, @HouseId, @TenantId, @BatchId, @PrimaryDate,
                    @ArabicTitle, @Category, @PageCount, 1, @Notes, 0
                );";

            var rows = await conn.ExecuteAsync(insertSql, new
            {
                VaultId = newVaultId,
                HouseId = src.HouseId,
                TenantId = src.TenantId,
                BatchId = src.BatchId,
                PrimaryDate = src.PrimaryDate,
                ArabicTitle = src.ArabicTitle,
                Category = formattedCategory,
                PageCount = src.PageCount,
                Notes = src.Notes
            }, tx);

            if (rows > 0)
            {
                newVaultIds.Add(newVaultId);
            }
        }

        await tx.CommitAsync();

        return new BatchCopyResponseDto
        {
            Status = "success",
            CopiedCount = newVaultIds.Count,
            TargetCategory = formattedCategory,
            NewVaultIds = newVaultIds
        };
    }

    public async Task<TenantReallocationResponseDto> BulkUpdateTenantsAsync(string houseId, IReadOnlyList<TenantDto> tenants, bool reallocate)
    {
        await using var conn = await _connectionFactory.CreateConnectionAsync();
        await using var tx = await conn.BeginTransactionAsync();

        var cleanHouseId = TextUtils.ExtractHouseNumber(houseId);

        var currentTenants = (await conn.QueryAsync<Tenant>(
            "SELECT id, house_id AS HouseId, name, start_date AS StartDate, end_date AS EndDate FROM tenants WHERE house_id = @HouseId OR house_id = @CleanHouseId;",
            new { HouseId = houseId, CleanHouseId = cleanHouseId }, tx)).ToList();

        if (tenants.Count > 0)
        {
            var payloadIds = tenants.Where(t => t.Id.HasValue).Select(t => t.Id!.Value).ToHashSet();

            // 1. Delete removed tenants
            foreach (var ct in currentTenants)
            {
                if (!payloadIds.Contains(ct.Id))
                {
                    await conn.ExecuteAsync("DELETE FROM tenants WHERE id = @Id;", new { Id = ct.Id }, tx);
                }
            }

            // 2. Insert or update tenants
            foreach (var t in tenants)
            {
                var sDate = !string.IsNullOrWhiteSpace(t.StartDate) ? (t.StartDate.Length >= 10 ? t.StartDate[..10] : t.StartDate) : "1970-01-01";
                string? eDate = null;
                if (!string.IsNullOrWhiteSpace(t.EndDate) && !t.EndDate.Equals("none", StringComparison.OrdinalIgnoreCase) && !t.EndDate.Equals("null", StringComparison.OrdinalIgnoreCase) && !t.EndDate.Equals("present", StringComparison.OrdinalIgnoreCase))
                {
                    eDate = t.EndDate.Length >= 10 ? t.EndDate[..10] : t.EndDate;
                }

                if (t.Id.HasValue && currentTenants.Any(ct => ct.Id == t.Id.Value))
                {
                    await conn.ExecuteAsync(
                        "UPDATE tenants SET name = @Name, start_date = @StartDate, end_date = @EndDate WHERE id = @Id;",
                        new { Name = t.Name.Trim(), StartDate = sDate, EndDate = eDate, Id = t.Id.Value }, tx);
                }
                else
                {
                    await conn.ExecuteAsync(
                        "INSERT INTO tenants (house_id, name, start_date, end_date) VALUES (@HouseId, @Name, @StartDate, @EndDate);",
                        new { HouseId = cleanHouseId, Name = t.Name.Trim(), StartDate = sDate, EndDate = eDate }, tx);
                }
            }
        }


        int reallocatedCount = 0;
        if (reallocate)
        {
            var updatedTenants = (await conn.QueryAsync<Tenant>(
                "SELECT id, house_id AS HouseId, name, start_date AS StartDate, end_date AS EndDate FROM tenants WHERE house_id = @HouseId OR house_id = @CleanHouseId ORDER BY start_date DESC;",
                new { HouseId = houseId, CleanHouseId = cleanHouseId }, tx)).ToList();

            var docs = (await conn.QueryAsync<Document>(
                "SELECT vault_id AS VaultId, tenant_id AS TenantId, primary_date AS PrimaryDate, is_manual AS IsManual FROM documents WHERE (house_id = @HouseId OR house_id = @CleanHouseId) AND (is_manual IS NULL OR is_manual = 0);",
                new { HouseId = houseId, CleanHouseId = cleanHouseId }, tx)).ToList();

            foreach (var doc in docs)
            {
                if (string.IsNullOrEmpty(doc.PrimaryDate)) continue;
                var docDate = doc.PrimaryDate.Length >= 10 ? doc.PrimaryDate[..10] : doc.PrimaryDate;

                var targetTenant = updatedTenants.FirstOrDefault(ut =>
                {
                    var start = ut.StartDate.Length >= 10 ? ut.StartDate[..10] : ut.StartDate;
                    if (string.Compare(docDate, start, StringComparison.Ordinal) < 0) return false;
                    if (string.IsNullOrEmpty(ut.EndDate) || ut.EndDate.Equals("present", StringComparison.OrdinalIgnoreCase)) return true;
                    var end = ut.EndDate.Length >= 10 ? ut.EndDate[..10] : ut.EndDate;
                    return string.Compare(docDate, end, StringComparison.Ordinal) <= 0;
                }) ?? updatedTenants.FirstOrDefault();

                if (targetTenant != null && targetTenant.Id != doc.TenantId)
                {
                    await conn.ExecuteAsync("UPDATE documents SET tenant_id = @TenantId WHERE vault_id = @VaultId;",
                        new { TenantId = targetTenant.Id, VaultId = doc.VaultId }, tx);
                    await conn.ExecuteAsync("UPDATE pages SET tenant_id = @TenantId WHERE vault_id = @VaultId;",
                        new { TenantId = targetTenant.Id, VaultId = doc.VaultId }, tx);
                    reallocatedCount++;
                }
            }
        }

        await tx.CommitAsync();

        var totalDocs = await conn.ExecuteScalarAsync<int>(
            "SELECT COUNT(*) FROM documents WHERE house_id = @HouseId OR house_id = @CleanHouseId;",
            new { HouseId = houseId, CleanHouseId = cleanHouseId });

        var totalTenants = await conn.ExecuteScalarAsync<int>(
            "SELECT COUNT(*) FROM tenants WHERE house_id = @HouseId OR house_id = @CleanHouseId;",
            new { HouseId = houseId, CleanHouseId = cleanHouseId });

        return new TenantReallocationResponseDto
        {
            Status = "success",
            ReallocatedCount = reallocatedCount,
            TotalDocuments = totalDocs,
            TenantsCount = totalTenants
        };
    }

    public async Task<int> DeleteCategoryAsync(string houseId, string categoryName)
    {
        await using var conn = await _connectionFactory.CreateConnectionAsync();
        var cleanHouseId = TextUtils.ExtractHouseNumber(houseId);
        const string defaultTarget = "13 - رسائل متنوعة";
        var cleanName = categoryName.Trim();

        return await conn.ExecuteAsync(@"
            UPDATE documents
            SET category = @DefaultTarget
            WHERE (house_id = @HouseId OR house_id = @CleanHouseId)
              AND (category = @CleanName OR category LIKE @Pattern);",
            new
            {
                DefaultTarget = defaultTarget,
                HouseId = houseId,
                CleanHouseId = cleanHouseId,
                CleanName = cleanName,
                Pattern = $"%{cleanName}%"
            });
    }

    public async Task<DbInfoResponseDto> GetDbStatsAsync()
    {
        await using var conn = await _connectionFactory.CreateConnectionAsync();
        var tables = new[] { "areas", "houses", "tenants", "batches", "pages", "documents" };
        var tableCounts = new Dictionary<string, int>();

        foreach (var tbl in tables)
        {
            try
            {
                var count = await conn.ExecuteScalarAsync<int>($"SELECT COUNT(*) FROM {tbl};");
                tableCounts[tbl] = count;
            }
            catch
            {
                tableCounts[tbl] = 0;
            }
        }

        return new DbInfoResponseDto
        {
            Connected = true,
            DbPath = _connectionFactory.DatabasePath,
            Tables = tableCounts
        };
    }

    public async Task<DbTableResponseDto> GetDbTableDataAsync(string tableName, int limit = 50, int offset = 0, string? search = null)
    {
        if (!AllowedDbTables.Contains(tableName))
            throw new ArgumentException($"Invalid table '{tableName}'. Allowed tables: {string.Join(", ", AllowedDbTables)}");

        await using var conn = await _connectionFactory.CreateConnectionAsync();

        // Get columns
        var colRows = (await conn.QueryAsync<(int Cid, string Name, string Type)>($"PRAGMA table_info({tableName});")).ToList();
        var columns = colRows.Select(c => c.Name).ToList();

        var whereClause = "";
        var parameters = new DynamicParameters();

        if (!string.IsNullOrWhiteSpace(search))
        {
            var searchConditions = columns.Select(c => $"CAST({c} AS TEXT) LIKE @Search");
            whereClause = $" WHERE {string.Join(" OR ", searchConditions)}";
            parameters.Add("Search", $"%{search.Trim()}%");
        }

        var countSql = $"SELECT COUNT(*) FROM {tableName}{whereClause};";
        var total = await conn.ExecuteScalarAsync<int>(countSql, parameters);

        var dataSql = $"SELECT * FROM {tableName}{whereClause} LIMIT @Limit OFFSET @Offset;";
        parameters.Add("Limit", limit);
        parameters.Add("Offset", offset);

        var rowsRaw = (await conn.QueryAsync(dataSql, parameters)).ToList();
        var rows = new List<Dictionary<string, object?>>();

        foreach (var r in rowsRaw)
        {
            var dict = new Dictionary<string, object?>();
            var rowDict = (IDictionary<string, object>)r;
            foreach (var col in columns)
            {
                dict[col] = rowDict.TryGetValue(col, out var val) ? val : null;
            }
            rows.Add(dict);
        }

        return new DbTableResponseDto
        {
            Table = tableName,
            Columns = columns,
            Total = total,
            Limit = limit,
            Offset = offset,
            Rows = rows
        };
    }
}
