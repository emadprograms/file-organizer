using System.Text;
using System.Text.RegularExpressions;

namespace FileOrganizer.Web.Common;

/// <summary>
/// Provides zero-dependency contextual shaping and bidirectional visual reordering
/// for Arabic text rendering in PDF engines (such as PDFSharpCore).
/// </summary>
public static class ArabicReshaper
{
    private enum JoiningType
    {
        NonJoining,
        RightJoining,
        DualJoining
    }

    private readonly struct GlyphForms
    {
        public char Isolated { get; }
        public char Final { get; }
        public char Initial { get; }
        public char Medial { get; }
        public JoiningType Type { get; }

        public GlyphForms(char isolated, char final, char initial, char medial, JoiningType type)
        {
            Isolated = isolated;
            Final = final;
            Initial = initial;
            Medial = medial;
            Type = type;
        }

        public GlyphForms(char isolated, char final, JoiningType type)
            : this(isolated, final, '\0', '\0', type)
        {
        }

        public GlyphForms(char isolated, JoiningType type)
            : this(isolated, '\0', '\0', '\0', type)
        {
        }
    }

    // Mapping table for standard Arabic letters to Unicode Presentation Forms-B (\uFE80 - \uFEFC)
    private static readonly Dictionary<char, GlyphForms> ArabicLetters = new()
    {
        // Hamza
        ['\u0621'] = new GlyphForms('\uFE80', JoiningType.NonJoining), // ء

        // Alef with Madda Above
        ['\u0622'] = new GlyphForms('\uFE81', '\uFE82', JoiningType.RightJoining), // آ

        // Alef with Hamza Above
        ['\u0623'] = new GlyphForms('\uFE83', '\uFE84', JoiningType.RightJoining), // أ

        // Waw with Hamza Above
        ['\u0624'] = new GlyphForms('\uFE85', '\uFE86', JoiningType.RightJoining), // ؤ

        // Alef with Hamza Below
        ['\u0625'] = new GlyphForms('\uFE87', '\uFE88', JoiningType.RightJoining), // إ

        // Yeh with Hamza Above
        ['\u0626'] = new GlyphForms('\uFE89', '\uFE8A', '\uFE8B', '\uFE8C', JoiningType.DualJoining), // ئ

        // Alef
        ['\u0627'] = new GlyphForms('\uFE8D', '\uFE8E', JoiningType.RightJoining), // ا

        // Beh
        ['\u0628'] = new GlyphForms('\uFE8F', '\uFE90', '\uFE91', '\uFE92', JoiningType.DualJoining), // ب

        // Teh Marbuta
        ['\u0629'] = new GlyphForms('\uFE93', '\uFE94', JoiningType.RightJoining), // ة

        // Teh
        ['\u062A'] = new GlyphForms('\uFE95', '\uFE96', '\uFE97', '\uFE98', JoiningType.DualJoining), // ت

        // Theh
        ['\u062B'] = new GlyphForms('\uFE99', '\uFE9A', '\uFE9B', '\uFE9C', JoiningType.DualJoining), // ث

        // Jeem
        ['\u062C'] = new GlyphForms('\uFE9D', '\uFE9E', '\uFE9F', '\uFEA0', JoiningType.DualJoining), // ج

        // Hah
        ['\u062D'] = new GlyphForms('\uFEA1', '\uFEA2', '\uFEA3', '\uFEA4', JoiningType.DualJoining), // ح

        // Khah
        ['\u062E'] = new GlyphForms('\uFEA5', '\uFEA6', '\uFEA7', '\uFEA8', JoiningType.DualJoining), // خ

        // Dal
        ['\u062F'] = new GlyphForms('\uFEA9', '\uFEAA', JoiningType.RightJoining), // د

        // Thal
        ['\u0630'] = new GlyphForms('\uFEAB', '\uFEAC', JoiningType.RightJoining), // ذ

        // Reh
        ['\u0631'] = new GlyphForms('\uFEAD', '\uFEAE', JoiningType.RightJoining), // ر

        // Zain
        ['\u0632'] = new GlyphForms('\uFEAF', '\uFEB0', JoiningType.RightJoining), // ز

        // Seen
        ['\u0633'] = new GlyphForms('\uFEB1', '\uFEB2', '\uFEB3', '\uFEB4', JoiningType.DualJoining), // س

        // Sheen
        ['\u0634'] = new GlyphForms('\uFEB5', '\uFEB6', '\uFEB7', '\uFEB8', JoiningType.DualJoining), // ش

        // Sad
        ['\u0635'] = new GlyphForms('\uFEB9', '\uFEBA', '\uFEBB', '\uFEBC', JoiningType.DualJoining), // ص

        // Dad
        ['\u0636'] = new GlyphForms('\uFEBD', '\uFEBE', '\uFEBF', '\uFEC0', JoiningType.DualJoining), // ض

        // Tah
        ['\u0637'] = new GlyphForms('\uFEC1', '\uFEC2', '\uFEC3', '\uFEC4', JoiningType.DualJoining), // ط

        // Zah
        ['\u0638'] = new GlyphForms('\uFEC5', '\uFEC6', '\uFEC7', '\uFEC8', JoiningType.DualJoining), // ظ

        // Ain
        ['\u0639'] = new GlyphForms('\uFEC9', '\uFECA', '\uFECB', '\uFECC', JoiningType.DualJoining), // ع

        // Ghain
        ['\u063A'] = new GlyphForms('\uFECD', '\uFECE', '\uFECF', '\uFED0', JoiningType.DualJoining), // غ

        // Tatweel
        ['\u0640'] = new GlyphForms('\u0640', '\u0640', '\u0640', '\u0640', JoiningType.DualJoining), // ـ

        // Feh
        ['\u0641'] = new GlyphForms('\uFED1', '\uFED2', '\uFED3', '\uFED4', JoiningType.DualJoining), // ف

        // Qaf
        ['\u0642'] = new GlyphForms('\uFED5', '\uFED6', '\uFED7', '\uFED8', JoiningType.DualJoining), // ق

        // Kaf
        ['\u0643'] = new GlyphForms('\uFED9', '\uFEDA', '\uFEDB', '\uFEDC', JoiningType.DualJoining), // ك

        // Lam
        ['\u0644'] = new GlyphForms('\uFEDD', '\uFEDE', '\uFEDF', '\uFEE0', JoiningType.DualJoining), // ل

        // Meem
        ['\u0645'] = new GlyphForms('\uFEE1', '\uFEE2', '\uFEE3', '\uFEE4', JoiningType.DualJoining), // م

        // Noon
        ['\u0646'] = new GlyphForms('\uFEE5', '\uFEE6', '\uFEE7', '\uFEE8', JoiningType.DualJoining), // ن

        // Heh
        ['\u0647'] = new GlyphForms('\uFEE9', '\uFEEA', '\uFEEB', '\uFEEC', JoiningType.DualJoining), // ه

        // Waw
        ['\u0648'] = new GlyphForms('\uFEED', '\uFEEE', JoiningType.RightJoining), // و

        // Alef Maksura
        ['\u0649'] = new GlyphForms('\uFEEF', '\uFEF0', JoiningType.RightJoining), // ى

        // Yeh
        ['\u064A'] = new GlyphForms('\uFEF1', '\uFEF2', '\uFEF3', '\uFEF4', JoiningType.DualJoining)  // ي
    };

