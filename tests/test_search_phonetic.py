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
