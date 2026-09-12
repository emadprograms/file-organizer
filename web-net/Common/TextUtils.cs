using System.Text;
using System.Text.RegularExpressions;

namespace FileOrganizer.Web.Common;

public static class TextUtils
{
    private static readonly Dictionary<char, string> ArabicToEnglishMap = new()
    {
        ['ا'] = "", ['أ'] = "", ['إ'] = "", ['آ'] = "", ['ى'] = "",
        ['ب'] = "b", ['ت'] = "t", ['ث'] = "s", ['ج'] = "j", ['ح'] = "h", ['خ'] = "k",
        ['د'] = "d", ['ذ'] = "z", ['ر'] = "r", ['ز'] = "z", ['س'] = "s", ['ش'] = "s",
        ['ص'] = "s", ['ض'] = "d", ['ط'] = "t", ['ظ'] = "z", ['ع'] = "", ['غ'] = "g",
        ['ف'] = "f", ['ق'] = "k", ['ك'] = "k", ['ل'] = "l", ['م'] = "m", ['ن'] = "n",
        ['ه'] = "h", ['ة'] = "h", ['W'] = "w", ['و'] = "", ['ي'] = "", ['ئ'] = "", ['ؤ'] = "w", ['ء'] = ""
    };

    public static string CleanArticle(string? word)
    {
        if (string.IsNullOrWhiteSpace(word))
            return string.Empty;

        var w = word.Trim().ToLowerInvariant();
        if (w.StartsWith("al-") || w.StartsWith("al "))
            return w[3..].Trim();
        if (w.StartsWith("al") && w.Length > 4)
            return w[2..].Trim();
        if (w.StartsWith("ال") && w.Length > 3)
            return w[2..].Trim();
        return w;
    }

    public static string PhoneticNormalize(string? text)
    {
        if (string.IsNullOrWhiteSpace(text))
            return string.Empty;

        var lower = text.ToLowerInvariant().Trim();

        // Distinguish Arabic 'و' as consonant 'W' vs long vowel (uu/oo)
        // 1. Beginning of word (^و or [ -]و) -> consonant W (وسيم, وليد)
        lower = Regex.Replace(lower, @"(^|[\s\-])و", "$1W");
        // 2. Adjacent to Alif (او or وا) -> consonant W (جاويد, فواز, نواز, رضوان)
        lower = Regex.Replace(lower, @"[اآإأ][وؤ]|[وؤ][اآإأ]", "W");
        // 3. Waw followed by Yaa (وي as in سويدي, برويز, كويت, رويلي) -> consonant W
        lower = Regex.Replace(lower, @"[وؤ]ي", "Wy");
        // 4. Word-initial Ayn followed by Waw (^عو as in عوض, عواض) -> consonant W
        lower = Regex.Replace(lower, @"(^|[\s\-])ع[وؤ]", "$1W");
        // 5. Names on pattern Anwar/Munawwar ([اآإأ]نو, منو, أرو) -> consonant W
        lower = Regex.Replace(lower, @"(^|[\s\-])([اآإأ]ن|[اآإأ]ر|من)[وؤ]", "$1$2W");

        // In English: diphthong ow/aw before consonant or end of token -> vowel (e.g. showkat -> shokat)
        lower = Regex.Replace(lower, @"([oa])w(?=[^aeiouy\s]|$)", "$1");

        // Replace English digraphs prior to Arabic mapping to prevent Arabic س + ح (Seen + Haa) from collapsing as English "sh"
        lower = lower.Replace("v", "w");
        lower = lower.Replace("th", "s");
        lower = lower.Replace("kh", "k").Replace("gh", "g").Replace("sh", "s");
        lower = lower.Replace("dh", "z").Replace("zh", "z");
        lower = lower.Replace("ph", "f").Replace("p", "b");
        lower = lower.Replace("ck", "k").Replace("c", "k").Replace("q", "k");

        var sb = new StringBuilder();
        foreach (var ch in lower)
        {
            if (ArabicToEnglishMap.TryGetValue(ch, out var mapped))
            {
                sb.Append(mapped);
            }
            else
            {
                sb.Append(ch);
            }
        }

        var res = sb.ToString();
        res = Regex.Replace(res, "[aeiouy]", "");
        res = Regex.Replace(res, @"(.)\1+", "$1");
        return res.Trim();
    }

    public static string StripArabicDiacritics(string? text)
    {
        if (string.IsNullOrWhiteSpace(text))
            return string.Empty;

        return Regex.Replace(text, @"[\u064B-\u065F\u0670\u0640]", "");
    }