    /// <summary>
    /// Checks if a character can connect to a preceding letter (from its right side).
    /// </summary>
    private static bool CanConnectBefore(char c)
    {
        if (ArabicLetters.TryGetValue(c, out var forms))
        {
            return forms.Type == JoiningType.RightJoining || forms.Type == JoiningType.DualJoining;
        }
        return false;
    }

    /// <summary>
    /// Checks if a character can connect to a following letter (from its left side).
    /// </summary>
    private static bool CanConnectAfter(char c)
    {
        if (ArabicLetters.TryGetValue(c, out var forms))
        {
            return forms.Type == JoiningType.DualJoining;
        }
        return false;
    }

    /// <summary>
    /// Resolves Lam-Alef ligatures (لا, لأ, لإ, لآ) in Isolated or Final form.
    /// </summary>
    private static bool TryGetLamAlef(char alefChar, bool connectedBefore, out char ligature)
    {
        switch (alefChar)
        {
            case '\u0622': // آ
                ligature = connectedBefore ? '\uFEF6' : '\uFEF5';
                return true;
            case '\u0623': // أ
                ligature = connectedBefore ? '\uFEF8' : '\uFEF7';
                return true;
            case '\u0625': // إ
                ligature = connectedBefore ? '\uFEFA' : '\uFEF9';
                return true;
            case '\u0627': // ا
                ligature = connectedBefore ? '\uFEFC' : '\uFEFB';
                return true;
            default:
                ligature = '\0';
                return false;
        }
    }

