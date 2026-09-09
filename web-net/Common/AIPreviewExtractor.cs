using System.Text;
using System.Text.RegularExpressions;
using FileOrganizer.Web.Data;
using FileOrganizer.Web.Models;

namespace FileOrganizer.Web.Common;

public static class AIPreviewExtractor
{
    private static readonly (string Category, string[] Keywords)[] CategoryRules = new[]
    {
        ("05 - عقود", new[] { "عقد", "دقع", "إيجار", "راجيإ", "اتفاقية", "تأجير", "شروط العقد", "contract", "contracts", "lease", "agreement", "طرف أول", "طرف ثاني" }),
        ("06 - كهرباء وماء", new[] { "كهرباء", "ءابرهك", "ماء", "فاتورة", "ةروطاف", "فواتير", "استهلاك", "هيئة الكهرباء", "ewa", "electricity", "water", "utility", "bill", "حساب كهرباء" }),
        ("03 - أمر تخصيص", new[] { "أمر تخصيص", "تخصيص مسكن", "تخصيص وحدة", "قرار تخصيص", "تسكين", "وزارة الإسكان", "allocation", "allotment", "amar takhsees" }),
        ("04 - محضر تسليم مفتاح", new[] { "تسليم مفتاح", "محضر تسليم", "استلام مفتاح", "تسليم المسكن", "مفاتيح", "key handover", "keys" }),
        ("07 - استقطاع إيجار", new[] { "استقطاع إيجار", "استقطاع شهري", "خصم إيجار", "استقطاع", "rent deduction", "salary deduction" }),
        ("08 - وقف استقطاع بدل", new[] { "وقف استقطاع", "بدل سكن", "وقف بدل", "stop allowance", "allowance" }),
        ("10 - صيانة", new[] { "صيانة", "ةنايص", "إصلاح", "ترميم", "عطل", "تسريب", "كهربائي", "سباكة", "maintenance", "repair" }),
        ("02 - بيانات شخصية", new[] { "بطاقة هوية", "جواز سفر", "جواز", "عقد زواج", "رخصة قيادة", "cpr", "passport", "id card", "personal details" }),
        ("01 - بيانات أساسية", new[] { "بيانات أساسية", "استمارة", "إقرار", "طلب سكن", "براءة ذمة", "تقرير حالة", "basic details", "application form" }),
        ("12 - تعديلات", new[] { "تعديل", "تعديلات", "إضافة غرفة", "كراج", "بناء ملحق", "توسعة", "modification", "modifications", "renovation" }),
        ("11 - صور ومعاينات", new[] { "معاينة", "تقرير معاينة", "صور", "كشف ميداني", "inspection", "pictures", "photos" }),
        ("09 - إشعارات", new[] { "إشعار", "إنذار", "تنبيه", "إخلاء", "warning", "notice", "eviction" }),
    };

    private static readonly Dictionary<string, string> CategoryTitles = new()
    {
        { "05 - عقود", "عقد إيجار" },
        { "06 - كهرباء وماء", "فاتورة كهرباء وماء" },
        { "03 - أمر تخصيص", "أمر تخصيص مسكن" },
        { "04 - محضر تسليم مفتاح", "محضر تسليم مفتاح" },
        { "07 - استقطاع إيجار", "إشعار استقطاع إيجار" },
        { "08 - وقف استقطاع بدل", "طلب وقف استقطاع بدل سكن" },
        { "10 - صيانة", "طلب صيانة وإصلاح" },
        { "02 - بيانات شخصية", "وثيقة بيانات شخصية" },
        { "01 - بيانات أساسية", "استمارة بيانات أساسية" },
        { "12 - تعديلات", "طلب تعديلات على المسكن" },
        { "11 - صور ومعاينات", "تقرير معاينة وصور" },
        { "09 - إشعارات", "إشعار رسمي" },
        { "13 - رسائل متنوعة", "مستند رسمي" }
    };

