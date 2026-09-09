using System.Text.Json.Serialization;

namespace FileOrganizer.Web.Models;

public record TreeAreaDto
{
    [JsonPropertyName("id")]
    public string Id { get; init; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; init; } = string.Empty;

    [JsonPropertyName("type")]
    public string Type { get; init; } = "area";

    [JsonPropertyName("subtitle")]
    public string? Subtitle { get; init; }

    [JsonPropertyName("duration_category")]
    public string? DurationCategory { get; init; }

    [JsonPropertyName("current_tenant")]
    public string? CurrentTenant { get; init; }

    [JsonPropertyName("total_documents")]
    public int TotalDocuments { get; init; }

    [JsonPropertyName("category_counts")]
    public Dictionary<string, int>? CategoryCounts { get; init; }

    [JsonPropertyName("children")]
    public List<TreeHouseDto>? Children { get; init; }
}

public record TreeHouseDto
{
    [JsonPropertyName("id")]
    public string Id { get; init; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; init; } = string.Empty;

    [JsonPropertyName("type")]
    public string Type { get; init; } = "house";

    [JsonPropertyName("subtitle")]
    public string? Subtitle { get; init; }

    [JsonPropertyName("duration_category")]
    public string? DurationCategory { get; init; } // "short", "medium", "long"

    [JsonPropertyName("current_tenant")]
    public string? CurrentTenant { get; init; }

    [JsonPropertyName("total_documents")]
    public int TotalDocuments { get; init; }

    [JsonPropertyName("category_counts")]
    public Dictionary<string, int>? CategoryCounts { get; init; }

    [JsonPropertyName("children")]
    public List<TreeTenantDto>? Children { get; init; }
}

public record TreeTenantDto
{
    [JsonPropertyName("id")]
    public string Id { get; init; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; init; } = string.Empty;

    [JsonPropertyName("type")]
    public string Type { get; init; } = "tenant";

    [JsonPropertyName("subtitle")]
    public string? Subtitle { get; init; }

    [JsonPropertyName("duration_category")]
    public string? DurationCategory { get; init; }
}

public record HouseCardDto
{
    [JsonPropertyName("id")]
    public string Id { get; init; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; init; } = string.Empty;

    [JsonPropertyName("area_id")]
    public string AreaId { get; init; } = string.Empty;

    [JsonPropertyName("current_tenant")]
    public string? CurrentTenant { get; init; }

    [JsonPropertyName("tenure_duration_years")]
    public int? TenureDurationYears { get; init; }

    [JsonPropertyName("duration_category")]
    public string? DurationCategory { get; init; } // "short", "medium", "long"

    [JsonPropertyName("tenure_color")]
    public string? TenureColor { get; init; } // "green", "yellow", "red"

    [JsonPropertyName("subtitle")]
    public string? Subtitle { get; init; }

    [JsonPropertyName("total_documents")]
    public int TotalDocuments { get; init; }

    [JsonPropertyName("category_counts")]
    public Dictionary<string, int>? CategoryCounts { get; init; }
}

public record HouseProfileDto
{
    [JsonPropertyName("house_id")]
    public string HouseId { get; init; } = string.Empty;

    [JsonPropertyName("area_id")]
    public string AreaId { get; init; } = string.Empty;

    [JsonPropertyName("active_resident")]
    public string? ActiveResident { get; init; }

    [JsonPropertyName("tenants")]
    public List<HouseTenantProfileDto> Tenants { get; init; } = new();

    [JsonPropertyName("archive")]
    public HouseArchiveProfileDto Archive { get; init; } = new();
}

public record HouseTenantProfileDto
{
    [JsonPropertyName("id")]
    public int Id { get; init; }

    [JsonPropertyName("name")]
    public string Name { get; init; } = string.Empty;

    [JsonPropertyName("start_date")]
    public string StartDate { get; init; } = string.Empty;

    [JsonPropertyName("end_date")]
    public string? EndDate { get; init; }

    [JsonPropertyName("is_active")]
    public bool IsActive { get; init; }

    [JsonPropertyName("duration_str_ar")]
    public string DurationStrAr { get; init; } = string.Empty;

    [JsonPropertyName("document_count")]
    public int DocumentCount { get; init; }

    [JsonPropertyName("category_count")]
    public int CategoryCount { get; init; }
}

public record CategoryBreakdownItemDto
{
    [JsonPropertyName("category")]
    public string Category { get; init; } = string.Empty;

    [JsonPropertyName("document_count")]
    public int DocumentCount { get; init; }
}

