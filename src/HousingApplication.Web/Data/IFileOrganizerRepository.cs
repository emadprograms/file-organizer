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
    Task<DocumentDetailsDto?> GetDocumentDetailsAsync(string vaultId, string? areasRoot = null);
    Task<DocumentActionResponseDto?> ResetDocumentLockAsync(string vaultId);
    Task<DocumentActionResponseDto?> UpdateDocumentNotesAsync(string vaultId, string notes);
    Task<DocumentActionResponseDto?> UpdateDocumentTenantAsync(string vaultId, int tenantId);
    Task<bool> DeleteDocumentAsync(string areaId, string houseId, string vaultId, string? areasRoot = null);
    Task<BatchDeleteResponseDto> BatchDeleteDocumentsAsync(string areaId, string houseId, IEnumerable<string> vaultIds, string? areasRoot = null);
    Task<BatchMoveResponseDto> BatchMoveDocumentsAsync(string areaId, string houseId, IEnumerable<string> vaultIds, string targetCategory, int? targetTenantId = null);
    Task<BatchCopyResponseDto> BatchCopyDocumentsAsync(string areaId, string houseId, IEnumerable<string> vaultIds, string targetCategory, int? targetTenantId = null, string? areasRoot = null);
    Task<TenantReallocationResponseDto> BulkUpdateTenantsAsync(string houseId, IReadOnlyList<TenantDto> tenants, bool reallocate);
    Task<int> DeleteCategoryAsync(string houseId, string categoryName);
    Task<DbInfoResponseDto> GetDbStatsAsync();
    Task<DbTableResponseDto> GetDbTableDataAsync(string tableName, int limit = 50, int offset = 0, string? search = null);
    Task<CreateHouseResponseDto> CreateHouseAsync(string areaId, string houseId, string? initialTenantName = null, string? startDate = null, string? areasRoot = null);
    Task<bool> DeleteHouseAsync(string areaId, string houseId, string? areasRoot = null);
    Task<bool> UpdateTenantDatesAsync(int tenantId, string? startDate, string? endDate);
    Task<ExtractPagesResponseDto> ExtractPagesAsync(string areaId, string houseId, string vaultId, ExtractPagesRequestDto request, string? areasRoot = null);
    Task<DeletePagesResponseDto> DeletePagesAsync(string areaId, string houseId, string vaultId, DeletePagesRequestDto request, string? areasRoot = null);
    Task<ReorderPagesResponseDto> ReorderPagesAsync(string areaId, string houseId, string vaultId, ReorderPagesRequestDto request, string? areasRoot = null);
    Task<RotatePagesResponseDto> RotatePagesAsync(string areaId, string houseId, string vaultId, RotatePagesRequestDto request, string? areasRoot = null);
    Task<MergeDocumentsResponseDto> MergeDocumentsAsync(string areaId, string houseId, MergeDocumentsRequestDto request, string? areasRoot = null);

    // User Authentication & Management
    Task<User?> GetUserByUsernameAsync(string username);
    Task<User?> GetUserByIdAsync(int id);
    Task<IReadOnlyList<UserDto>> GetAllUsersAsync();

    // Helpers for database seeding and testing
    Task<Area> AddAreaAsync(string areaId, string? code = null);
    Task<House> AddHouseAsync(string houseId, string areaId);
    Task<Tenant> AddTenantAsync(string houseId, string name, string? startDate = null, string? endDate = null, int isResident = 1, string? notes = null);
    Task<Document?> GetDocumentRawAsync(string vaultId);
    Task<IReadOnlyList<Page>> GetPagesByVaultIdAsync(string vaultId);
    Task EnsureSchemaAsync();
}

