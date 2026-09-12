import pytest
from src.core.text_utils import phonetic_normalize, clean_article, score_tenant_match


def test_clean_article():
    assert clean_article("al-balushi") == "balushi"
    assert clean_article("al balushi") == "balushi"
    assert clean_article("albalushi") == "balushi"
    assert clean_article("البلوشي") == "بلوشي"
    assert clean_article("الطارش") == "طارش"


def test_phonetic_normalize_javed_jawed():
    assert phonetic_normalize("javed") == phonetic_normalize("jawed")
    assert phonetic_normalize("javed") == phonetic_normalize("جاويد")


def test_score_tenant_match_ameed():
    # ameed must match عميد ali mohamed aziz with high score
    score = score_tenant_match("ameed", "عميد علي محمد عزيز", "SAF F 2450_22")
    assert score >= 400

    # ameed must NOT match Ahmed or Mohamed
    assert score_tenant_match("ameed", "أحمد سالم بورشيد", "512") == 0
    assert score_tenant_match("ameed", "محمد عثمان حاجي", "551") == 0


def test_score_tenant_match_javed():
    # javed must match all variations of جاويد
    assert score_tenant_match("javed", "جاويد أكرم محمد", "1264") >= 400
    assert score_tenant_match("javed", "خالد جاويد محمد", "1247") >= 400
    assert score_tenant_match("jawed", "جاويد أكرم محمد", "1264") >= 400


def test_score_tenant_match_multiword():
    score = score_tenant_match("fawaz khalil", "فواز خليل الطارش", "500")
    assert score >= 800
    assert score_tenant_match("fawaz javed", "فواز خليل الطارش", "500") == 0


def test_score_tenant_match_usman_othman_precision():
    # Usman, Uthman, Osman, Othman MUST match عثمان with high score
    assert score_tenant_match("usman", "محمد عثمان حاجي", "551") >= 400
    assert score_tenant_match("uthman", "محمد عثمان حاجي", "551") >= 400
    assert score_tenant_match("osman", "محسن عثمان عبد الرب", "950") >= 400
    assert score_tenant_match("othman", "عادل عبد الرحمن عثمان البلوشي", "1336") >= 400

    # Usman MUST NOT match Zaid, Salman, Sulaiman, or Waseem
    assert score_tenant_match("usman", "زياد عوض السليمان", "SAF F 2450_21") == 0
    assert score_tenant_match("usman", "سلمان عبيد عنفوس", "1281") == 0
    assert score_tenant_match("usman", "سليمان مطلق نجم العبدالله", "608") == 0
    assert score_tenant_match("usman", "وسيم سردار محمد", "551") == 0


def test_score_tenant_match_waseem_precision():
    # Waseem must match وسيم
    assert score_tenant_match("waseem", "وسيم سردار محمد", "551") >= 400

    # Waseem MUST NOT match Sami or Asma
    assert score_tenant_match("waseem", "سامي محمد ناجي الصميل", "944") == 0
    assert score_tenant_match("waseem", "أسماء خيام محمد الأنصاري", "514") == 0


def test_score_tenant_match_zaid_precision():
    # Zaid must match زياد and زيد
    assert score_tenant_match("zaid", "زياد عوض السليمان", "SAF F 2450_21") >= 400
    assert score_tenant_match("zaid", "مصلح عيسى علي زيد", "1336") >= 400

    # Zaid MUST NOT match عثمان
    assert score_tenant_match("zaid", "محمد عثمان حاجي", "551") == 0


def test_score_tenant_match_balushi():
    # Balushi must match البلوشي
    assert score_tenant_match("balushi", "عدنان عبدالواحد علي البلوشي", "100") >= 400
    assert score_tenant_match("al balushi", "عدنان عبدالواحد علي البلوشي", "100") >= 400


