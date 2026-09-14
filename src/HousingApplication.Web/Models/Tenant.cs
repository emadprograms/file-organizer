namespace FileOrganizer.Web.Models;

public class Tenant
{
    public int Id { get; set; }
    public string HouseId { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string? StartDate { get; set; }
    public string? EndDate { get; set; }
    public int IsResident { get; set; } = 1;
    public string? Notes { get; set; }
}