    public static string NormalizeArabic(string? text)
    {
        if (string.IsNullOrWhiteSpace(text))
            return string.Empty;

        var s = StripArabicDiacritics(text).Trim().ToLowerInvariant();
        s = Regex.Replace(s, "[أإآٱ]", "ا");
        s = s.Replace('ة', 'ه');
        s = s.Replace('ى', 'ي');
        return s;
    }

    public static List<string> GetArabicSearchVariants(string? query)
    {
        if (string.IsNullOrWhiteSpace(query))
            return new List<string>();

        var clean = StripArabicDiacritics(query).Trim().ToLowerInvariant();
        var variants = new HashSet<string> { clean };

        // 1. Alef with Hamza <-> bare Alef
        if (clean.IndexOfAny(new[] { 'أ', 'إ', 'آ', 'ٱ' }) >= 0)
        {
            variants.Add(Regex.Replace(clean, "[أإآٱ]", "ا"));
        }
        else if (clean.Contains('ا'))
        {
            variants.Add(Regex.Replace(clean, @"(^|[\s\-])ا", "$1أ"));
            variants.Add(Regex.Replace(clean, @"(^|[\s\-])ا", "$1إ"));
        }

        // 2. Taa Marbuta <-> Haa
        if (clean.EndsWith('ة'))
            variants.Add(clean[..^1] + "ه");
        else if (clean.EndsWith('ه'))
            variants.Add(clean[..^1] + "ة");

        // 3. Alif Maqsura <-> Yaa
        if (clean.EndsWith('ى'))
            variants.Add(clean[..^1] + "ي");
        else if (clean.EndsWith('ي'))
            variants.Add(clean[..^1] + "ى");

        return variants.Where(v => !string.IsNullOrWhiteSpace(v)).Distinct().ToList();
    }

    public static int ScoreTenantMatch(string query, string tenantName, string houseId)
    {
        if (string.IsNullOrWhiteSpace(query) || string.IsNullOrWhiteSpace(tenantName))
            return 0;

        var qClean = StripArabicDiacritics(query);
        var tClean = StripArabicDiacritics(tenantName);
        var qLow = qClean.Trim().ToLowerInvariant();
        var tLow = tClean.Trim().ToLowerInvariant();
        var hLow = houseId.Trim().ToLowerInvariant();

        var qNormAr = NormalizeArabic(qLow);
        var tNormAr = NormalizeArabic(tLow);

        // 1. Direct full substring match (raw or normalized Arabic)
        if (tLow.Contains(qLow) || (!string.IsNullOrEmpty(qNormAr) && tNormAr.Contains(qNormAr)))
            return 1000 + (qLow.Length * 10);
        if (hLow.Contains(qLow))
            return 900;

        var qWords = qLow.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        var tWords = tLow.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        if (qWords.Length == 0 || tWords.Length == 0)
            return 0;

        int matchedWords = 0;
        int totalScore = 0;

        for (int qi = 0; qi < qWords.Length; qi++)
        {
            var qw = qWords[qi];
            var qwClean = CleanArticle(qw);
            var qwNorm = PhoneticNormalize(qwClean);
            var qwLatin = NormalizeTranslit(qwClean);
            var qwNormAr = NormalizeArabic(qwClean);
            int bestWordScore = 0;

            for (int ti = 0; ti < tWords.Length; ti++)
            {
                var tw = tWords[ti];
                var twClean = CleanArticle(tw);
                var twLatin = NormalizeTranslit(ToLatin(twClean));
                var twNormAr = NormalizeArabic(twClean);

                // Exact word match
                if (qw == tw || (!string.IsNullOrEmpty(qwClean) && qwClean == twClean) ||
                    (!string.IsNullOrEmpty(qwNormAr) && qwNormAr == twNormAr))
                {
                    int s = 500;
                    if (ti == 0 && qi == 0) s += 50;
                    bestWordScore = Math.Max(bestWordScore, s);
                }
                // Prefix match (e.g. "khal" -> "khalil")
                else if (((tw.StartsWith(qw) || (!string.IsNullOrEmpty(qwClean) && twClean.StartsWith(qwClean))) && qwClean.Length >= 3) ||
                         ((!string.IsNullOrEmpty(qwNormAr) && twNormAr.StartsWith(qwNormAr)) && qwNormAr.Length >= 3))
                {
                    int s = 300;
                    if (ti == 0 && qi == 0) s += 30;
                    bestWordScore = Math.Max(bestWordScore, s);
                }
                // Substring word match
                else if (tw.Contains(qw) || (!string.IsNullOrEmpty(qwClean) && twClean.Contains(qwClean)) ||
                         (!string.IsNullOrEmpty(qwNormAr) && twNormAr.Contains(qwNormAr)))
                {
                    bestWordScore = Math.Max(bestWordScore, 250);
                }
                else
                {
                    // Phonetic word match
                    var twNorm = PhoneticNormalize(twClean);

                    if (!string.IsNullOrEmpty(qwNorm) && !string.IsNullOrEmpty(twNorm))
                    {
                        bool isPhoneticMatch = (qwNorm == twNorm) ||
                            (qwNorm.Contains('z') && qwNorm.Replace("z", "d") == twNorm);

                        if (isPhoneticMatch)
                        {
                            int s = 400;
                            if (ti == 0 && qi == 0) s += 50;
                            if (!string.IsNullOrEmpty(qwLatin) && !string.IsNullOrEmpty(twLatin))
                            {
                                if (qwLatin == twLatin)
                                    s += 100;
                                else if (qwLatin[0] == twLatin[0])
                                    s += 30;
                            }
                            bestWordScore = Math.Max(bestWordScore, s);
                        }
                        else if (qwNorm.Length >= 3 && twNorm.StartsWith(qwNorm))
                        {
                            bestWordScore = Math.Max(bestWordScore, 200);
                        }
                    }
                }

                // Compound token pair check (e.g. "abdullah" matching "عبد" + "الله")
                if (ti + 1 < tWords.Length)
                {
                    var twPair = twClean + " " + CleanArticle(tWords[ti + 1]);
                    var twPairNorm = PhoneticNormalize(twPair).Replace(" ", "");
                    bool isCompoundMatch = (qwNorm == twPairNorm) ||
                        (!string.IsNullOrEmpty(qwNorm) && qwNorm.Contains('z') && qwNorm.Replace("z", "d") == twPairNorm);

                    if (!string.IsNullOrEmpty(qwNorm) && qwNorm.Length >= 4 && isCompoundMatch)
                    {
                        int s = 450;
                        if (ti == 0 && qi == 0) s += 50;
                        bestWordScore = Math.Max(bestWordScore, s);
                    }
                }
            }

            if (bestWordScore > 0)
            {
                matchedWords++;
                totalScore += bestWordScore;
            }
        }

        if (matchedWords == qWords.Length)
            return totalScore;

        return 0;
    }

