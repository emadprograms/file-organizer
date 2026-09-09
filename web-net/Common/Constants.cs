using System.Text.RegularExpressions;

namespace FileOrganizer.Web.Common;

public static class Constants
{
    public static readonly Dictionary<string, string> FolderPrefixes = new()
    {
        ["بيانات أساسية"] = "01",
        ["بيانات شخصية"] = "02",
        ["أمر تخصيص"] = "03",
        ["محضر تسليم مفتاح"] = "04",
        ["عقود"] = "05",
        ["كهرباء وماء"] = "06",
        ["استقطاع إيجار"] = "07",
        ["وقف استقطاع بدل"] = "08",
        ["إشعارات"] = "09",
        ["صيانة"] = "10",
        ["صور ومعاينات"] = "11",
        ["تعديلات"] = "12",
        ["رسائل متنوعة"] = "13",
    };

    public static readonly string[] StandardFolders = new[]
    {
        "01 - بيانات أساسية",
        "02 - بيانات شخصية",
        "03 - أمر تخصيص",
        "04 - محضر تسليم مفتاح",
        "05 - عقود",
        "06 - كهرباء وماء",
        "07 - استقطاع إيجار",
        "08 - وقف استقطاع بدل",
        "09 - إشعارات",
        "10 - صيانة",
        "11 - صور ومعاينات",
        "12 - تعديلات",
        "13 - رسائل متنوعة"
    };

    public static string FormatCategoryWithPrefix(string? rawCategory)
    {
        if (string.IsNullOrWhiteSpace(rawCategory))
            return "13 - رسائل متنوعة";

        var trimmed = rawCategory.Trim();

        // Check if already prefixed with e.g. "05 - عقود" or "05-عقود"
        if (Regex.IsMatch(trimmed, @"^\d+\s*-\s*"))
        {
            var match = Regex.Match(trimmed, @"^(\d+)\s*-\s*(.+)$");
            if (match.Success)
            {
                var num = int.Parse(match.Groups[1].Value);
                var name = match.Groups[2].Value.Trim();
                if (FolderPrefixes.TryGetValue(name, out var stdPrefix))
                {
                    return $"{stdPrefix} - {name}";
                }
                return $"{num:D2} - {name}";
            }
            return trimmed;
        }

        // Check if plain name exists in folder prefixes
        if (FolderPrefixes.TryGetValue(trimmed, out var prefix))
        {
            return $"{prefix} - {trimmed}";
        }

        return trimmed;
    }

    public static string CleanCategoryName(string? rawCategory)
    {
        if (string.IsNullOrWhiteSpace(rawCategory))
            return string.Empty;

        return Regex.Replace(rawCategory.Trim(), @"^\d+\s*-\s*", string.Empty).Trim();
    }
}
