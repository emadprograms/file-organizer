namespace FileOrganizer.Web.Models;

public class Page
{
    public int Id { get; set; }
    public int BatchId { get; set; }
    public int PageNumber { get; set; }
    public string HouseId { get; set; } = string.Empty;
    public string? Category { get; set; }
    public string? ContentExplanation { get; set; }
    public string? ExpectedTenantName { get; set; }
    public string? ExpectedHouseNumber { get; set; }
    public string? RawDate { get; set; }
    public string? Sender { get; set; }
    public string? Receiver { get; set; }
    public string? Subject { get; set; }
    public bool IsContinuation { get; set; }
    public int? TenantId { get; set; }
    public string? ResolvedDate { get; set; }
    public string? FineCategory { get; set; }
    public string? FineCategoryReason { get; set; }
    public string? VaultId { get; set; }
}