def test_score_tenant_match_unique_db_names():
    # 1. Jamshed / Jamsheed / Jamshid -> جمشيد أنور محمد أنور
    assert score_tenant_match("jamshed", "جمشيد أنور محمد أنور", "SAF F 2452_12") >= 400
    assert score_tenant_match("jamsheed", "جمشيد أنور محمد أنور", "SAF F 2452_12") >= 400
    assert score_tenant_match("jamshid", "جمشيد أنور محمد أنور", "SAF F 2452_12") >= 400

    # 2. Tayseer / Taiseer -> تيسير خطاب عبد الكريم
    assert score_tenant_match("tayseer", "تيسير خطاب عبد الكريم", "SAF F 2456_33") >= 400
    assert score_tenant_match("taiseer", "تيسير خطاب عبد الكريم", "SAF F 2456_33") >= 400
    assert score_tenant_match("khattab", "تيسير خطاب عبد الكريم", "SAF F 2456_33") >= 400

    # 3. Sarfaraz / Sarfraz -> سرفراز نواز محمد يوسف عبد الصادق رجا
    assert score_tenant_match("sarfaraz", "سرفراز نواز محمد يوسف عبد الصادق رجا", "SAF F 2452_33") >= 400
    assert score_tenant_match("sarfraz", "سرفراز نواز محمد يوسف عبد الصادق رجا", "SAF F 2452_33") >= 400

    # 4. Madhu / Soodanan / Sudanan / Nair -> مادو سودانان ناير
    assert score_tenant_match("madu", "مادو سودانان ناير", "SAF F 2456_11") >= 400
    assert score_tenant_match("soodanan", "مادو سودانان ناير", "SAF F 2456_11") >= 400
    assert score_tenant_match("sudanan", "مادو سودانان ناير", "SAF F 2456_11") >= 400
    assert score_tenant_match("nair", "مادو سودانان ناير", "SAF F 2456_11") >= 400

    # 5. Shaukat / Showkat / Shoukat -> شوكت علي البلوشي
    assert score_tenant_match("shaukat", "شوكت علي البلوشي", "1260") >= 400
    assert score_tenant_match("showkat", "شوكت علي البلوشي", "1260") >= 400
    assert score_tenant_match("shoukat", "شوكت علي البلوشي", "1260") >= 400

    # 6. Anwar -> أنور (محمد أنور حاجي حسن البلوشي)
    assert score_tenant_match("anwar", "محمد أنور حاجي حسن البلوشي", "1260") >= 400
    assert score_tenant_match("anwar", "أنور علي عوض علي", "1260") >= 400

    # 7. Parvez / Parwez -> شمس برويز محمد
    assert score_tenant_match("parvez", "شمس برويز محمد", "SAF F 2450_12") >= 400
    assert score_tenant_match("parwez", "شمس برويز محمد", "SAF F 2450_12") >= 400

    # 8. Suwaidi vs Saud isolation: suwaidi must match السويدي and NOT match سعود
    assert score_tenant_match("suwaidi", "محمد عبد القادر السويدي", "100") >= 400
    assert score_tenant_match("suwaidi", "عبدالله سعود الدوسري", "500") == 0
    assert score_tenant_match("saud", "عبدالله سعود الدوسري", "500") >= 400

    # 9. Awadh / Awad -> زياد عوض السليمان
    assert score_tenant_match("awadh", "زياد عوض السليمان", "SAF F 2450_21") >= 400
    assert score_tenant_match("awad", "زياد عوض السليمان", "SAF F 2450_21") >= 400


