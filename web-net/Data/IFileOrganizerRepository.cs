using FileOrganizer.Web.Models;

namespace FileOrganizer.Web.Data;

public interface IFileOrganizerRepository
{
    Task<IReadOnlyList<TreeAreaDto>> GetTreeAsync(bool includeCategories = false, bool includeTimeline = false);
    Task<IReadOnlyList<HouseCardDto>> GetHousesAsync(string? areaId = null);
    Task<HouseProfileDto?> GetHouseProfileAsync(string areaId, string houseId);
    Task<IReadOnlyList<TimelineItemDto>> GetTimelineAsync(string areaId, string houseId, string? tenantName = null);
    Task<IReadOnlyList<CategoryFolderDto>> GetCategoriesAsync(string areaId, string houseId);
    Task<IReadOnlyList<TenantDto>> GetTenantsAsync(string houseId);
    Task<IReadOnlyList<SearchResultDto>> SearchAsync(string query, int limit = 50);
    Task<DocumentDetailsDto?> GetDocumentByVaultIdAsync(string vaultId, string? areasRoot = null);
    Task<IngestResponseDto> AddManualDocumentAsync(IngestRequestDto request);
    Task<DocumentActionResponseDto?> UpdateDocumentAsync(
        string vaultId,
        string? arabicTitle = null,
        string? category = null,
        int? tenantId = null,
        string? primaryDate = null,
        int? isManual = 1,
        string? notes = null);
    Task<DocumentActionResponseDto?> CopyDocumentAsync(
        string vaultId,
        string? targetCategory = null,
        int? targetTenantId = null,
        string? targetTitle = null,
        string? newVaultId = null,
        string? areasRoot = null);

    // Helpers for database seeding and testing
    Task<Area> AddAreaAsync(string areaId, string? code = null);
    Task<House> AddHouseAsync(string houseId, string areaId);
    Task<Tenant> AddTenantAsync(string houseId, string name, string startDate, string? endDate = null);
    Task<Document?> GetDocumentRawAsync(string vaultId);
    Task<IReadOnlyList<Page>> GetPagesByVaultIdAsync(string vaultId);
    Task EnsureSchemaAsync();
}
