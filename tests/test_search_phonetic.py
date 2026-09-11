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