    private static readonly Dictionary<char, string> ArabicTranslitMap = new()
    {
        ['ا'] = "a", ['أ'] = "a", ['إ'] = "i", ['آ'] = "aa", ['ى'] = "a",
        ['ب'] = "b", ['ت'] = "t", ['ث'] = "th", ['ج'] = "j", ['ح'] = "h", ['خ'] = "kh",
        ['د'] = "d", ['ذ'] = "dh", ['ر'] = "r", ['ز'] = "z", ['س'] = "s", ['ش'] = "sh",
        ['ص'] = "s", ['ض'] = "d", ['ط'] = "t", ['ظ'] = "dh", ['ع'] = "a", ['غ'] = "gh",
        ['ف'] = "f", ['ق'] = "q", ['ك'] = "k", ['ل'] = "l", ['م'] = "m", ['ن'] = "n",
        ['ه'] = "h", ['ة'] = "h", ['و'] = "w", ['ي'] = "y", ['ئ'] = "y", ['ؤ'] = "w", ['ء'] = ""
    };

    public static string ToLatin(string? text)
    {
        if (string.IsNullOrWhiteSpace(text)) return string.Empty;
        var lower = text.ToLowerInvariant();
        var sb = new StringBuilder();
        foreach (var ch in lower)
        {
            if (ArabicTranslitMap.TryGetValue(ch, out var mapped))
                sb.Append(mapped);
            else
                sb.Append(ch);
        }
        return sb.ToString();
    }

    public static string NormalizeTranslit(string? text)
    {
        if (string.IsNullOrWhiteSpace(text)) return string.Empty;
        var w = text.ToLowerInvariant();
        w = Regex.Replace(w, "ee|ea|ey|ie|i", "y");
        w = Regex.Replace(w, "oo|ou|u", "w");
        w = Regex.Replace(w, "aa", "a");
        w = w.Replace("v", "w");
        return w;
    }

    public static double Similarity(string s, string t)
    {
        if (string.IsNullOrEmpty(s) && string.IsNullOrEmpty(t)) return 1.0;
        if (string.IsNullOrEmpty(s) || string.IsNullOrEmpty(t)) return 0.0;

        int n = s.Length;
        int m = t.Length;
        int[,] d = new int[n + 1, m + 1];

        for (int i = 0; i <= n; d[i, 0] = i++) { }
        for (int j = 0; j <= m; d[0, j] = j++) { }

        for (int i = 1; i <= n; i++)
        {
            for (int j = 1; j <= m; j++)
            {
                int cost = (t[j - 1] == s[i - 1]) ? 0 : 1;
                d[i, j] = Math.Min(
                    Math.Min(d[i - 1, j] + 1, d[i, j - 1] + 1),
                    d[i - 1, j - 1] + cost
                );
            }
        }

        int maxLen = Math.Max(n, m);
        return 1.0 - ((double)d[n, m] / maxLen);
    }