def test_score_tenant_match_arabic_searches():
    # 1. Exact Arabic name matching
    assert score_tenant_match("جمشيد", "جمشيد أنور محمد أنور", "SAF F 2452_12") >= 1000
    assert score_tenant_match("تيسير", "تيسير خطاب عبد الكريم", "SAF F 2456_33") >= 1000
    assert score_tenant_match("عميد", "عميد علي محمد عزيز", "SAF F 2450_22") >= 1000
    assert score_tenant_match("جاويد", "جاويد إقبال شودري", "1264") >= 1000
    assert score_tenant_match("شوكت", "شوكت علي البلوشي", "1260") >= 1000
    assert score_tenant_match("عثمان", "محمد عثمان حاجي فقير محمد", "551") >= 1000
    assert score_tenant_match("مادو", "مادو سودانان ناير", "SAF F 2456_11") >= 1000
    assert score_tenant_match("سرفراز", "سرفراز نواز محمد يوسف عبد الصادق رجا", "SAF F 2452_33") >= 1000
    assert score_tenant_match("شمس برويز", "شمس برويز محمد", "SAF F 2450_12") >= 1000

    # 2. Hamza variations (bare Alif vs Hamza above/below: انور vs أنور, اقبال vs إقبال, احمد vs أحمد)
    assert score_tenant_match("انور", "أنور علي عوض علي", "SAF F 2450_24") >= 1000
    assert score_tenant_match("أنور", "أنور علي عوض علي", "SAF F 2450_24") >= 1000
    assert score_tenant_match("اقبال", "جاويد إقبال شودري", "1264") >= 1000
    assert score_tenant_match("إقبال", "جاويد إقبال شودري", "1264") >= 1000
    assert score_tenant_match("احمد", "أحمد سالم بورشيد", "512") >= 1000
    assert score_tenant_match("أحمد", "أحمد سالم بورشيد", "512") >= 1000

    # 3. Arabic Tashkeel / Harakat (diacritics stripping)
    assert score_tenant_match("أَنْوَر", "أنور علي عوض علي", "SAF F 2450_24") >= 1000
    assert score_tenant_match("مُحَمَّد", "محمد أنور", "1260") >= 1000
    assert score_tenant_match("جَمْشِيد", "جمشيد أنور محمد أنور", "SAF F 2452_12") >= 1000
    assert score_tenant_match("تَيْسِير", "تيسير خطاب عبد الكريم", "SAF F 2456_33") >= 1000

    # 4. Taa Marbuta (ة) vs Haa (ه) and Alif Maqsura (ى) vs Yaa (ي)
    assert score_tenant_match("فاطمه", "فاطمة بنت علي", "100") >= 1000
    assert score_tenant_match("فاطمة", "فاطمة بنت علي", "100") >= 1000
    assert score_tenant_match("يحيي", "يحيى عبد الرحمن", "100") >= 1000
    assert score_tenant_match("يحيى", "يحيى عبد الرحمن", "100") >= 1000

    # 5. Arabic isolation: سويدي matches السويدي and NOT سعود
    assert score_tenant_match("السويدي", "محمد عبد القادر السويدي", "100") >= 1000
    assert score_tenant_match("سويدي", "محمد عبد القادر السويدي", "100") >= 1000
    assert score_tenant_match("سويدي", "عبدالله سعود الدوسري", "500") == 0
    assert score_tenant_match("سعود", "عبدالله سعود الدوسري", "500") >= 1000
    assert score_tenant_match("سعود", "محمد عبد القادر السويدي", "100") == 0


def test_arabic_normalization_and_variants():
    from src.core.text_utils import strip_arabic_diacritics, normalize_arabic, get_arabic_search_variants

    assert strip_arabic_diacritics("أَنْوَر") == "أنور"
    assert strip_arabic_diacritics("مُحَمَّد") == "محمد"
    assert normalize_arabic("إقبال") == "اقبال"
    assert normalize_arabic("فاطمة") == "فاطمه"
    assert normalize_arabic("مستشفى") == "مستشفي"

    v_anwar = get_arabic_search_variants("انور")
    assert "انور" in v_anwar and "أنور" in v_anwar

    v_syana = get_arabic_search_variants("صيانه")
    assert "صيانه" in v_syana and "صيانة" in v_syana

    v_shahada = get_arabic_search_variants("شهاده")
    assert "شهاده" in v_shahada and "شهادة" in v_shahada