public record HouseArchiveProfileDto
{
    [JsonPropertyName("total_documents")]
    public int TotalDocuments { get; init; }

    [JsonPropertyName("total_pages")]
    public int TotalPages { get; init; }

    [JsonPropertyName("batch_count")]
    public int BatchCount { get; init; }

    [JsonPropertyName("oldest_date")]
    public string? OldestDate { get; init; }

    [JsonPropertyName("newest_date")]
    public string? NewestDate { get; init; }

    [JsonPropertyName("timespan_years")]
    public int TimespanYears { get; init; }

    [JsonPropertyName("timespan_str_ar")]
    public string TimespanStrAr { get; init; } = string.Empty;

    [JsonPropertyName("categories")]
    public List<CategoryBreakdownItemDto> Categories { get; init; } = new();
}

public record TimelineItemDto
{
    [JsonPropertyName("vault_id")]
    public string VaultId { get; init; } = string.Empty;

    [JsonPropertyName("primary_tenant")]
    public string PrimaryTenant { get; init; } = string.Empty;

    [JsonPropertyName("tenant_id")]
    public int? TenantId { get; init; }

    [JsonPropertyName("dates")]
    public List<string> Dates { get; init; } = new();

    [JsonPropertyName("brief_arabic_title")]
    public string BriefArabicTitle { get; init; } = string.Empty;

    [JsonPropertyName("category")]
    public string? Category { get; init; }

    [JsonPropertyName("is_manual")]
    public int IsManual { get; init; }

    [JsonPropertyName("notes")]
    public string? Notes { get; init; }
}

public record CategoryFolderDto
{
    [JsonPropertyName("tenant")]
    public string Tenant { get; init; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; init; } = string.Empty;

    [JsonPropertyName("document_count")]
    public int DocumentCount { get; init; }

    [JsonPropertyName("documents")]
    public List<VaultFileDto> Documents { get; init; } = new();
}

public record VaultFileDto
{
    [JsonPropertyName("vault_id")]
    public string VaultId { get; init; } = string.Empty;

    [JsonPropertyName("filename")]
    public string Filename { get; init; } = string.Empty;

    [JsonPropertyName("start_page")]
    public int StartPage { get; init; } = 1;

    [JsonPropertyName("end_page")]
    public int EndPage { get; init; } = 1;

    [JsonPropertyName("date")]
    public string Date { get; init; } = string.Empty;

    [JsonPropertyName("tenant")]
    public string Tenant { get; init; } = string.Empty;

    [JsonPropertyName("tenant_id")]
    public int? TenantId { get; init; }

    [JsonPropertyName("category")]
    public string? Category { get; init; }

    [JsonPropertyName("brief_arabic_title")]
    public string? BriefArabicTitle { get; init; }

    [JsonPropertyName("is_manual")]
    public int IsManual { get; init; }

    [JsonPropertyName("notes")]
    public string? Notes { get; init; }
}

public record SearchResultDto
{
    [JsonPropertyName("id")]
    public string Id { get; init; } = string.Empty;

    [JsonPropertyName("type")]
    public string Type { get; init; } = string.Empty; // "house", "tenant", "document"

    [JsonPropertyName("title")]
    public string Title { get; init; } = string.Empty;

    [JsonPropertyName("subtitle")]
    public string? Subtitle { get; init; }

    [JsonPropertyName("url")]
    public string Url { get; init; } = string.Empty;

    [JsonPropertyName("area_id")]
    public string? AreaId { get; init; }

    [JsonPropertyName("house_id")]
    public string? HouseId { get; init; }

    [JsonPropertyName("tenant_name")]
    public string? TenantName { get; init; }

    [JsonPropertyName("category")]
    public string? Category { get; init; }

    [JsonPropertyName("date")]
    public string? Date { get; init; }

    [JsonPropertyName("vault_id")]
    public string? VaultId { get; init; }

    [JsonPropertyName("is_manual")]
    public int? IsManual { get; init; }

    [JsonPropertyName("extra_info")]
    public string? ExtraInfo { get; init; }
}

public record TenantDto
{
    [JsonPropertyName("id")]
    public int? Id { get; init; }

    [JsonPropertyName("name")]
    public string Name { get; init; } = string.Empty;

    [JsonPropertyName("start_date")]
    public string StartDate { get; init; } = string.Empty;

    [JsonPropertyName("end_date")]
    public string? EndDate { get; init; }

    [JsonPropertyName("house_id")]
    public string? HouseId { get; init; }
}

public record DocumentDetailsDto
{
    [JsonPropertyName("vault_id")]
    public string VaultId { get; init; } = string.Empty;