    public static string ExtractHouseNumber(string houseId)
    {
        if (string.IsNullOrWhiteSpace(houseId))
            return string.Empty;

        if (houseId.Contains(" - "))
        {
            return houseId.Split(" - ")[0].Trim();
        }

        return houseId.Trim();
    }

    public static (int Years, string DurationStrAr) FormatArabicDuration(string startDateStr, string? endDateStr)
    {
        if (string.IsNullOrWhiteSpace(startDateStr) || startDateStr.Length < 4)
            return (0, string.Empty);

        if (!DateTime.TryParse(startDateStr.Length >= 10 ? startDateStr[..10] : startDateStr, out var startDate))
        {
            if (int.TryParse(startDateStr[..4], out var parsedYear))
                startDate = new DateTime(parsedYear, 1, 1);
            else
                return (0, string.Empty);
        }

        bool isActive;
        DateTime endDate;
        if (string.IsNullOrWhiteSpace(endDateStr) || endDateStr.Trim().ToLower() == "present")
        {
            endDate = DateTime.Today;
            isActive = true;
        }
        else if (DateTime.TryParse(endDateStr.Length >= 10 ? endDateStr[..10] : endDateStr, out var parsedEnd))
        {
            endDate = parsedEnd;
            isActive = false;
        }
        else
        {
            endDate = DateTime.Today;
            isActive = false;
        }

        int days = Math.Max((int)(endDate - startDate).TotalDays, 0);
        int yearsInt = (int)Math.Round(days / 365.25);
        int startYr = startDate.Year;

        string durStr;
        if (isActive)
        {
            if (yearsInt <= 0)
                durStr = $"بدء الإيجار {startYr} (مستمر منذ أقل من سنة)";
            else if (yearsInt == 1)
                durStr = $"بدء الإيجار {startYr} (مستمر منذ سنة واحدة)";
            else if (yearsInt == 2)
                durStr = $"بدء الإيجار {startYr} (مستمر منذ سنتين)";
            else if (yearsInt >= 3 && yearsInt <= 10)
                durStr = $"بدء الإيجار {startYr} (مستمر منذ {yearsInt} سنوات)";
            else
                durStr = $"بدء الإيجار {startYr} (مستمر منذ {yearsInt} سنة)";
        }
        else
        {
            int endYr = endDate.Year;
            if (yearsInt <= 0)
                durStr = $"فترة الإيجار: {startYr} (أقل من سنة)";
            else if (yearsInt == 1)
                durStr = $"فترة الإيجار: {startYr} – {endYr} (سنة واحدة)";
            else if (yearsInt == 2)
                durStr = $"فترة الإيجار: {startYr} – {endYr} (سنتان)";
            else if (yearsInt >= 3 && yearsInt <= 10)
                durStr = $"فترة الإيجار: {startYr} – {endYr} ({yearsInt} سنوات)";
            else
                durStr = $"فترة الإيجار: {startYr} – {endYr} ({yearsInt} سنة)";
        }

        return (yearsInt, durStr);
    }

    public static (int Years, string TimespanStrAr) FormatArabicTimespan(string? oldestStr, string? newestStr)
    {
        if (string.IsNullOrWhiteSpace(oldestStr) || string.IsNullOrWhiteSpace(newestStr))
            return (0, "لا توجد وثائق مسجلة");

        if (!DateTime.TryParse(oldestStr.Length >= 10 ? oldestStr[..10] : oldestStr, out var d1) ||
            !DateTime.TryParse(newestStr.Length >= 10 ? newestStr[..10] : newestStr, out var d2))
        {
            return (0, $"من {oldestStr} إلى {newestStr}");
        }

        if (d1 > d2)
        {
            var temp = d1;
            d1 = d2;
            d2 = temp;
        }

        int totalDays = (int)(d2 - d1).TotalDays;
        int years = totalDays > 180 ? Math.Max((int)Math.Round(totalDays / 365.25), 1) : 0;
        int y1 = d1.Year;
        int y2 = d2.Year;

        if (y1 == y2)
            return (1, $"سجلات عام {y1}");

        if (years <= 1)
            return (1, $"من {y1} إلى {y2} (سنة واحدة)");
        else if (years == 2)
            return (2, $"من {y1} إلى {y2} (سنتان)");
        else if (years >= 3 && years <= 10)
            return (years, $"من {y1} إلى {y2} ({years} سنوات)");
        else
            return (years, $"من {y1} إلى {y2} ({years} سنة)");
    }
}
