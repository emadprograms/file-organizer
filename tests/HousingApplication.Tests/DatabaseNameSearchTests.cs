using System.Text.Json;
using FileOrganizer.Web.Common;
using Xunit;

namespace FileOrganizer.Tests;

public class DatabaseNameSearchTests
{
    private class TenantRecord
    {
        public int id { get; set; }
        public string house_id { get; set; } = "";
        public string name { get; set; } = "";
        public int is_resident { get; set; }
    }

    private static readonly List<TenantRecord> AllTenants;

    static DatabaseNameSearchTests()
    {
        string[] candidatePaths = new[]
        {
            Path.Combine(AppContext.BaseDirectory, "TestData", "all_715_tenants.json"),
            Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "TestData", "all_715_tenants.json"),
            Path.Combine(Directory.GetCurrentDirectory(), "tests", "HousingApplication.Tests", "TestData", "all_715_tenants.json"),
            Path.Combine(Directory.GetCurrentDirectory(), "TestData", "all_715_tenants.json"),
            "/tmp/all_715_tenants.json"
        };

        string? foundPath = candidatePaths.FirstOrDefault(File.Exists);
        if (foundPath != null)
        {
            var json = File.ReadAllText(foundPath);
            AllTenants = JsonSerializer.Deserialize<List<TenantRecord>>(json) ?? new();
        }
        else
        {
            AllTenants = new();
        }
    }

    public static IEnumerable<object[]> GetAllTenantsData()
    {
        return AllTenants.Select(t => new object[] { t.id, t.name, t.house_id });
    }

    [Theory]
    [MemberData(nameof(GetAllTenantsData))]
    public void EverySingleTenant_InDatabase_MatchesSuccessfully(int id, string name, string houseId)
    {
        if (string.IsNullOrWhiteSpace(name)) return;

        // 1. Exact Arabic Match
        int exactScore = TextUtils.ScoreTenantMatch(name, name, houseId);
        Assert.True(exactScore >= 1000, $"Tenant ID {id} '{name}' (House {houseId}) failed exact match: {exactScore}");

        // 2. Normalized Arabic Match
        string normalized = TextUtils.NormalizeArabic(name);
        int normScore = TextUtils.ScoreTenantMatch(normalized, name, houseId);
        Assert.True(normScore >= 1000, $"Tenant ID {id} '{name}' (House {houseId}) failed normalized match '{normalized}': {normScore}");

        // 3. First Name Match
        var tokens = name.Trim().Split(' ', StringSplitOptions.RemoveEmptyEntries);
        if (tokens.Length > 0)
        {
            string first = tokens[0];
            int firstScore = TextUtils.ScoreTenantMatch(first, name, houseId);
            Assert.True(firstScore >= 500, $"Tenant ID {id} '{name}' (House {houseId}) failed first name match '{first}': {firstScore}");
        }

        // 4. Latin Transliteration Match
        string latin = TextUtils.ToLatin(name);
        int latinScore = TextUtils.ScoreTenantMatch(latin, name, houseId);
        Assert.True(latinScore >= 400, $"Tenant ID {id} '{name}' (House {houseId}) failed Latin transliteration match '{latin}': {latinScore}");
    }

    [Fact]
    public void DatabaseDataset_HasAll715Tenants()
    {
        Assert.True(AllTenants.Count >= 715, $"Expected at least 715 tenants, found {AllTenants.Count}");
    }

    [Fact]
    public void All715Tenants_ExactArabicFullName_ScoresMaximum()
    {
        foreach (var tenant in AllTenants)
        {
            if (string.IsNullOrWhiteSpace(tenant.name)) continue;

            int score = TextUtils.ScoreTenantMatch(tenant.name, tenant.name, tenant.house_id);
            Assert.True(score >= 1000,
                $"Tenant ID {tenant.id} '{tenant.name}' in house {tenant.house_id} failed exact match: score was {score}");
        }
    }

    [Fact]
    public void All715Tenants_NormalizedArabicFullName_MatchesWithHighConfidence()
    {
        foreach (var tenant in AllTenants)
        {
            if (string.IsNullOrWhiteSpace(tenant.name)) continue;

            // Normalized: strip diacritics, normalize hamzas and taa marbuta
            string normalized = TextUtils.NormalizeArabic(tenant.name);
            int score = TextUtils.ScoreTenantMatch(normalized, tenant.name, tenant.house_id);
            Assert.True(score >= 1000,
                $"Tenant ID {tenant.id} '{tenant.name}' failed normalized Arabic search '{normalized}': score was {score}");
        }
    }

    [Fact]
    public void All715Tenants_ArabicFirstName_MatchesEachTenant()
    {
        foreach (var tenant in AllTenants)
        {
            if (string.IsNullOrWhiteSpace(tenant.name)) continue;

            var tokens = tenant.name.Trim().Split(' ', StringSplitOptions.RemoveEmptyEntries);
            if (tokens.Length == 0) continue;

            string firstName = tokens[0];
            int score = TextUtils.ScoreTenantMatch(firstName, tenant.name, tenant.house_id);
            Assert.True(score >= 500,
                $"Tenant ID {tenant.id} '{tenant.name}' failed first-name search '{firstName}': score was {score}");
        }
    }

    [Fact]
    public void All715Tenants_TransliteratedLatinName_MatchesEachTenant()
    {
        foreach (var tenant in AllTenants)
        {
            if (string.IsNullOrWhiteSpace(tenant.name)) continue;

            string latin = TextUtils.ToLatin(tenant.name);
            int score = TextUtils.ScoreTenantMatch(latin, tenant.name, tenant.house_id);
            Assert.True(score >= 400,
                $"Tenant ID {tenant.id} '{tenant.name}' failed transliterated search '{latin}': score was {score}");
        }
    }

    [Theory]
    [InlineData("nadia")]
    [InlineData("nadiya")]
    [InlineData("nadya")]
    [InlineData("nadiah")]
    [InlineData("نادية")]
    [InlineData("ناديه")]
    [InlineData("ناديا")]
    public void NadiaSearch_MatchesBothHouse616AndSafF2456_1(string query)
    {
        // House 616: نادية ممتاز علي (ends in Taa Marbuta ة)
        int score616 = TextUtils.ScoreTenantMatch(query, "نادية ممتاز علي", "616");
        Assert.True(score616 >= 400,
            $"Expected query '{query}' to match House 616 'نادية ممتاز علي', got score {score616}");

        // House SAF F 2456_1: ناديا ميرزا أنام محمد (ends in Alif ا)
        int scoreSaf = TextUtils.ScoreTenantMatch(query, "ناديا ميرزا أنام محمد", "SAF F 2456_1");
        Assert.True(scoreSaf >= 400,
            $"Expected query '{query}' to match Safra Flats 'ناديا ميرزا أنام محمد', got score {scoreSaf}");
    }

    [Fact]
    public void FemaleAndTaaMarbutaNames_MatchTransliterationsAndVariations()
    {
        // Fatima / Fatimah / Fatma
        Assert.True(TextUtils.ScoreTenantMatch("fatima", "فاطمة أحمد حمود ناصر", "SAF F 2458_23") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("fatimah", "فاطمة أحمد حمود ناصر", "SAF F 2458_23") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("fatma", "فاطمة أحمد حمود ناصر", "SAF F 2458_23") >= 400);

        // Amina / Aminah / Ameena
        Assert.True(TextUtils.ScoreTenantMatch("amina", "أمينة محمد عبد الله محمد المطوع", "615") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("aminah", "أمينة محمد عبد الله محمد المطوع", "615") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("ameena", "أمينة محمد عبد الله محمد المطوع", "615") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("amina", "أمينة علي النياري", "SAF F 2452_1") >= 400);

        // Aisha / Aishah / Ayesha
        Assert.True(TextUtils.ScoreTenantMatch("aisha", "عائشة عبدالله ربيعة", "695") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("aishah", "عائشة عبدالله ربيعة", "695") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("ayesha", "عائشة عبدالله ربيعة", "695") >= 400);

        // Hessa / Hissa
        Assert.True(TextUtils.ScoreTenantMatch("hessa", "حصة جاسم محمد علي", "1288") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("hissa", "حصة جاسم محمد علي", "1288") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("hessa", "حصة محمد شريف", "SAF F 2452_1") >= 400);

        // Marwa / Marwah
        Assert.True(TextUtils.ScoreTenantMatch("marwa", "مروة جاسم محمد", "567") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("marwah", "مروة جاسم محمد", "567") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("marwa", "مروة صالح خليفة الصقر", "1149") >= 400);

        // Lulwa / Lolwa
        Assert.True(TextUtils.ScoreTenantMatch("lulwa", "لولوة خالد عبدالله جمعة الذوادي", "623") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("lolwa", "لولوة خالد عبدالله جمعة الذوادي", "623") >= 400);

        // Sheikha / Shaikha
        Assert.True(TextUtils.ScoreTenantMatch("sheikha", "شيخة نصيب جاسم", "769") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("shaikha", "شيخة نصيب جاسم", "769") >= 400);

        // Samira / Sameera / Samirah
        Assert.True(TextUtils.ScoreTenantMatch("samira", "سميرة عبدالله علي عنبر", "SAF F 2456_1") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("sameera", "سميرة عبدالله علي عنبر", "SAF F 2456_1") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("samirah", "سميرة عبدالله علي عنبر", "SAF F 2456_1") >= 400);

        // Munira / Muneera / Munirah
        Assert.True(TextUtils.ScoreTenantMatch("munira", "منيرة عوض مبارك عبدالله", "1154") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("muneera", "منيرة عوض مبارك عبدالله", "1154") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("munirah", "منيرة عوض مبارك عبدالله", "1154") >= 400);

        // Hamza / Hamzah
        Assert.True(TextUtils.ScoreTenantMatch("hamza", "حمزة والي محمد", "956") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("hamzah", "حمزة والي محمد", "956") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("hamza", "إبراهيم حمزة محمد محمود", "1269") >= 400);

        // Khalifa / Khalifah
        Assert.True(TextUtils.ScoreTenantMatch("khalifa", "خليفة حبيب خلف", "SAF F 2450_21") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("khalifah", "خليفة حبيب خلف", "SAF F 2452_4") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("khalifa", "هجرس خليفة محمد خليفة", "679") >= 400);

        // Juma / Jumah
        Assert.True(TextUtils.ScoreTenantMatch("juma", "جمعة سالم علي", "526") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("jumah", "جمعة سالم علي", "526") >= 400);

        // Amna / Aamna
        Assert.True(TextUtils.ScoreTenantMatch("amna", "آمنة الله بخش هاشم رحيم داد", "630") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("aamna", "آمنة الله بخش هاشم رحيم داد", "630") >= 400);
    }

    [Fact]
    public void CompoundNames_MatchJoinedAndSeparated_AcrossAllVariations()
    {
        // Abdul Rahman: split in query matching joined in tenant and split in tenant
        Assert.True(TextUtils.ScoreTenantMatch("abdul rahman", "عبدالرحمن أمحان عوض العماش", "1314") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("abdulrahman", "عبدالرحمن أمحان عوض العماش", "1314") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("abdur rahman", "عبدالرحمن أمحان عوض العماش", "1314") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("abdul rahman", "عبد الرحمن حافظ محمد أشرف", "1318") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("abdulrahman", "عبد الرحمن حافظ محمد أشرف", "1318") >= 400);

        // Abdul Aziz
        Assert.True(TextUtils.ScoreTenantMatch("abdul aziz", "عبدالعزيز حاجي رحمة الله", "637") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("abdulaziz", "عبدالعزيز حاجي رحمة الله", "637") >= 400);

        // Abdul Qadir
        Assert.True(TextUtils.ScoreTenantMatch("abdul qadir", "عبد القادر إبراهيم حمزة محمود", "1277") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("abdulqadir", "عبد القادر إبراهيم حمزة محمود", "1277") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("abdul qadir", "محمد عبد القادر السويدي", "1306") >= 400);

        // Abdullah
        Assert.True(TextUtils.ScoreTenantMatch("abdullah", "عبدالله ناجي محمد", "1261") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("abd allah", "عبد الله محمد السعد", "1273") >= 400);

        // De Souza
        Assert.True(TextUtils.ScoreTenantMatch("de souza", "مارتينو ديسوزا", "725") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("desouza", "مارتينو ديسوزا", "725") >= 400);

        // Abu Bakr
        Assert.True(TextUtils.ScoreTenantMatch("abu bakr", "أبو بكر صديق", "1347") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("abubakar", "كوتيليكات كنجومات أبوبكر", "1282") >= 400);

        // Foreign / Urdu names
        int scoreAvinash = TextUtils.ScoreTenantMatch("avinash", "أفيناش راجانيكانت جورد", "552A");
        Assert.True(scoreAvinash >= 400, $"Expected avinash score >= 400, got {scoreAvinash}");
        Assert.True(TextUtils.ScoreTenantMatch("javed akram", "جاويد أكرم محمد", "1264") >= 800);
        Assert.True(TextUtils.ScoreTenantMatch("sarfaraz nawaz", "سرفراز نواز محمد يوسف عبد الصادق رجا", "SAF F 2452_33") >= 800);
        Assert.True(TextUtils.ScoreTenantMatch("shaukat ali", "شوكت علي البلوشي", "1260") >= 800);
        Assert.True(TextUtils.ScoreTenantMatch("anwar", "محمد أنور حاجي حسن البلوشي", "1260") >= 400);
        int scoreChoudhary = TextUtils.ScoreTenantMatch("choudhary", "جاويد إقبال شودري", "1264");
        Assert.True(scoreChoudhary >= 400, $"Expected choudhary score >= 400, got {scoreChoudhary}");
        Assert.True(TextUtils.ScoreTenantMatch("chaudhry", "جاويد إقبال شودري", "1264") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("fernandes", "كارمو كاريدادي فيرنانديز", "567") >= 400);
    }

    [Fact]
    public void ShortNames_MatchWithPrecisionAndRejectCollisions()
    {
        // Ali
        Assert.True(TextUtils.ScoreTenantMatch("ali", "علي صالح أحمد", "550A") >= 400);

        // Noor
        Assert.True(TextUtils.ScoreTenantMatch("noor", "نور علي خان", "1257") >= 400);
        Assert.True(TextUtils.ScoreTenantMatch("nur", "نور علي خان", "1257") >= 400);

        // Zaid
        Assert.True(TextUtils.ScoreTenantMatch("zaid", "مصلح عيسى علي زيد", "1321") >= 400);

        // Eid
        Assert.True(TextUtils.ScoreTenantMatch("eid", "عيد مطشر الدندل", "1324") >= 400);
        Assert.Equal(0, TextUtils.ScoreTenantMatch("eid", "دعاء عادل ناجي", "608"));

        // Isa vs Aisha isolation
        Assert.True(TextUtils.ScoreTenantMatch("isa", "عيسى محمد ابراهيم", "1274") >= 400);
        Assert.Equal(0, TextUtils.ScoreTenantMatch("isa", "عائشة عبدالله ربيعة", "695"));
        Assert.True(TextUtils.ScoreTenantMatch("aisha", "عائشة عبدالله ربيعة", "695") >= 400);

        // Sami
        Assert.True(TextUtils.ScoreTenantMatch("sami", "سامي محمد ناجي الصميل", "749") >= 400);

        // Saud
        Assert.True(TextUtils.ScoreTenantMatch("saud", "عبدالله سعود الدوسري", "630") >= 400);
    }
}
