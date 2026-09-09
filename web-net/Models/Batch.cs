namespace FileOrganizer.Web.Models;

public class Batch
{
    public int Id { get; set; }
    public string HouseId { get; set; } = string.Empty;
    public string Filename { get; set; } = string.Empty;
    public string FilePath { get; set; } = string.Empty;
    public int PageCount { get; set; }
    public string Status { get; set; } = "completed";
    public string? CreatedAt { get; set; }
}
