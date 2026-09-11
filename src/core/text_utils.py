from __future__ import annotations
import re
import difflib

AR_TO_EN_MAP = {
    'ا': '', 'أ': '', 'إ': '', 'آ': '', 'ى': '',
    'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'j', 'ح': 'h', 'خ': 'kh',
    'د': 'd', 'ذ': 'dh', 'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'sh',
    'ص': 's', 'ض': 'd', 'ط': 't', 'ظ': 'dh', 'ع': '', 'غ': 'gh',
    'ف': 'f', 'ق': 'q', 'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n',
    'ه': 'h', 'ة': 'h', 'و': '', 'ي': '', 'ئ': '', 'ؤ': '', 'ء': ''
}


def clean_article(word: str) -> str:
    """Strip Arabic/English definite articles (al-, al, ال)."""
    if not word:
        return ""
    w = word.strip().lower()
    if w.startswith("al-") or w.startswith("al "):
        return w[3:].strip()
    if w.startswith("al") and len(w) > 4:
        return w[2:].strip()
    if w.startswith("ال") and len(w) > 3:
        return w[2:].strip()
    return w


def phonetic_normalize(text: str) -> str:
    """Normalize Arabic and Latin text to a consonant phonetic key.
    
    Treats v and w as equivalent (common in Gulf/South Asian transliteration).
    Strips short vowels and glides, collapses repeated characters.
    """
    if not text:
        return ""
    lower = text.lower()
    res = [AR_TO_EN_MAP.get(char, char) for char in lower]
    val = "".join(res)
    val = val.replace('v', 'w')
    val = re.sub(r'[aeiouyw]', '', val)
    val = val.replace('ph', 'f').replace('ck', 'k').replace('c', 'k')
    val = val.replace('th', 't').replace('dh', 'd').replace('kh', 'k').replace('gh', 'g').replace('sh', 's')
    val = re.sub(r'(.)\1+', r'\1', val)
    return val.strip()


AR_TRANSLIT_MAP = {
    'ا': 'a', 'أ': 'a', 'إ': 'i', 'آ': 'aa', 'ى': 'a',
    'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'j', 'ح': 'h', 'خ': 'kh',
    'د': 'd', 'ذ': 'dh', 'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'sh',
    'ص': 's', 'ض': 'd', 'ط': 't', 'ظ': 'dh', 'ع': 'a', 'غ': 'gh',
    'ف': 'f', 'ق': 'q', 'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n',
    'ه': 'h', 'ة': 'h', 'و': 'w', 'ي': 'y', 'ئ': 'y', 'ؤ': 'w', 'ء': ''
}


def to_latin(text: str) -> str:
    """Transliterate Arabic script into basic Latin characters."""
    if not text:
        return ""
    return "".join(AR_TRANSLIT_MAP.get(ch, ch) for ch in text.lower())


def normalize_translit(text: str) -> str:
    """Normalize common English transliteration variations (ee->y, oo->w, aa->a, v->w)."""
    if not text:
        return ""
    w = text.lower()
    w = re.sub(r'ee|ea|ey|ie|i', 'y', w)
    w = re.sub(r'oo|ou|u', 'w', w)
    w = re.sub(r'aa', 'a', w)
    w = w.replace('v', 'w')
    return w


def score_tenant_match(query: str, tenant_name: str, house_id: str = "") -> int:
    """Score how well a query matches a tenant name, with token-aware matching and ranking.
    
    Returns:
        int: 0 if no match, or a score >= 100 indicating match quality (higher = more relevant).
    """
    if not query or not tenant_name:
        return 0

    q_low = query.strip().lower()
    t_low = tenant_name.strip().lower()
    h_low = str(house_id).strip().lower()

    # Direct substring matches
    if q_low in t_low:
        return 1000 + (len(q_low) * 10)
    if h_low and q_low in h_low:
        return 900

    q_words = [w for w in q_low.split() if w]
    t_words = [w for w in t_low.split() if w]
    if not q_words or not t_words:
        return 0

    matched_words = 0
    total_score = 0

    for qi, qw in enumerate(q_words):
        qw_clean = clean_article(qw)
        qw_norm = phonetic_normalize(qw_clean)
        qw_latin = normalize_translit(qw_clean)
        best_word_score = 0

        for ti, tw in enumerate(t_words):
            tw_clean = clean_article(tw)
            tw_latin = normalize_translit(to_latin(tw_clean))

            # Exact word match
            if qw == tw or (qw_clean and qw_clean == tw_clean):
                s = 500
                if ti == 0 and qi == 0:
                    s += 50
                best_word_score = max(best_word_score, s)
            # Prefix match
            elif (tw.startswith(qw) or (qw_clean and tw_clean.startswith(qw_clean))) and len(qw_clean) >= 3:
                s = 300
                if ti == 0 and qi == 0:
                    s += 30
                best_word_score = max(best_word_score, s)
            # Substring word match
            elif tw.find(qw) != -1 or (qw_clean and tw_clean.find(qw_clean) != -1):
                best_word_score = max(best_word_score, 250)
            else:
                # Phonetic token match
                tw_norm = phonetic_normalize(tw_clean)
                if qw_norm and tw_norm:
                    if qw_norm == tw_norm:
                        s = 400
                        if ti == 0 and qi == 0:
                            s += 50
                        if qw_latin and tw_latin:
                            if qw_latin == tw_latin:
                                s += 100
                            else:
                                if qw_latin[0] == tw_latin[0]:
                                    s += 30
                                s += int(difflib.SequenceMatcher(None, qw_latin, tw_latin).ratio() * 70)
                        best_word_score = max(best_word_score, s)
                    elif (tw_norm.startswith(qw_norm) or qw_norm.startswith(tw_norm)) and min(len(qw_norm), len(tw_norm)) >= 3:
                        best_word_score = max(best_word_score, 200)
                    elif len(qw_norm) >= 3 and len(tw_norm) >= 3 and qw_norm[0] == tw_norm[0]:
                        sim = difflib.SequenceMatcher(None, qw_norm, tw_norm).ratio()
                        if sim >= 0.75:
                            best_word_score = max(best_word_score, int(sim * 150))

        if best_word_score > 0:
            matched_words += 1
            total_score += best_word_score

    if matched_words == len(q_words):
        return total_score

    return 0
