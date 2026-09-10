using FileOrganizer.Web.Common;
using Xunit;

namespace FileOrganizer.Tests;

public class ArabicReshaperTests
{
    [Theory]
    [InlineData("عقود", "ﺩﻮﻘﻋ")]
    [InlineData("كهرباء وماء", "ﺀﺎﻣﻭ ﺀﺎﺑﺮﻬﻛ")]
    [InlineData("بيانات شخصية", "ﺔﻴﺼﺨﺷ ﺕﺎﻧﺎﻴﺑ")]
    [InlineData("أمر تخصيص", "ﺺﻴﺼﺨﺗ ﺮﻣﺃ")]
    [InlineData("محضر تسليم مفتاح", "ﺡﺎﺘﻔﻣ ﻢﻴﻠﺴﺗ ﺮﻀﺤﻣ")]
    [InlineData("استقطاع إيجار", "ﺭﺎﺠﻳﺇ ﻉﺎﻄﻘﺘﺳﺍ")]
    [InlineData("سندات قبض", "ﺾﺒﻗ ﺕﺍﺪﻨﺳ")]
    [InlineData("إشعارات", "ﺕﺍﺭﺎﻌﺷﺇ")]
    [InlineData("صيانة", "ﺔﻧﺎﻴﺻ")]
    [InlineData("صور ومعاينات", "ﺕﺎﻨﻳﺎﻌﻣﻭ ﺭﻮﺻ")]
    [InlineData("تعديلات", "ﺕﻼﻳﺪﻌﺗ")]
    [InlineData("رسائل متنوعة", "ﺔﻋﻮﻨﺘﻣ ﻞﺋﺎﺳﺭ")]
    [InlineData("عقود إيجار", "ﺭﺎﺠﻳﺇ ﺩﻮﻘﻋ")]
    public void ReshapeAndReorder_All13Categories_MatchesConnectedForms(string input, string expected)
    {
        var result = ArabicReshaper.ReshapeAndReorder(input);
        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("عقود", "ﻋﻘﻮﺩ")]
    [InlineData("كهرباء وماء", "ﻛﻬﺮﺑﺎﺀ ﻭﻣﺎﺀ")]
    [InlineData("بيانات شخصية", "ﺑﻴﺎﻧﺎﺕ ﺷﺨﺼﻴﺔ")]
    [InlineData("أمر تخصيص", "ﺃﻣﺮ ﺗﺨﺼﻴﺺ")]
    [InlineData("محضر تسليم مفتاح", "ﻣﺤﻀﺮ ﺗﺴﻠﻴﻢ ﻣﻔﺘﺎﺡ")]
    [InlineData("استقطاع إيجار", "ﺍﺳﺘﻘﻄﺎﻉ ﺇﻳﺠﺎﺭ")]
    [InlineData("سندات قبض", "ﺳﻨﺪﺍﺕ ﻗﺒﺾ")]
    [InlineData("إشعارات", "ﺇﺷﻌﺎﺭﺍﺕ")]
    [InlineData("صيانة", "ﺻﻴﺎﻧﺔ")]
    [InlineData("صور ومعاينات", "ﺻﻮﺭ ﻭﻣﻌﺎﻳﻨﺎﺕ")]
    [InlineData("تعديلات", "ﺗﻌﺪﻳﻼﺕ")]
    [InlineData("رسائل متنوعة", "ﺭﺳﺎﺋﻞ ﻣﺘﻨﻮﻋﺔ")]
    [InlineData("عقود إيجار", "ﻋﻘﻮﺩ ﺇﻳﺠﺎﺭ")]
    public void Reshape_LogicalOrder_MatchesPresentationForms(string input, string expected)
    {
        var result = ArabicReshaper.Reshape(input);
        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("05 - عقود", "ﺩﻮﻘﻋ - 05")]
    [InlineData("06 - كهرباء وماء", "ﺀﺎﻣﻭ ﺀﺎﺑﺮﻬﻛ - 06")]
    [InlineData("10 - صيانة", "ﺔﻧﺎﻴﺻ - 10")]
    [InlineData("01 - بيانات شخصية", "ﺔﻴﺼﺨﺷ ﺕﺎﻧﺎﻴﺑ - 01")]
    public void ReshapeAndReorder_WithCategoryNumberPrefix_PreservesPrefixAndShapesArabic(string input, string expected)
    {
        var result = ArabicReshaper.ReshapeAndReorder(input);
        Assert.Equal(expected, result);
    }

    [Fact]
    public void ReshapeAndReorder_EmptyOrNull_ReturnsEmpty()
    {
        Assert.Equal(string.Empty, ArabicReshaper.ReshapeAndReorder(null));
        Assert.Equal(string.Empty, ArabicReshaper.ReshapeAndReorder(""));
        Assert.Equal(string.Empty, ArabicReshaper.ReshapeAndReorder("   "));
    }

    [Fact]
    public void ReshapeAndReorder_PureAscii_ReturnsUnchanged()
    {
        var input = "Area A - House 100";
        var result = ArabicReshaper.ReshapeAndReorder(input);
        Assert.Equal(input, result);
    }
}
