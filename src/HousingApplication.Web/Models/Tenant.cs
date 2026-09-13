namespace FileOrganizer.Web.Models;

public class Tenant
{
    public int Id { get; set; }
    public string HouseId { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string StartDate { get; set; } = string.Empty;
    public string? EndDate { get; set; }
}
