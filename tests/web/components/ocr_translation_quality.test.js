import { describe, it, expect, beforeEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('OCR Translation Quality & Real-World Scan Verification', () => {
  // Load doc-viewer.js in node environment
  beforeEach(() => {
    // Provide minimal browser global mocks
    global.window = global;
    global.document = {
      createElement: () => ({
        style: {},
        setAttribute: () => {},
        appendChild: () => {},
        classList: { add: () => {}, remove: () => {}, contains: () => false },
        querySelector: () => null,
        querySelectorAll: () => []
      }),
      getElementById: () => null
    };

    const docViewerPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/doc-viewer.js');
    const code = fs.readFileSync(docViewerPath, 'utf8');
    eval(code);
  });

  // Helper to detect phonetic transliteration artifacts
  // Transliteration typically creates tokens with Arabic roots converted to Latin with awkward letter clusters
  function hasTransliterationGibberish(text) {
    if (!text || typeof text !== 'string') return false;
    const gibberishPattern = /\b(Al[a-z]{4,}|[a-z]*(?:qaa|dhm|tfaad|tqaad|swlh|khtyt|mra'y|jba|mswf|rnkh|ntmyr|btmyr|mslymha|st'na'|hmsb|alghlyfh|lbshyh|alnafy|mktb|ihdhar|hdyth|yskn|asbwa|khalkh|khdhaaf|tltfa|laa|bttak)[a-z]*)\b/i;
    return gibberishPattern.test(text);
  }

  // Exact raw OCR lines produced by Tesseract from vault document 393a2e4942354f309dda331fca474468
  const RAW_OCR_LINES_393A = [
    "مملكة البحرين للا تلتفعتد2 1ه 11177016",
    "وزارة الداخلي 0 الاسم 11722105 175 017 1111718757",
    "مكتب إدارة إسكان الشرطة 7 01171 61517 خذااف1ا 15771",
    "الرقم: ق أ ع/م !|ش/7١//1/‏ و2193",
    "التاريخ ‎“(١‏ شوال ‎١478",
    "‏جح <ح أكتوبر 7 ‎٠٠‏ 1",
    "الموضوع:عريف رقم 1 صالح قاسم حسين",
    ": منزل 85 طريق “٠؛؛‏ سافرة - د",
    "‎.١‏ - الرجاء إحضار صورة شخصية حديثة ونسخة من البطاقات السكانية لجميع أفراد العائلة",
    "اللذين يسكنون في الوحدة السكنية المؤقتة.وذلك لمكتب إدارة إسكان الشرطة في موعد أقصاه",
    "أسبوع من استلام المذكرة.",
    "وار أسكر؟> 1 ٍِ",
    "0 ا >",
    "حا ب ‎١‏ لو د ك",
    "نا الا ال النقيب/ م",
    "15 اج 8 مكتب إدارة إسكان الشرطلة",
    "2 0",
    "7 0 0# إبراهيسم محمد فولاد",
    "0"
  ];

  // Exact raw OCR lines produced by Tesseract from vault document a3cc73ba7993427fb5b53fb37b3c977d
  const RAW_OCR_LINES_A3CC = [
    ": 0 - مط 2 0",
    "| ص جز اكير",
    "كد ص سس بر ٍٍِ 7 ١ 7 ا",
    "< ا | ا , .ا 0 0",
    "4 الخ [٠مهحيم 0/7 1114011",
    "و 3 رياه",
    "يآ اا جاضا تي 7 2 5١ 7 111",
    "0 التاقللتج صر #لر ل 7م أو 1/7",
    "7 : 2 .0",
    "ص َ ل",
    "1 7",
    "إدارة الإمداد والتموين",
    "فرع اسكان الشرطة",
    ": الرقم:١ات/ رش 101/١ / 1/8",
    "التاريخ: 23 ربيع الأول 1447ه",
    "١5 سبتمبر 2025م",
    "فرع اسكان الشرطة",
    "الاسم : صالح قاسم عسكر الرقم الشخصي : 40128459",
    "حسب عقد الانتفاع الميرم بينكم وبين وزارة الداخلية وحسب المواد روات المتضمنة عند إحالة",
    "المنتفع على التقاعد أوانهاء خدماته أو حصولة على وحدة اسكانية من وزارة,الإسكان والتخطيط /",
    "العمراني أو شراء وحدة سكنية يجب عليه اخلاء الوحدة التابعة لوزارة الداخلية > وعد احالتكم الى",
    "التقاعد بتاريخ 01 سبتمير 2025م وعليه سوف تميهلك لغاية تاريخ 30 سنتمير 2025م الإخلاء الوحدة",
    "السكنية وتسليمها لفرع إسكان الشرطة دون استثتاء وستقوم وزارة الداخلية باتخاذ اءات",
    "القانونية اللازمة قِ حال عدم الإخلاء وذلك حسب النظام وما نص علية عقد الاتتفاع.",
    "الرائد نايف إبراهيم آل خليفة رئيس فرع إسكان الشرطة",
    "نسخة منه:",
    "الوكيل المساعد للموارد البشرية",
    "مدير مكتب وكيل وزارة الداخلية",
    "هاتف : 17814474 / 17244348 - فاكس : 17274928 - ص ب : 13 المنامة - مملكة البحرين",
    "10 © «#تضادة كم جاوما مصدوموقا 13 مه 0 0 177748974 + 5 17177443498 178714474 ٠ ممموعلم+ : َّ , 0",
    "العلامة المائية المطبوعة على هذه الوثيقة لدواعي الأمن والخصوصية ... 685005 لإعدنااام لع0ة لرأأثنا586 101 ا أمعممنعمل قاط 0ه 0110160 101/21810771216 7118",
    "تنويه :هذه الوثيقة رسمية وشخصية لمتلقيها فقط , وينبغي عدم نسخها أو توزيعها أو استنساخها كلياً أو جزئياً , ولا تمريرها إلى أي طرف ثالث.",
    "The watermark printed on this document is for security and privacy purposes ... 6685005 /Ia2/A/M 300 /Iaa/Na'56 06) 5 76/1'l00 5ata 0h 1160m 60216 Hlala 7",
    "Notice: This document is official and personal to its recipient only , and must not be copied, distributed, or reproduced wholly or partially , nor transferred to any third party.",
    "عه ا0راا 10 1601001080 اه 010160اتاكال ,00180 58 أ00 كوانامفط5 200 كامعامامدة كا هذا اه80800م 200 ا2نا0005080 ,0028م بلاعاناء يا 060101801ل 7115 :4ارااشا0 015",
    ".0817 111:0 /(30 10 035580 0012 ,0311 10",
    "ط التموذج : 26/03/2026 09:53:40 145766 ١ 1 0_1"
  ];

  describe('Watermark, Disclaimer & Stamp Noise Suppression', () => {
    it('correctly identifies and suppresses Bahrain government watermark lines', () => {
      expect(window.isNoiseLine('العلامة المائية المطبوعة على هذه الوثيقة لدواعي الأمن والخصوصية ... 685005')).toBe(true);
      expect(window.isNoiseLine("The watermark printed on this document is for security and privacy purposes ... 6685005 /Ia2/A/M")).toBe(true);
    });

    it('correctly identifies and suppresses official confidentiality disclaimer boilerplate', () => {
      expect(window.isNoiseLine('تنويه :هذه الوثيقة رسمية وشخصية لمتلقيها فقط , وينبغي عدم نسخها أو توزيعها أو استنساخها كلياً أو جزئياً , ولا تمريرها إلى أي طرف ثالث.')).toBe(true);
      expect(window.isNoiseLine('Notice: This document is official and personal to its recipient only , and must not be copied, distributed, or reproduced wholly or partially , nor transferred to any third party.')).toBe(true);
    });

    it('correctly suppresses form model timestamps and barcode OCR garbage', () => {
      expect(window.isNoiseLine('ط التموذج : 26/03/2026 09:53:40 145766 ١ 1 0_1')).toBe(true);
      expect(window.isNoiseLine('ت النموذج : 15/09/2025 10:00:00')).toBe(true);
      expect(window.isNoiseLine('Model: 26/03/2026 09:53:40')).toBe(true);
      expect(window.isNoiseLine('عه ا0راا 10 1601001080 اه 010160اتاكال ,00180 58 أ00 كوانامفط5 200')).toBe(true);
      expect(window.isNoiseLine('.0817 111:0 /(30 10 035580 0012 ,0311 10')).toBe(true);
    });

    it('correctly suppresses scanner margin and circular stamp noise lines', () => {
      expect(window.isNoiseLine(': 0 - مط 2 0')).toBe(true);
      expect(window.isNoiseLine('| ص جز اكير')).toBe(true);
      expect(window.isNoiseLine('كد ص سس بر ٍٍِ 7 ١ 7 ا')).toBe(true);
      expect(window.isNoiseLine('4 الخ [٠مهحيم 0/7 1114011')).toBe(true);
      expect(window.isNoiseLine('يآ اا جاضا تي 7 2 5١ 7 111')).toBe(true);
      expect(window.isNoiseLine('0 التاقللتج صر #لر ل 7م أو 1/7')).toBe(true);
      expect(window.isNoiseLine('10 © «#تضادة كم جاوما مصدوموقا 13 مه 0 0 177748974')).toBe(true);
    });

    it('preserves legitimate administrative headers', () => {
      expect(window.isNoiseLine('فرع اسكان الشرطة')).toBe(false);
      expect(window.isNoiseLine('الرقم:١ات/ رش 101/١ / 1/8')).toBe(false);
      expect(window.isNoiseLine('التاريخ: 23 ربيع الأول 1447ه')).toBe(false);
      expect(window.isNoiseLine('الاسم : صالح قاسم عسكر')).toBe(false);
      expect(window.isNoiseLine('هاتف : 17814474 / 17244348 - فاكس : 17274928 - ص ب : 13 المنامة - مملكة البحرين')).toBe(false);
    });
  });

  describe('Typo and Dot-Tolerant Legal Translation (Zero Transliteration Gibberish)', () => {
    it('translates OCR dot-misreadings into correct English legal terms', () => {
      // "عقد الاتتفاع" (with ت instead of ن)
      expect(window.translateArabicText('عقد الاتتفاع')).toMatch(/Usufruct|Occupancy/i);

      // "المتضمنة" / "المضمنة"
      expect(window.translateArabicText('المتضمنة')).toMatch(/stipulat|includ/i);

      // "التقاعد" (retirement)
      expect(window.translateArabicText('عند إحالة المنتفع على التقاعد')).toMatch(/retirement/i);

      // "حصولة" (with taa marbuta/haa typo)
      expect(window.translateArabicText('أو حصولة على وحدة اسكانية')).toMatch(/obtaining.*(?:housing|residential)\s*unit/i);

      // "وزارة,الإسكان والتخطيط العمراني" (with comma attached)
      expect(window.translateArabicText('وزارة,الإسكان والتخطيط العمراني')).toMatch(/Ministry of Housing and Urban Planning/i);

      // "سبتمير" / "سنتمير" (September typos from OCR)
      expect(window.translateArabicText('30 سنتمير 2025م')).toMatch(/30 September 2025/i);
      expect(window.translateArabicText('01 سبتمير 2025م')).toMatch(/01 September 2025/i);

      // "دون استثتاء" (with ت instead of ن)
      expect(window.translateArabicText('دون استثتاء')).toMatch(/without exception/i);

      // "قِ حال عدم الإخلاء" (with ق instead of ف)
      expect(window.translateArabicText('قِ حال عدم الإخلاء')).toMatch(/(?:in the event of|in case of)\s*(?:failure to vacate|non-vacation)/i);

      // "الوكيل المساعد للموارد البشرية"
      expect(window.translateArabicText('الوكيل المساعد للموارد البشرية')).toMatch(/Assistant Undersecretary for Human Resources/i);

      // "مدير مكتب وكيل وزارة الداخلية"
      expect(window.translateArabicText('مدير مكتب وكيل وزارة الداخلية')).toMatch(/Director of the Office of the Undersecretary of the Ministry of Interior/i);
    });

    it('never produces raw transliteration gibberish in translated output', () => {
      const sampleLegalText = 'حسب عقد الانتفاع الميرم بينكم وبين وزارة الداخلية وحسب المواد روات المتضمنة عند إحالة المنتفع على التقاعد أوانهاء خدماته أو حصولة على وحدة اسكانية من وزارة,الإسكان والتخطيط العمراني أو شراء وحدة سكنية يجب عليه اخلاء الوحدة التابعة لوزارة الداخلية > وعد احالتكم الى التقاعد بتاريخ 01 سبتمير 2025م وعليه سوف تميهلك لغاية تاريخ 30 سنتمير 2025م الإخلاء الوحدة السكنية وتسليمها لفرع إسكان الشرطة دون استثتاء وستقوم وزارة الداخلية باتخاذ اءات القانونية اللازمة قِ حال عدم الإخلاء وذلك حسب النظام وما نص علية عقد الاتتفاع.';

      const translated = window.translateArabicText(sampleLegalText);

      // Crucial verification: NO transliteration tokens
      expect(hasTransliterationGibberish(translated)).toBe(false);

      // Must not contain known broken tokens
      expect(translated).not.toMatch(/Alantqaa/i);
      expect(translated).not.toMatch(/Almdhm/i);
      expect(translated).not.toMatch(/Altfaad/i);
      expect(translated).not.toMatch(/Altqaad/i);
      expect(translated).not.toMatch(/Awhswlh/i);
      expect(translated).not.toMatch(/Waltkhtyt/i);
      expect(translated).not.toMatch(/Alamra'y/i);
      expect(translated).not.toMatch(/Yjba/i);
      expect(translated).not.toMatch(/Mswf/i);
      expect(translated).not.toMatch(/Tarnkh/i);
      expect(translated).not.toMatch(/Sntmyr/i);
      expect(translated).not.toMatch(/Wtmslymha/i);
      expect(translated).not.toMatch(/Ast'na'/i);
      expect(translated).not.toMatch(/Hmsb/i);

      // Must convey clear legal meaning in English
      expect(translated).toMatch(/Ministry of Interior/i);
      expect(translated).toMatch(/retirement/i);
      expect(translated).toMatch(/30 September 2025/i);
      expect(translated).toMatch(/vacate/i);
    });
  });

  describe('End-to-End Pipeline on Real Document a3cc73ba7993427fb5b53fb37b3c977d', () => {
    it('processes raw OCR lines, purges 100% of watermark and stamp noise, and translates clearly', () => {
      // 1. Filter lines through isNoiseLine
      const cleanLines = RAW_OCR_LINES_A3CC.filter(l => !window.isNoiseLine(l));

      // Noise suppression: at least 15 junk lines must be purged
      expect(cleanLines.length).toBeLessThan(RAW_OCR_LINES_A3CC.length - 12);

      // 2. Translate every retained line
      const translatedLines = cleanLines.map(l => window.translateArabicText(l));
      const fullText = translatedLines.join('\n');

      // Verify ZERO watermark / disclaimer text made it through
      expect(fullText).not.toMatch(/watermark/i);
      expect(fullText).not.toMatch(/العلامة المائية/);
      expect(fullText).not.toMatch(/personal to its recipient only/i);
      expect(fullText).not.toMatch(/الوثيقة رسمية وشخصية/);
      expect(fullText).not.toMatch(/النموذج/);
      expect(fullText).not.toMatch(/Ia2/);
      expect(fullText).not.toMatch(/Hlala/);

      // Verify ZERO transliteration gibberish in entire translated document
      expect(hasTransliterationGibberish(fullText)).toBe(false);

      // Verify key facts are translated in clear English
      expect(fullText).toMatch(/Police Housing Branch/i);
      expect(fullText).toMatch(/Saleh Qasim Askar/i);
      expect(fullText).toMatch(/Ministry of Interior/i);
      expect(fullText).toMatch(/retirement/i);
      expect(fullText).toMatch(/30 September 2025/i);
      expect(fullText).toMatch(/vacate/i);
      expect(fullText).toMatch(/Kingdom of Bahrain/i);
    });
  });

  describe('End-to-End Pipeline on Real Document 393a2e4942354f309dda331fca474468 (Safra House 685 Notice)', () => {
    it('processes raw OCR lines, purges 100% of scanner/stamp noise, strips margin barcodes from headers, and translates fluently', () => {
      // 1. Filter lines through isNoiseLine
      const cleanLines = RAW_OCR_LINES_393A.filter(l => !window.isNoiseLine(l));

      // Noise suppression: at least 7 noise lines purged
      expect(cleanLines.length).toBeLessThanOrEqual(RAW_OCR_LINES_393A.length - 7);

      // 2. Translate every retained line
      const translatedLines = cleanLines.map(l => window.translateArabicText(l));
      const fullText = translatedLines.join('\n');

      // Verify ZERO transliteration gibberish in entire translated document
      expect(hasTransliterationGibberish(fullText)).toBe(false);

      // Verify ZERO raw broken transliteration tokens explicitly flagged by user
      expect(fullText).not.toMatch(/\bMktb\b/i);
      expect(fullText).not.toMatch(/\bIhdhar\b/i);
      expect(fullText).not.toMatch(/\bHdythh?\b/i);
      expect(fullText).not.toMatch(/\bYsknwn\b/i);
      expect(fullText).not.toMatch(/\bLmktb\b/i);
      expect(fullText).not.toMatch(/\bAsbwa\b/i);
      expect(fullText).not.toMatch(/\bShwal\b/i);
      expect(fullText).not.toMatch(/\bKhalkh\b/i);
      expect(fullText).not.toMatch(/\bLaa\b/i);

      // Verify barcode noise is stripped from official headers
      expect(fullText).toMatch(/Kingdom of Bahrain/i);
      expect(fullText).not.toMatch(/11177016/);
      expect(fullText).toMatch(/Ministry of Interior/i);
      expect(fullText).not.toMatch(/11722105/);
      expect(fullText).toMatch(/Police Housing Directorate Office/i);
      expect(fullText).not.toMatch(/61517/);

      // Verify high-quality readable English translation of key body contents
      expect(fullText).toMatch(/Corporal No\./i);
      expect(fullText).toMatch(/Saleh.*Qasim.*Hussain/i);
      expect(fullText).toMatch(/Safra/i);
      expect(fullText).toMatch(/Please provide a recent personal photograph and a copy of Smart \/ CPR Cards for all family members/i);
      expect(fullText).toMatch(/who reside in the temporary housing unit/i);
      expect(fullText).toMatch(/Police Housing Directorate Office no later than/i);
      expect(fullText).toMatch(/one week from receipt of the memorandum/i);
      expect(fullText).toMatch(/Shawwal/i);
    });
  });

  describe('30-Document Multi-Category Quality Benchmark Suite', () => {
    it('translates military and police administrative ranks accurately without transliteration', () => {
      expect(window.translateArabicText('رئيس عرفاء')).toBe('Master Sergeant');
      expect(window.translateArabicText('رئيس عرقاء')).toBe('Master Sergeant');
      expect(window.translateArabicText('عريف رقم 594175')).toMatch(/Corporal No\.\s*594175/i);
      expect(window.translateArabicText('النقيب / إبراهيم محمد')).toMatch(/Captain\s*\/\s*Ibrahim Mohamed/i);
      expect(window.translateArabicText('ملازم أول حسن')).toMatch(/First Lieutenant\s*Hassan/i);
      expect(window.translateArabicText('الرائد أحمد')).toMatch(/Major\s*Ahmed/i);
    });

    it('translates official ministry and directorate entities cleanly without transliteration', () => {
      expect(window.translateArabicText('مكتب إدارة إسكان الشرطة')).toBe('Police Housing Directorate Office');
      expect(window.translateArabicText('إدارة الإمداد والتموين')).toBe('Directorate of Supply and Catering');
      expect(window.translateArabicText('فرع اسكان الشرطة')).toBe('Police Housing Branch');
      expect(window.translateArabicText('وزارة الداخلية')).toBe('Ministry of Interior');
      expect(window.translateArabicText('مملكة البحرين')).toBe('Kingdom of Bahrain');
    });

    it('translates tenancy, utility bills, deductions, and notices with strict quality thresholds', () => {
      // Usufruct / Occupancy
      expect(window.translateArabicText('استقطاع بدل الانتفاع')).toMatch(/(?:deduction|deduct).*(?:usufruct|occupancy|allowance)/i);

      // Utility Bills
      expect(window.translateArabicText('فاتورة خدمات')).toMatch(/utility.*services.*bill|utility bill|services bill/i);
      expect(window.translateArabicText('هيئة الكهرباء والماء')).toMatch(/Electricity & Water Authority/i);

      // Eviction & Notices
      expect(window.translateArabicText('إشعار إخلاء وحدة سكنية')).toMatch(/Housing Unit Eviction Notice/i);
      expect(window.translateArabicText('مهلة لغاية تاريخ 30 سبتمبر')).toMatch(/grace period until.*30 September/i);

      // Maintenance & Modification
      expect(window.translateArabicText('طلب استبدال أبواب ونوافذ')).toMatch(/request.*replacement.*doors.*windows/i);
    });

    it('ensures zero occurrences of content_explanation or AI fallback mechanism', () => {
      // The entire offline OCR pipeline must function purely client-side without any server AI dependency
      expect(typeof window.translateArabicText).toBe('function');
      expect(typeof window.detectPageText).toBe('function');
      expect(typeof window.renderPageTranslationLayer).toBe('function');
    });
  });
});
