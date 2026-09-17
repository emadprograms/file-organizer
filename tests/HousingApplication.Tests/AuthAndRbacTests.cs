using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using FileOrganizer.Web.Common;
using FileOrganizer.Web.Data;
using FileOrganizer.Web.Models;
using Microsoft.Extensions.DependencyInjection;
using Xunit;

namespace FileOrganizer.Tests;

public class AuthAndRbacTests : IClassFixture<ApiTestFixture>
{
    private readonly ApiTestFixture _fixture;
    private readonly HttpClient _client;

    public AuthAndRbacTests(ApiTestFixture fixture)
    {
        _fixture = fixture;
        _client = fixture.CreateClient(new Microsoft.AspNetCore.Mvc.Testing.WebApplicationFactoryClientOptions
        {
            HandleCookies = true
        });
    }

    [Fact]
    public async Task Seeding_InitializesAll10Users_WithCorrectRoles()
    {
        await _fixture.SeedDataAsync();

        using var scope = _fixture.Services.CreateScope();
        var repo = scope.ServiceProvider.GetRequiredService<IFileOrganizerRepository>();

        var users = await repo.GetAllUsersAsync();
        Assert.NotNull(users);
        Assert.True(users.Count >= 10);

        var adminUsernames = new[] { "Emad", "Bubshait", "Ehtezaz", "Mustafa" };
        foreach (var admin in adminUsernames)
        {
            var user = users.FirstOrDefault(u => string.Equals(u.Username, admin, StringComparison.OrdinalIgnoreCase));
            Assert.NotNull(user);
            Assert.Equal("Admin", user.Role);
            Assert.True(user.CanDelete);
        }

        var contributorUsernames = new[] { "Nawaf", "Naseem", "Mulla", "Mariam", "Shaima", "Mona" };
        foreach (var contrib in contributorUsernames)
        {
            var user = users.FirstOrDefault(u => string.Equals(u.Username, contrib, StringComparison.OrdinalIgnoreCase));
            Assert.NotNull(user);
            Assert.Equal("Contributor", user.Role);
            Assert.False(user.CanDelete);
        }
    }

    [Fact]
    public void PasswordHasher_GeneratesDistinctSalt_AndVerifiesCorrectly()
    {
        var (hash1, salt1) = PasswordHasher.HashPassword("SecretPassword123");
        var (hash2, salt2) = PasswordHasher.HashPassword("SecretPassword123");

        Assert.NotEmpty(hash1);
        Assert.NotEmpty(salt1);
        Assert.NotEqual(salt1, salt2); // Unique salts
        Assert.NotEqual(hash1, hash2);

        Assert.True(PasswordHasher.VerifyPassword("SecretPassword123", hash1, salt1));
        Assert.False(PasswordHasher.VerifyPassword("WrongPassword", hash1, salt1));
        Assert.False(PasswordHasher.VerifyPassword("", hash1, salt1));
        Assert.False(PasswordHasher.VerifyPassword(null, hash1, salt1));
    }

    [Fact]
    public async Task AuthEndpoints_LoginSuccess_MeReturnsUser_LogoutClearsSession()
    {
        await _fixture.SeedDataAsync();

        var client = _fixture.CreateClient(new Microsoft.AspNetCore.Mvc.Testing.WebApplicationFactoryClientOptions
        {
            HandleCookies = true
        });

        // 1. Initially unauthenticated
        var meInitial = await client.GetFromJsonAsync<AuthStatusResponseDto>("/api/auth/me");
        Assert.NotNull(meInitial);
        Assert.False(meInitial.Authenticated);
        Assert.Null(meInitial.User);

        // 2. Login with valid Admin user Emad
        var loginRes = await client.PostAsJsonAsync("/api/auth/login", new LoginRequestDto
        {
            Username = "Emad",
            Password = "emad123"
        });
        Assert.Equal(HttpStatusCode.OK, loginRes.StatusCode);
        var loginData = await loginRes.Content.ReadFromJsonAsync<LoginResponseDto>();
        Assert.NotNull(loginData);
        Assert.True(loginData.Success);
        Assert.NotNull(loginData.User);
        Assert.Equal("Emad", loginData.User.Username);
        Assert.Equal("Admin", loginData.User.Role);
        Assert.True(loginData.User.CanDelete);

        // 3. Current user is now authenticated
        var meAuth = await client.GetFromJsonAsync<AuthStatusResponseDto>("/api/auth/me");
        Assert.NotNull(meAuth);
        Assert.True(meAuth.Authenticated);
        Assert.NotNull(meAuth.User);
        Assert.Equal("Emad", meAuth.User.Username);
        Assert.True(meAuth.User.CanDelete);

        // 4. Logout
        var logoutRes = await client.PostAsync("/api/auth/logout", null);
        Assert.Equal(HttpStatusCode.OK, logoutRes.StatusCode);

        // 5. Current user is now unauthenticated
        var meAfterLogout = await client.GetFromJsonAsync<AuthStatusResponseDto>("/api/auth/me");
        Assert.NotNull(meAfterLogout);
        Assert.False(meAfterLogout.Authenticated);
        Assert.Null(meAfterLogout.User);
    }

    [Fact]
    public async Task AuthEndpoints_InvalidPassword_Returns401()
    {
        await _fixture.SeedDataAsync();

        var client = _fixture.CreateClient();
        var loginRes = await client.PostAsJsonAsync("/api/auth/login", new LoginRequestDto
        {
            Username = "Emad",
            Password = "CompletelyWrongPassword!999"
        });
        Assert.Equal(HttpStatusCode.Unauthorized, loginRes.StatusCode);
    }