    private static readonly Dictionary<string, int> ArabicMonths = new(StringComparer.OrdinalIgnoreCase)
    {
        { "يناير", 1 }, { "فبراير", 2 }, { "مارس", 3 }, { "أبريل", 4 },
        { "مايو", 5 }, { "يونيو", 6 }, { "يوليو", 7 }, { "أغسطس", 8 },
        { "سبتمبر", 9 }, { "أكتوبر", 10 }, { "نوفمبر", 11 }, { "ديسمبر", 12 }
    };

    public static async Task<AIPreviewResponseDto> ExtractAsync(
        byte[] pdfBytes,
        string? filename,
        string? areaId,
        string? houseId,
        IFileOrganizerRepository? repo = null)
    {
        var utf8 = Encoding.UTF8.GetString(pdfBytes);
        var latin1 = Encoding.Latin1.GetString(pdfBytes);
        var searchable = (utf8 + "\n" + latin1 + "\n" + (filename ?? "")).ToLowerInvariant();

        // 1. Page count
        var pageMatches = Regex.Matches(utf8, @"/Type\s*/Page\b");
        var pageCount = Math.Max(1, pageMatches.Count);

        // 2. Date extraction
        string? suggestedDate = null;

        // ISO format YYYY-MM-DD or YYYY/MM/DD
        var mIso = Regex.Match(searchable, @"\b(19\d{2}|20\d{2})[-/.](0?[1-9]|1[0-2])[-/.](0?[1-9]|[12]\d|3[01])\b");
        if (mIso.Success)
        {
            var y = int.Parse(mIso.Groups[1].Value);
            var m = int.Parse(mIso.Groups[2].Value);
            var d = int.Parse(mIso.Groups[3].Value);
            suggestedDate = $"{y:D4}-{m:D2}-{d:D2}";
        }

        // DMY format DD-MM-YYYY or DD/MM/YYYY
        if (suggestedDate == null)
        {
            var mDmy = Regex.Match(searchable, @"\b(0?[1-9]|[12]\d|3[01])[-/.](0?[1-9]|1[0-2])[-/.](19\d{2}|20\d{2})\b");
            if (mDmy.Success)
            {
                var d = int.Parse(mDmy.Groups[1].Value);
                var m = int.Parse(mDmy.Groups[2].Value);
                var y = int.Parse(mDmy.Groups[3].Value);
                suggestedDate = $"{y:D4}-{m:D2}-{d:D2}";
            }
        }

        // Arabic month format
        if (suggestedDate == null)
        {
            var mAr = Regex.Match(utf8, @"\b(\d{1,2})\s+(يناير|فبراير|مارس|أبريل|مايو|يونيو|يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر)\s+(\d{4})\b");
            if (mAr.Success)
            {
                var d = int.Parse(mAr.Groups[1].Value);
                var monthStr = mAr.Groups[2].Value;
                var y = int.Parse(mAr.Groups[3].Value);
                var m = ArabicMonths.GetValueOrDefault(monthStr, 1);
                suggestedDate = $"{y:D4}-{m:D2}-{d:D2}";
            }
        }

        // Check filename for year or date
        if (suggestedDate == null && !string.IsNullOrEmpty(filename))
        {
            var mFile = Regex.Match(filename, @"(\d{4})[-_](\d{2})[-_](\d{2})");
            if (mFile.Success)
            {
                suggestedDate = $"{mFile.Groups[1].Value}-{mFile.Groups[2].Value}-{mFile.Groups[3].Value}";
            }
        }

        // 3. Category extraction
        string? bestCat = null;
        int maxScore = 0;

        foreach (var (cat, keywords) in CategoryRules)
        {
            int score = 0;
            foreach (var kw in keywords)
            {
                if (searchable.Contains(kw.ToLowerInvariant()))
                {
                    score++;
                }
            }
            if (score > maxScore)
            {
                maxScore = score;
                bestCat = cat;
            }
        }

        var suggestedCategory = (maxScore > 0 && bestCat != null) ? bestCat : "13 - رسائل متنوعة";

        // 4. Suggested Title
        string? suggestedTitle = null;
        var subjectMatch = Regex.Match(utf8, @"(?:الموضوع|بشأن|subject)\s*[:/–—\-]\s*([^\n\r]+)", RegexOptions.IgnoreCase);
        if (subjectMatch.Success)
        {
            var subj = subjectMatch.Groups[1].Value.Trim();
            if (subj.Length is >= 3 and <= 80)
            {
                suggestedTitle = subj;
            }
        }

        if (string.IsNullOrEmpty(suggestedTitle))
        {
            suggestedTitle = CategoryTitles.GetValueOrDefault(suggestedCategory, "مستند رسمي");
            if (!string.IsNullOrEmpty(filename))
            {
                var stem = Path.GetFileNameWithoutExtension(filename);
                if (!string.Equals(stem, "scan", StringComparison.OrdinalIgnoreCase) &&
                    !string.Equals(stem, "document", StringComparison.OrdinalIgnoreCase) &&
                    !string.Equals(stem, "upload", StringComparison.OrdinalIgnoreCase) &&
                    !string.Equals(stem, "file", StringComparison.OrdinalIgnoreCase) &&
                    !string.Equals(stem, "test", StringComparison.OrdinalIgnoreCase))
                {
                    suggestedTitle = $"{suggestedTitle} - {stem}";
                }
            }
        }

        // 5. Clean house ID
        string? suggestedHouseId = !string.IsNullOrEmpty(houseId) ? TextUtils.ExtractHouseNumber(houseId) : null;
        if (string.IsNullOrEmpty(suggestedHouseId))
        {
            var houseMatch = Regex.Match(searchable, @"(?:منزل|بيت|شقة|house|villa|unit)\s*(?:رقم|#)?\s*(\d+)", RegexOptions.IgnoreCase);
            if (houseMatch.Success)
            {
                suggestedHouseId = houseMatch.Groups[1].Value;
            }
        }

        // 6. Tenant name suggestion
        string? suggestedTenantName = null;
        if (repo != null && !string.IsNullOrEmpty(suggestedHouseId))
        {
            try
            {
                var existingTenants = await repo.GetTenantsAsync(suggestedHouseId);
                foreach (var t in existingTenants)
                {
                    if (!string.IsNullOrWhiteSpace(t.Name) && searchable.Contains(t.Name.ToLowerInvariant()))
                    {
                        suggestedTenantName = t.Name;
                        break;
                    }
                }

                if (suggestedTenantName == null && existingTenants.Count > 0)
                {
                    suggestedTenantName = existingTenants[0].Name;
                }
            }
            catch
            {
                // Ignore DB error during preview
            }
        }

        if (string.IsNullOrEmpty(suggestedTenantName))
        {
            var tenantMatch = Regex.Match(utf8, @"(?:المستأجر|السيد|المواطن|الاسم|tenant|name)\s*[:/–—\-]\s*([^\n\r,–—\(\)]+)", RegexOptions.IgnoreCase);
            if (tenantMatch.Success)
            {
                var rawName = tenantMatch.Groups[1].Value.Trim();
                foreach (var suffix in new[] { "المحترم", "حفظه الله", "ورعاه", "وفقه الله" })
                {
                    rawName = rawName.Replace(suffix, "").Trim();
                }
                if (rawName.Length is >= 2 and <= 60)
                {
                    suggestedTenantName = rawName;
                }
            }
        }

        return new AIPreviewResponseDto
        {
            Status = "success",
            PageCount = pageCount,
            SuggestedTitle = suggestedTitle,
            SuggestedCategory = suggestedCategory,
            SuggestedDate = suggestedDate,
            SuggestedTenantName = suggestedTenantName,
            SuggestedHouseId = suggestedHouseId,
            SuggestedAreaId = areaId
        };
    }
}
