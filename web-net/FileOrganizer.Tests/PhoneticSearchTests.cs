using FileOrganizer.Web.Common;
using Xunit;

namespace FileOrganizer.Tests;

public class PhoneticSearchTests
{
    [Theory]
    [InlineData("ameed", "عميد علي محمد عزيز", true)]
    [InlineData("ameed", "أحمد سالم بورشيد", false)]
    [InlineData("ameed", "محمد عثمان حاجي فقير محمد", false)]
    [InlineData("javed", "جاويد أكرم محمد", true)]
    [InlineData("javed", "خالد جاويد محمد", true)]
    [InlineData("jawed", "جاويد أكرم محمد", true)]
    [InlineData("khalil", "فواز خليل الطارش", true)]
    [InlineData("khalil", "خليل محمد صادق الساعاتي", true)]
    [InlineData("fawaz", "فواز خليل الطارش", true)]
    [InlineData("balushi", "عدنان عبدالواحد علي البلوشي", true)]
    [InlineData("al balushi", "عدنان عبدالواحد علي البلوشي", true)]
    [InlineData("iqbal", "جاويد إقبال شودري", true)]
    [InlineData("aziz", "عميد علي محمد عزيز", true)]
    public void ScoreTenantMatch_AccuratelyMatchesOrRejects(string query, string tenantName, bool shouldMatch)
    {
        int score = TextUtils.ScoreTenantMatch(query, tenantName, "100");
        if (shouldMatch)
        {
            Assert.True(score > 0, $"Expected '{query}' to match '{tenantName}', but got score {score}");
        }
        else
        {
            Assert.True(score == 0, $"Expected '{query}' NOT to match '{tenantName}', but got score {score}");
        }
    }

    [Fact]
    public void ScoreTenantMatch_AmeedRanksHigherThanUnrelatedNames()
    {
        int ameedScore = TextUtils.ScoreTenantMatch("ameed", "عميد علي محمد عزيز", "SAF F 2450_22");
        int ahmedScore = TextUtils.ScoreTenantMatch("ameed", "أحمد سالم بورشيد", "512");
        int mohamedScore = TextUtils.ScoreTenantMatch("ameed", "محمد عثمان حاجي", "551");

        Assert.True(ameedScore >= 400, $"Expected high score for ameed, got {ameedScore}");
        Assert.Equal(0, ahmedScore);
        Assert.Equal(0, mohamedScore);
    }

    [Fact]
    public void ScoreTenantMatch_JavedMatchesBothVandWTransliterations()
    {
        int javedScore = TextUtils.ScoreTenantMatch("javed", "جاويد أكرم محمد", "1264");
        int jawedScore = TextUtils.ScoreTenantMatch("jawed", "جاويد أكرم محمد", "1264");

        Assert.True(javedScore >= 400, $"Expected javed to match جاويد with score >= 400, got {javedScore}");
        Assert.True(jawedScore >= 400, $"Expected jawed to match جاويد with score >= 400, got {jawedScore}");
    }

    [Fact]
    public void ScoreTenantMatch_MultiWordQuery_MatchesAllTokens()
    {
        int score = TextUtils.ScoreTenantMatch("fawaz khalil", "فواز خليل الطارش", "500");
        Assert.True(score >= 800, $"Expected multi-word query score >= 800, got {score}");

        int mismatchScore = TextUtils.ScoreTenantMatch("fawaz javed", "فواز خليل الطارش", "500");
        Assert.Equal(0, mismatchScore);
    }

    [Fact]
    public void CleanArticle_StripsAlPrefixesCorrectly()
    {
        Assert.Equal("balushi", TextUtils.CleanArticle("al-balushi"));
        Assert.Equal("balushi", TextUtils.CleanArticle("al balushi"));
        Assert.Equal("balushi", TextUtils.CleanArticle("albalushi"));
        Assert.Equal("بلوشي", TextUtils.CleanArticle("البلوشي"));
        Assert.Equal("طارش", TextUtils.CleanArticle("الطارش"));
    }
}
