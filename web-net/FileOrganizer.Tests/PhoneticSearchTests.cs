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
    [InlineData("jamshed", "جمشيد أنور محمد أنور", true)]
    [InlineData("jamsheed", "جمشيد أنور محمد أنور", true)]
    [InlineData("jamshid", "جمشيد أنور محمد أنور", true)]
    [InlineData("tayseer", "تيسير خطاب عبد الكريم", true)]
    [InlineData("taiseer", "تيسير خطاب عبد الكريم", true)]
    [InlineData("sarfaraz", "سرفراز نواز محمد يوسف عبد الصادق رجا", true)]
    [InlineData("sarfraz", "سرفراز نواز محمد يوسف عبد الصادق رجا", true)]
    [InlineData("madu", "مادو سودانان ناير", true)]
    [InlineData("soodanan", "مادو سودانان ناير", true)]
    [InlineData("sudanan", "مادو سودانان ناير", true)]
    [InlineData("nair", "مادو سودانان ناير", true)]
    [InlineData("shaukat", "شوكت علي البلوشي", true)]
    [InlineData("showkat", "شوكت علي البلوشي", true)]
    [InlineData("shoukat", "شوكت علي البلوشي", true)]
    [InlineData("anwar", "محمد أنور حاجي حسن البلوشي", true)]
    [InlineData("anwar", "أنور علي عوض علي", true)]
    [InlineData("parvez", "شمس برويز محمد", true)]
    [InlineData("parwez", "شمس برويز محمد", true)]
    [InlineData("suwaidi", "محمد عبد القادر السويدي", true)]
    [InlineData("suwaidi", "عبدالله سعود الدوسري", false)]
    [InlineData("saud", "عبدالله سعود الدوسري", true)]
    [InlineData("awadh", "زياد عوض السليمان", true)]
    [InlineData("awad", "زياد عوض السليمان", true)]
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

    [Fact]
    public void ScoreTenantMatch_UniqueDatabaseNamesPrecisionAndIsolation()
    {
        // Jamshed
        Assert.True(TextUtils.ScoreTenantMatch("jamshed", "جمشيد أنور محمد أنور", "SAF F 2452_12") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("jamsheed", "جمشيد أنور محمد أنور", "SAF F 2452_12") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("jamshid", "جمشيد أنور محمد أنور", "SAF F 2452_12") >= 400);

        // Tayseer / Taiseer
        Assert.True(TextUtils.ScoreTenantMatch("tayseer", "تيسير خطاب عبد الكريم", "SAF F 2456_33") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("taiseer", "تيسير خطاب عبد الكريم", "SAF F 2456_33") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("khattab", "تيسير خطاب عبد الكريم", "SAF F 2456_33") >= 400);

        // Sarfaraz / Sarfraz
        Assert.True(TextUtils.ScoreTenantMatch("sarfaraz", "سرفراز نواز محمد يوسف عبد الصادق رجا", "SAF F 2452_33") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("sarfraz", "سرفراز نواز محمد يوسف عبد الصادق رجا", "SAF F 2452_33") >= 400);

        // Madhu / Soodanan / Nair
        Assert.True(TextUtils.ScoreTenantMatch("madu", "مادو سودانان ناير", "SAF F 2456_11") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("soodanan", "مادو سودانان ناير", "SAF F 2456_11") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("nair", "مادو سودانان ناير", "SAF F 2456_11") >= 400);

        // Shaukat / Showkat / Shoukat
        Assert.True(TextUtils.ScoreTenantMatch("shaukat", "شوكت علي البلوشي", "1260") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("showkat", "شوكت علي البلوشي", "1260") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("shoukat", "شوكت علي البلوشي", "1260") >= 400);

        // Anwar
        Assert.True(TextUtils.ScoreTenantMatch("anwar", "محمد أنور حاجي حسن البلوشي", "1260") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("anwar", "أنور علي عوض علي", "1260") >= 400);

        // Parvez / Parwez
        Assert.True(TextUtils.ScoreTenantMatch("parvez", "شمس برويز محمد", "SAF F 2450_12") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("parwez", "شمس برويز محمد", "SAF F 2450_12") >= 400);

        // Suwaidi vs Saud isolation
        Assert.True(TextUtils.ScoreTenantMatch("suwaidi", "محمد عبد القادر السويدي", "100") >= 400);
        Assert.Equal(0, TextUtils.ScoreTenantMatch("suwaidi", "عبدالله سعود الدوسري", "500"));
        Assert.True(TextUtils.ScoreTenantMatch("saud", "عبدالله سعود الدوسري", "500") >= 400);

        // Awadh / Awad
        Assert.True(TextUtils.ScoreTenantMatch("awadh", "زياد عوض السليمان", "SAF F 2450_21") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("awad", "زياد عوض السليمان", "SAF F 2450_21") >= 400);
    }

    [Fact]
    public void ScoreTenantMatch_ArabicSearches_PrecisionAndVariations()
    {
        // 1. Exact Arabic name matching
        Assert.True(TextUtils.ScoreTenantMatch("جمشيد", "جمشيد أنور محمد أنور", "SAF F 2452_12") >= 1000);
        Assert.True(TextUtils.ScoreTenantMatch("تيسير", "تيسير خطاب عبد الكريم", "SAF F 2456_33") >= 1000);
        Assert.True(TextUtils.ScoreTenantMatch("عميد", "عميد علي محمد عزيز", "SAF F 2450_22") >= 1000);
        Assert.True(TextUtils.ScoreTenantMatch("جاويد", "جاويد إقبال شودري", "1264") >= 1000);
        Assert.True(TextUtils.ScoreTenantMatch("شوكت", "شوكت علي البلوشي", "1260") >= 1000);
        Assert.True(TextUtils.ScoreTenantMatch("عثمان", "محمد عثمان حاجي فقير محمد", "551") >= 1000);
        Assert.True(TextUtils.ScoreTenantMatch("مادو", "مادو سودانان ناير", "SAF F 2456_11") >= 1000);
        Assert.True(TextUtils.ScoreTenantMatch("سرفراز", "سرفراز نواز محمد يوسف عبد الصادق رجا", "SAF F 2452_33") >= 1000);
        Assert.True(TextUtils.ScoreTenantMatch("شمس برويز", "شمس برويز محمد", "SAF F 2450_12") >= 1000);

        // 2. Hamza variations (bare Alif vs Hamza above/below: انور vs أنور, اقبال vs إقبال, احمد vs أحمد)
        Assert.True(TextUtils.ScoreTenantMatch("انور", "أنور علي عوض علي", "SAF F 2450_24") >= 1000);
        Assert.True(TextUtils.ScoreTenantMatch("أنور", "أنور علي عوض علي", "SAF F 2450_24") >= 1000);
        Assert.True(TextUtils.ScoreTenantMatch("اقبال", "جاويد إقبال شودري", "1264") >= 1000);
        Assert.True(TextUtils.ScoreTenantMatch("إقبال", "جاويد إقبال شودري", "1264") >= 1000);
        Assert.True(TextUtils.ScoreTenantMatch("احمد", "أحمد سالم بورشيد", "512") >= 1000);
        Assert.True(TextUtils.ScoreTenantMatch("أحمد", "أحمد سالم بورشيد", "512") >= 1000);

        // 3. Arabic Tashkeel / Harakat (diacritics stripping)
        Assert.True(TextUtils.ScoreTenantMatch("أَنْوَر", "أنور علي عوض علي", "SAF F 2450_24") >= 1000);
        Assert.True(TextUtils.ScoreTenantMatch("مُحَمَّد", "محمد أنور", "1260") >= 1000);
        Assert.True(TextUtils.ScoreTenantMatch("جَمْشِيد", "جمشيد أنور محمد أنور", "SAF F 2452_12") >= 1000);
        Assert.True(TextUtils.ScoreTenantMatch("تَيْسِير", "تيسير خطاب عبد الكريم", "SAF F 2456_33") >= 1000);

        // 4. Taa Marbuta (ة) vs Haa (ه) and Alif Maqsura (ى) vs Yaa (ي)
        Assert.True(TextUtils.ScoreTenantMatch("فاطمه", "فاطمة بنت علي", "100") >= 1000);
        Assert.True(TextUtils.ScoreTenantMatch("فاطمة", "فاطمة بنت علي", "100") >= 1000);
        Assert.True(TextUtils.ScoreTenantMatch("يحيي", "يحيى عبد الرحمن", "100") >= 1000);
        Assert.True(TextUtils.ScoreTenantMatch("يحيى", "يحيى عبد الرحمن", "100") >= 1000);

        // 5. Arabic isolation: سويدي matches السويدي and NOT سعود
        Assert.True(TextUtils.ScoreTenantMatch("السويدي", "محمد عبد القادر السويدي", "100") >= 1000);
        Assert.True(TextUtils.ScoreTenantMatch("سويدي", "محمد عبد القادر السويدي", "100") >= 1000);
        Assert.Equal(0, TextUtils.ScoreTenantMatch("سويدي", "عبدالله سعود الدوسري", "500"));
        Assert.True(TextUtils.ScoreTenantMatch("سعود", "عبدالله سعود الدوسري", "500") >= 1000);
        Assert.Equal(0, TextUtils.ScoreTenantMatch("سعود", "محمد عبد القادر السويدي", "100"));
    }

    [Fact]
    public void ArabicNormalizationAndVariants_WorksProperly()
    {
        Assert.Equal("أنور", TextUtils.StripArabicDiacritics("أَنْوَر"));
        Assert.Equal("محمد", TextUtils.StripArabicDiacritics("مُحَمَّد"));
        Assert.Equal("اقبال", TextUtils.NormalizeArabic("إقبال"));
        Assert.Equal("فاطمه", TextUtils.NormalizeArabic("فاطمة"));
        Assert.Equal("مستشفي", TextUtils.NormalizeArabic("مستشفى"));

        var vAnwar = TextUtils.GetArabicSearchVariants("انور");
        Assert.Contains("انور", vAnwar);
        Assert.Contains("أنور", vAnwar);

        var vSyana = TextUtils.GetArabicSearchVariants("صيانه");
        Assert.Contains("صيانه", vSyana);
        Assert.Contains("صيانة", vSyana);

        var vShahada = TextUtils.GetArabicSearchVariants("شهاده");
        Assert.Contains("شهاده", vShahada);
        Assert.Contains("شهادة", vShahada);
    }
}