    [Fact]
    public async Task AuthEndpoints_GetUsers_ReturnsAllAvailableUsers()
    {
        await _fixture.SeedDataAsync();

        var usersRes = await _client.GetAsync("/api/auth/users");
        Assert.Equal(HttpStatusCode.OK, usersRes.StatusCode);
        var users = await usersRes.Content.ReadFromJsonAsync<List<UserDto>>();
        Assert.NotNull(users);
        Assert.True(users.Count >= 10);
        Assert.Contains(users, u => u.Username == "Emad" && u.CanDelete);
        Assert.Contains(users, u => u.Username == "Nawaf" && !u.CanDelete);
    }

    [Fact]
    public async Task RBAC_ContributorUser_CannotDeleteDocument_Returns403()
    {
        await _fixture.SeedDataAsync();

        var client = _fixture.CreateClient(new Microsoft.AspNetCore.Mvc.Testing.WebApplicationFactoryClientOptions
        {
            HandleCookies = true
        });

        // Login as Contributor (Nawaf)
        var loginRes = await client.PostAsJsonAsync("/api/auth/login", new LoginRequestDto
        {
            Username = "Nawaf",
            Password = "nawaf123"
        });
        Assert.Equal(HttpStatusCode.OK, loginRes.StatusCode);

        // Attempt single doc delete
        var deleteRes = await client.DeleteAsync("/api/areas/Safra%20C/houses/500/documents/any_vault_id");
        Assert.Equal(HttpStatusCode.Forbidden, deleteRes.StatusCode);

        var json = await deleteRes.Content.ReadAsStringAsync();
        Assert.Contains("Permission denied", json);
    }

    [Fact]
    public async Task RBAC_ContributorUser_CannotBatchDelete_Returns403()
    {
        await _fixture.SeedDataAsync();

        var client = _fixture.CreateClient(new Microsoft.AspNetCore.Mvc.Testing.WebApplicationFactoryClientOptions
        {
            HandleCookies = true
        });

        // Login as Contributor (Mariam)
        await client.PostAsJsonAsync("/api/auth/login", new LoginRequestDto
        {
            Username = "Mariam",
            Password = "mariam123"
        });

        // Attempt batch delete
        var batchRes = await client.PostAsJsonAsync(
            "/api/areas/Safra%20C/houses/500/documents/batch-delete",
            new BatchDeleteRequestDto { VaultIds = new List<string> { "v1", "v2" } });

        Assert.Equal(HttpStatusCode.Forbidden, batchRes.StatusCode);
        var json = await batchRes.Content.ReadAsStringAsync();
        Assert.Contains("Permission denied", json);
    }

    [Fact]
    public async Task RBAC_ContributorUser_CannotDeletePages_Returns403()
    {
        await _fixture.SeedDataAsync();

        var client = _fixture.CreateClient(new Microsoft.AspNetCore.Mvc.Testing.WebApplicationFactoryClientOptions
        {
            HandleCookies = true
        });

        // Login as Contributor (Mona)
        await client.PostAsJsonAsync("/api/auth/login", new LoginRequestDto
        {
            Username = "Mona",
            Password = "mona123"
        });

        // Attempt page delete
        var pageRes = await client.PostAsJsonAsync(
            "/api/areas/Safra%20C/houses/500/documents/doc1/delete-pages",
            new DeletePagesRequestDto { PageNumbers = new List<int> { 1 } });

        Assert.Equal(HttpStatusCode.Forbidden, pageRes.StatusCode);
        var json = await pageRes.Content.ReadAsStringAsync();
        Assert.Contains("Permission denied", json);
    }

    [Fact]
    public async Task RBAC_ContributorUser_CannotDeleteHouse_Returns403()
    {
        await _fixture.SeedDataAsync();

        var client = _fixture.CreateClient(new Microsoft.AspNetCore.Mvc.Testing.WebApplicationFactoryClientOptions
        {
            HandleCookies = true
        });

        // Login as Contributor (Shaima)
        await client.PostAsJsonAsync("/api/auth/login", new LoginRequestDto
        {
            Username = "Shaima",
            Password = "shaima123"
        });

        // Attempt house delete
        var houseRes = await client.DeleteAsync("/api/areas/Safra%20C/houses/500");
        Assert.Equal(HttpStatusCode.Forbidden, houseRes.StatusCode);
        var json = await houseRes.Content.ReadAsStringAsync();
        Assert.Contains("Permission denied", json);
    }

    [Fact]
    public async Task RBAC_ContributorUser_CanReadAndUpload()
    {
        await _fixture.SeedDataAsync();

        var client = _fixture.CreateClient(new Microsoft.AspNetCore.Mvc.Testing.WebApplicationFactoryClientOptions
        {
            HandleCookies = true
        });

        // Login as Contributor (Naseem)
        var loginRes = await client.PostAsJsonAsync("/api/auth/login", new LoginRequestDto
        {
            Username = "Naseem",
            Password = "naseem123"
        });
        Assert.Equal(HttpStatusCode.OK, loginRes.StatusCode);

        // Read tree
        var treeRes = await client.GetAsync("/api/tree");
        Assert.Equal(HttpStatusCode.OK, treeRes.StatusCode);

        // Read houses
        var housesRes = await client.GetAsync("/api/houses");
        Assert.Equal(HttpStatusCode.OK, housesRes.StatusCode);

        // Search
        var searchRes = await client.GetAsync("/api/search?q=test");
        Assert.Equal(HttpStatusCode.OK, searchRes.StatusCode);
    }
}