    [JsonPropertyName("house_id")]
    public string HouseId { get; init; } = string.Empty;

    [JsonPropertyName("area_id")]
    public string? AreaId { get; init; }

    [JsonPropertyName("tenant_id")]
    public int TenantId { get; init; }

    [JsonPropertyName("tenant_name")]
    public string? TenantName { get; init; }

    [JsonPropertyName("tenant_start_date")]
    public string? TenantStartDate { get; init; }

    [JsonPropertyName("tenant_end_date")]
    public string? TenantEndDate { get; init; }

    [JsonPropertyName("batch_id")]
    public int BatchId { get; init; }

    [JsonPropertyName("batch_filename")]
    public string? BatchFilename { get; init; }

    [JsonPropertyName("batch_file_path")]
    public string? BatchFilePath { get; init; }

    [JsonPropertyName("primary_date")]
    public string? PrimaryDate { get; init; }

    [JsonPropertyName("arabic_title")]
    public string? ArabicTitle { get; init; }

    [JsonPropertyName("category")]
    public string? Category { get; init; }

    [JsonPropertyName("page_count")]
    public int PageCount { get; init; } = 1;

    [JsonPropertyName("is_manual")]
    public int IsManual { get; init; } = 0;

    [JsonPropertyName("notes")]
    public string? Notes { get; init; }

    [JsonPropertyName("created_at")]
    public string? CreatedAt { get; init; }

    [JsonPropertyName("physical_path")]
    public string? PhysicalPath { get; init; }

    [JsonPropertyName("pages")]
    public List<PageItemDto> Pages { get; init; } = new();
}

public record PageItemDto
{
    [JsonPropertyName("page_number")]
    public int PageNumber { get; init; }

    [JsonPropertyName("subject")]
    public string? Subject { get; init; }

    [JsonPropertyName("sender")]
    public string? Sender { get; init; }

    [JsonPropertyName("receiver")]
    public string? Receiver { get; init; }

    [JsonPropertyName("content_explanation")]
    public string? ContentExplanation { get; init; }

    [JsonPropertyName("raw_date")]
    public string? RawDate { get; init; }

    [JsonPropertyName("fine_category")]
    public string? FineCategory { get; init; }
}

public record IngestRequestDto
{
    public string AreaId { get; init; } = string.Empty;
    public string HouseId { get; init; } = string.Empty;
    public int TenantId { get; init; }
    public string Category { get; init; } = "13 - رسائل متنوعة";
    public string ArabicTitle { get; init; } = string.Empty;
    public string? PrimaryDate { get; init; }
    public string? Notes { get; init; }
    public int PageCount { get; init; } = 1;
    public string? SourcePdfFilename { get; init; }
    public string? SourcePdfPath { get; init; }
    public string? VaultId { get; init; }
    public string? Mode { get; init; } = "manual";
    public bool DryRun { get; init; } = false;
    public string? AreasRoot { get; init; }
}

public record IngestResponseDto
{
    [JsonPropertyName("status")]
    public string Status { get; init; } = "success";

    [JsonPropertyName("mode")]
    public string Mode { get; init; } = "manual";

    [JsonPropertyName("vault_id")]
    public string? VaultId { get; init; }

    [JsonPropertyName("vault_ids")]
    public List<string>? VaultIds { get; init; }

    [JsonPropertyName("batch_id")]
    public int? BatchId { get; init; }

    [JsonPropertyName("page_count")]
    public int PageCount { get; init; }

    [JsonPropertyName("documents_created")]
    public int DocumentsCreated { get; init; } = 1;

    [JsonPropertyName("house_id")]
    public string HouseId { get; init; } = string.Empty;

    [JsonPropertyName("area_id")]
    public string AreaId { get; init; } = string.Empty;

    [JsonPropertyName("message")]
    public string Message { get; init; } = string.Empty;

    [JsonPropertyName("is_manual")]
    public int IsManual { get; init; } = 1;
}

public record DocumentActionResponseDto
{
    [JsonPropertyName("status")]
    public string Status { get; init; } = "success";

    [JsonPropertyName("vault_id")]
    public string VaultId { get; init; } = string.Empty;

    [JsonPropertyName("arabic_title")]
    public string? ArabicTitle { get; init; }

    [JsonPropertyName("category")]
    public string? Category { get; init; }

    [JsonPropertyName("tenant_id")]
    public int? TenantId { get; init; }

    [JsonPropertyName("tenant_name")]
    public string? TenantName { get; init; }

    [JsonPropertyName("is_manual")]
    public int IsManual { get; init; } = 1;
}
