namespace FileOrganizer.Web.Models;

public class Document
{
    public string VaultId { get; set; } = string.Empty;
    public string HouseId { get; set; } = string.Empty;
    public int TenantId { get; set; }
    public int BatchId { get; set; }
    public string? PrimaryDate { get; set; }
    public string? ArabicTitle { get; set; }
    public string? Category { get; set; }
    public int PageCount { get; set; } = 1;
    public int IsManual { get; set; } = 0;
    public string? Notes { get; set; }
    public int IsTimelineVisible { get; set; } = 1;
    public string? CreatedAt { get; set; }
}
