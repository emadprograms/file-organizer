using FileOrganizer.Web.Common;
using FileOrganizer.Web.Data;
using Microsoft.Extensions.Configuration;
using Xunit;

namespace FileOrganizer.Tests;

public class HouseNumberSearchTests
{
    private readonly FileOrganizerRepository _repository;

    public HouseNumberSearchTests()
    {
        var config = new ConfigurationBuilder()
            .AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["ORGANIZER_DB_PATH"] = "/tmp/file_organizer_local.db"
            })
            .Build();

        var factory = new SqliteDbConnectionFactory(config);
        _repository = new FileOrganizerRepository(factory);
    }

    [Theory]
    [InlineData("٥٠٠")]
    [InlineData("۵۰۰")]
    [InlineData("بيت ٥٠٠")]
    [InlineData("بيت 500")]
    [InlineData("منزل ٥٠٠")]
    [InlineData("منزل 500")]
    [InlineData("house 500")]
    [InlineData("house ٥٠٠")]
    public async Task Search_ArabicHouse500_ReturnsHouse500AtTop(string query)
    {
        var results = await _repository.SearchAsync(query);

        Assert.NotEmpty(results);

        var house500 = results.FirstOrDefault(r => r.Type == "house" && r.HouseId == "500");
        Assert.NotNull(house500);
        Assert.Equal("House 500", house500.Title);
        Assert.Equal("Safra D", house500.AreaId);

        // Verify that House 500 is the first house result
        var firstHouse = results.FirstOrDefault(r => r.Type == "house");
        Assert.NotNull(firstHouse);
        Assert.Equal("500", firstHouse.HouseId);

        // Verify that tenants of House 500 are also surfaced
        var tenants = results.Where(r => r.Type == "tenant" && r.HouseId == "500").ToList();
        Assert.NotEmpty(tenants);
        Assert.Contains(tenants, t => t.Title == "فواز خليل الطارش");
    }

    [Theory]
    [InlineData("٥٥٢أ")]
    [InlineData("٥٥٢ أ")]
    [InlineData("552أ")]
    [InlineData("552 أ")]
    [InlineData("بيت ٥٥٢أ")]
    [InlineData("بيت 552أ")]
    [InlineData("house 552a")]
    [InlineData("552a")]
    [InlineData("552A")]
    public async Task Search_ArabicHouse552A_ReturnsHouse552AAtTop(string query)
    {
        var results = await _repository.SearchAsync(query);

        Assert.NotEmpty(results);

        var house552A = results.FirstOrDefault(r => r.Type == "house" && r.HouseId == "552A");
        Assert.NotNull(house552A);
        Assert.Equal("House 552A", house552A.Title);

        var firstHouse = results.FirstOrDefault(r => r.Type == "house");
        Assert.NotNull(firstHouse);
        Assert.Equal("552A", firstHouse.HouseId);

        // Verify tenants in 552A are surfaced (Avinash and Adnan)
        var tenants = results.Where(r => r.Type == "tenant" && r.HouseId == "552A").ToList();
        Assert.NotEmpty(tenants);
        Assert.Contains(tenants, t => t.Title.Contains("أفيناش") || t.Title.Contains("عدنان"));
    }

    [Theory]
    [InlineData("شقة 2450_1")]
    [InlineData("شقة ٢٤٥٠_١")]
    [InlineData("٢٤٥٠_١")]
    [InlineData("2450_1")]
    public async Task Search_ArabicFlat2450_1_ReturnsSafF2450_1(string query)
    {
        var results = await _repository.SearchAsync(query);

        Assert.NotEmpty(results);

        var flat = results.FirstOrDefault(r => r.Type == "house" && r.HouseId == "SAF F 2450_1");
        Assert.NotNull(flat);
        Assert.Equal("House SAF F 2450_1", flat.Title);
    }

    [Fact]
    public void NormalizeArabicDigits_ConvertsStandardAndEasternNumerals()
    {
        Assert.Equal("0123456789", TextUtils.NormalizeArabicDigits("٠١٢٣٤٥٦٧٨٩"));
        Assert.Equal("0123456789", TextUtils.NormalizeArabicDigits("۰۱۲۳۴۵۶۷۸۹"));
        Assert.Equal("House 500 in Safra", TextUtils.NormalizeArabicDigits("House ٥٠٠ in Safra"));
    }

    [Fact]
    public void ToArabicDigits_ConvertsAsciiDigitsToEasternNumerals()
    {
        Assert.Equal("٠١٢٣٤٥٦٧٨٩", TextUtils.ToArabicDigits("0123456789"));
        Assert.Equal("بيت ٥٠٠", TextUtils.ToArabicDigits("بيت 500"));
    }

    [Fact]
    public void ExtractHouseNumber_ExtractsNumbersAndLetterSuffixes()
    {
        Assert.Equal("500", TextUtils.ExtractHouseNumber("500"));
        Assert.Equal("500", TextUtils.ExtractHouseNumber("٥٠٠"));
        Assert.Equal("500", TextUtils.ExtractHouseNumber("بيت ٥٠٠"));
        Assert.Equal("500", TextUtils.ExtractHouseNumber("منزل 500"));
        Assert.Equal("500", TextUtils.ExtractHouseNumber("house 500"));
        Assert.Equal("552A", TextUtils.ExtractHouseNumber("٥٥٢أ"));
        Assert.Equal("552A", TextUtils.ExtractHouseNumber("٥٥٢ أ"));
        Assert.Equal("552A", TextUtils.ExtractHouseNumber("552أ"));
        Assert.Equal("552A", TextUtils.ExtractHouseNumber("552 a"));
        Assert.Equal("552A", TextUtils.ExtractHouseNumber("552A"));
        Assert.Equal("624D", TextUtils.ExtractHouseNumber("٦٢٤د"));
        Assert.Equal("624G", TextUtils.ExtractHouseNumber("٦٢٤ز"));
        Assert.Equal("2450_1", TextUtils.ExtractHouseNumber("شقة ٢٤٥٠_١"));
    }

    [Fact]
    public void ScoreTenantMatch_PrioritizesHouseMatchingWithArabicNumerals()
    {
        // Tenant in House 500 matches query ٥٠٠ with high score
        int scoreArabic = TextUtils.ScoreTenantMatch("٥٠٠", "فواز خليل الطارش", "500");
        Assert.True(scoreArabic >= 900, $"Expected score >= 900, got {scoreArabic}");

        int scorePrefix = TextUtils.ScoreTenantMatch("بيت ٥٠٠", "فواز خليل الطارش", "500");
        Assert.True(scorePrefix >= 900, $"Expected score >= 900, got {scorePrefix}");

        // Tenant in House 552A matches ٥٥٢أ
        int score552A = TextUtils.ScoreTenantMatch("٥٥٢أ", "أفيناش راجانيكانت جورد", "552A");
        Assert.True(score552A >= 900, $"Expected score >= 900, got {score552A}");
    }
}
