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
    [InlineData("usman", "محمد عثمان حاجي فقير محمد", true)]
    [InlineData("uthman", "محمد عثمان حاجي فقير محمد", true)]
    [InlineData("osman", "محسن عثمان عبد الرب", true)]
    [InlineData("othman", "عادل عبد الرحمن عثمان البلوشي", true)]
    [InlineData("usman", "زياد عوض السليمان", false)]
    [InlineData("usman", "سلمان عبيد عنفوس", false)]
    [InlineData("usman", "سليمان مطلق نجم العبدالله", false)]
    [InlineData("usman", "وسيم سردار محمد", false)]
    [InlineData("waseem", "وسيم سردار محمد", true)]
    [InlineData("waseem", "سامي محمد ناجي الصميل", false)]
    [InlineData("waseem", "أسماء خيام محمد الأنصاري", false)]
    [InlineData("zaid", "زياد عوض السليمان", true)]
    [InlineData("zaid", "مصلح عيسى علي زيد", true)]
    [InlineData("zaid", "محمد عثمان حاجي", false)]
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
    public void ScoreTenantMatch_UsmanMatchesOthmanAndStrictlyRejectsZaidSalmanWaseem()
    {
        // Must match عثمان variations with high score
        int usmanScore = TextUtils.ScoreTenantMatch("usman", "محمد عثمان حاجي فقير محمد", "551");
        int uthmanScore = TextUtils.ScoreTenantMatch("uthman", "محمد عثمان حاجي فقير محمد", "551");
        int osmanScore = TextUtils.ScoreTenantMatch("osman", "محسن عثمان عبد الرب", "950");
        int othmanScore = TextUtils.ScoreTenantMatch("othman", "عادل عبد الرحمن عثمان البلوشي", "1336");

        Assert.True(usmanScore >= 400, $"Expected usman to match عثمان with score >= 400, got {usmanScore}");
        Assert.True(uthmanScore >= 400, $"Expected uthman to match عثمان with score >= 400, got {uthmanScore}");
        Assert.True(osmanScore >= 400, $"Expected osman to match عثمان with score >= 400, got {osmanScore}");
        Assert.True(othmanScore >= 400, $"Expected othman to match عثمان with score >= 400, got {othmanScore}");

        // MUST NOT match Zaid, Salman, Sulaiman, or Waseem
        int zaidScore = TextUtils.ScoreTenantMatch("usman", "زياد عوض السليمان", "SAF F 2450_21");
        int salmanScore = TextUtils.ScoreTenantMatch("usman", "سلمان عبيد عنفوس", "1281");
        int sulaimanScore = TextUtils.ScoreTenantMatch("usman", "سليمان مطلق نجم العبدالله", "608");
        int waseemScore = TextUtils.ScoreTenantMatch("usman", "وسيم سردار محمد", "551");

        Assert.Equal(0, zaidScore);
        Assert.Equal(0, salmanScore);
        Assert.Equal(0, sulaimanScore);
        Assert.Equal(0, waseemScore);
    }

    [Fact]
    public void ScoreTenantMatch_WaseemMatchesWaseemAndStrictlyRejectsSamiAsma()
    {
        int waseemScore = TextUtils.ScoreTenantMatch("waseem", "وسيم سردار محمد", "551");
        int samiScore = TextUtils.ScoreTenantMatch("waseem", "سامي محمد ناجي الصميل", "944");
        int asmaScore = TextUtils.ScoreTenantMatch("waseem", "أسماء خيام محمد الأنصاري", "514");

        Assert.True(waseemScore >= 400, $"Expected waseem to match وسيم, got {waseemScore}");
        Assert.Equal(0, samiScore);
        Assert.Equal(0, asmaScore);
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