    /// <summary>
    /// Contextually shapes Arabic characters into connected cursive presentation forms.
    /// </summary>
    public static string Reshape(string? input)
    {
        if (string.IsNullOrEmpty(input))
            return string.Empty;

        var sb = new StringBuilder(input.Length);
        bool prevConnectsForward = false;

        for (int i = 0; i < input.Length; i++)
        {
            char c = input[i];

            // Check for Lam-Alef ligatures (لا, لأ, لإ, لآ)
            if (c == '\u0644' && i + 1 < input.Length && TryGetLamAlef(input[i + 1], prevConnectsForward, out char lamAlef))
            {
                sb.Append(lamAlef);
                i++; // Skip the combined Alef
                prevConnectsForward = false; // Ligature ends in Alef, which never connects forward
                continue;
            }

            if (!ArabicLetters.TryGetValue(c, out var forms))
            {
                // Non-Arabic character (space, digit, Latin, punctuation, etc.)
                sb.Append(c);
                prevConnectsForward = false;
                continue;
            }

            if (forms.Type == JoiningType.NonJoining)
            {
                sb.Append(forms.Isolated);
                prevConnectsForward = false;
                continue;
            }

            bool connectsBefore = prevConnectsForward && CanConnectBefore(c);

            // Look ahead to check if next character connects backward
            bool connectsAfter = false;
            if (forms.Type == JoiningType.DualJoining && i + 1 < input.Length)
            {
                char nextC = input[i + 1];
                connectsAfter = CanConnectBefore(nextC);
            }

            if (forms.Type == JoiningType.DualJoining)
            {
                if (connectsBefore && connectsAfter)
                    sb.Append(forms.Medial);
                else if (connectsBefore)
                    sb.Append(forms.Final);
                else if (connectsAfter)
                    sb.Append(forms.Initial);
                else
                    sb.Append(forms.Isolated);

                prevConnectsForward = true;
            }
            else // RightJoining
            {
                if (connectsBefore)
                    sb.Append(forms.Final);
                else
                    sb.Append(forms.Isolated);

                prevConnectsForward = false;
            }
        }

        return sb.ToString();
    }

    /// <summary>
    /// Reverses Arabic text segments and preserves LTR runs (numbers, Latin)
    /// so the string flows naturally right-to-left when drawn by LTR rendering engines.
    /// </summary>
    public static string ReorderBiDi(string? text)
    {
        if (string.IsNullOrEmpty(text))
            return string.Empty;

        bool hasArabic = false;
        foreach (char ch in text)
        {
            if (IsArabic(ch))
            {
                hasArabic = true;
                break;
            }
        }

        if (!hasArabic)
            return text;

        // Split text into runs of (digits | latin) vs other characters
        var parts = Regex.Split(text, @"([0-9]+|[a-zA-Z]+)");
        var sb = new StringBuilder(text.Length);

        for (int i = parts.Length - 1; i >= 0; i--)
        {
            var part = parts[i];
            if (string.IsNullOrEmpty(part))
                continue;

            if (Regex.IsMatch(part, @"^[0-9]+$") || Regex.IsMatch(part, @"^[a-zA-Z]+$"))
            {
                sb.Append(part);
            }
            else
            {
                for (int j = part.Length - 1; j >= 0; j--)
                {
                    sb.Append(MirrorChar(part[j]));
                }
            }
        }

        return sb.ToString();
    }

    /// <summary>
    /// Contextually shapes Arabic characters and visually reorders them for LTR PDF rendering.
    /// </summary>
    public static string ReshapeAndReorder(string? input)
    {
        if (string.IsNullOrWhiteSpace(input))
            return string.Empty;

        var reshaped = Reshape(input);
        return ReorderBiDi(reshaped);
    }

    private static char MirrorChar(char ch) => ch switch
    {
        '(' => ')',
        ')' => '(',
        '[' => ']',
        ']' => '[',
        '{' => '}',
        '}' => '{',
        '<' => '>',
        '>' => '<',
        _ => ch
    };

    private static bool IsArabic(char ch) =>
        (ch >= '\u0600' && ch <= '\u06FF') ||
        (ch >= '\u0750' && ch <= '\u077F') ||
        (ch >= '\uFB50' && ch <= '\uFDFF') ||
        (ch >= '\uFE70' && ch <= '\uFEFF');
}
