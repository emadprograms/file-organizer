from __future__ import annotations
import re
import difflib

AR_TO_EN_MAP = {
    'ا': '', 'أ': '', 'إ': '', 'آ': '', 'ى': '',
    'ب': 'b', 'ت': 't', 'ث': 's', 'ج': 'j', 'ح': 'h', 'خ': 'k',
    'د': 'd', 'ذ': 'z', 'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 's',
    'ص': 's', 'ض': 'd', 'ط': 't', 'ظ': 'z', 'ع': '', 'غ': 'g',
    'ف': 'f', 'ق': 'k', 'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n',
    'ه': 'h', 'ة': 'h', 'W': 'w', 'و': '', 'ي': '', 'ئ': '', 'ؤ': 'w', 'ء': ''
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
    lower = text.lower().strip()
    # Distinguish Arabic 'و' as consonant 'W' vs long vowel (uu/oo)
    # 1. Beginning of word (^و or [ -]و) -> consonant W (وسيم, وليد)
    lower = re.sub(r'(^|[\s\-])و', r'\1W', lower)
    # 2. Adjacent to Alif (او or وا) -> consonant W (جاويد, فواز, نواز, رضوان)
    lower = re.sub(r'[اآإأ][وؤ]|[وؤ][اآإأ]', 'W', lower)
    # 3. Waw followed by Yaa (وي as in سويدي, برويز, كويت, رويلي) -> consonant W
    lower = re.sub(r'[وؤ]ي', 'Wy', lower)
    # 4. Word-initial Ayn followed by Waw (^عو as in عوض, عواض) -> consonant W
    lower = re.sub(r'(^|[\s\-])ع[وؤ]', r'\1W', lower)
    # 5. Names on pattern Anwar/Munawwar ([اآإأ]نو, منو, أرو) -> consonant W
    lower = re.sub(r'(^|[\s\-])([اآإأ]ن|[اآإأ]ر|من)[وؤ]', r'\1\2W', lower)

    # In English: diphthong ow/aw before consonant or end of token -> vowel (e.g. showkat -> shokat)
    lower = re.sub(r'([oa])w(?=[^aeiouy\s]|$)', r'\1', lower)

    # Replace English digraphs prior to Arabic mapping to prevent Arabic س + ح (Seen + Haa) from collapsing as English "sh"
    lower = lower.replace('v', 'w')
    lower = lower.replace('th', 's')
    lower = lower.replace('kh', 'k').replace('gh', 'g').replace('sh', 's')
    lower = lower.replace('dh', 'z').replace('zh', 'z')
    lower = lower.replace('ph', 'f').replace('p', 'b')
    lower = lower.replace('ck', 'k').replace('c', 'k').replace('q', 'k')

    res = [AR_TO_EN_MAP.get(char, char) for char in lower]
    val = "".join(res)
    val = re.sub(r'[aeiouy]', '', val)
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


def strip_arabic_diacritics(text: str) -> str:
    """Remove Arabic tashkeel (harakat / diacritics) and tatweel (kashida)."""
    if not text:
        return ""
    return re.sub(r'[\u064B-\u065F\u0670\u0640]', '', text)


def normalize_arabic(text: str) -> str:
    """Normalize Arabic orthographic variations (Alefs, Taa Marbuta, Alif Maqsura)."""
    if not text:
        return ""
    s = strip_arabic_diacritics(text).strip().lower()
    s = re.sub(r'[أإآٱ]', 'ا', s)
    s = s.replace('ة', 'ه').replace('ى', 'ي')
    return s


def get_arabic_search_variants(query: str) -> list[str]:
    """Generate search query variants for Arabic spelling variations (Hamza, Taa Marbuta, Alif Maqsura)."""
    if not query:
        return []
    clean = strip_arabic_diacritics(query).strip().lower()
    variants = [clean]

    # 1. Alef with Hamza <-> bare Alef
    if any(c in clean for c in 'أإآٱ'):
        v = re.sub(r'[أإآٱ]', 'ا', clean)
        if v not in variants:
            variants.append(v)
    elif 'ا' in clean:
        v1 = re.sub(r'(^|[\s\-])ا', r'\1أ', clean)
        v2 = re.sub(r'(^|[\s\-])ا', r'\1إ', clean)
        if v1 not in variants:
            variants.append(v1)
        if v2 not in variants:
            variants.append(v2)

    # 2. Taa Marbuta <-> Haa
    if clean.endswith('ة'):
        v = clean[:-1] + 'ه'
        if v not in variants:
            variants.append(v)
    elif clean.endswith('ه'):
        v = clean[:-1] + 'ة'
        if v not in variants:
            variants.append(v)

    # 3. Alif Maqsura <-> Yaa
    if clean.endswith('ى'):
        v = clean[:-1] + 'ي'
        if v not in variants:
            variants.append(v)
    elif clean.endswith('ي'):
        v = clean[:-1] + 'ى'
        if v not in variants:
            variants.append(v)

    return [v for v in variants if v]


def score_tenant_match(query: str, tenant_name: str, house_id: str = "") -> int:
    """Score how well a query matches a tenant name, with token-aware matching and ranking.
    
    Returns:
        int: 0 if no match, or a score >= 100 indicating match quality (higher = more relevant).
    """
    if not query or not tenant_name:
        return 0

    q_clean = strip_arabic_diacritics(query)
    t_clean = strip_arabic_diacritics(tenant_name)
    q_low = q_clean.strip().lower()
    t_low = t_clean.strip().lower()
    h_low = str(house_id).strip().lower()

    q_norm_ar = normalize_arabic(q_low)
    t_norm_ar = normalize_arabic(t_low)

    # Direct substring matches (exact or normalized Arabic)
    if q_low in t_low or (q_norm_ar and q_norm_ar in t_norm_ar):
        return 1000 + (len(q_low) * 10)
    
    # House number matching (e.g. searching "500" returns tenants in house 500)
    h_num = h_low.split(" - ")[0].strip() if " - " in h_low else h_low
    if h_num and (q_low == h_num or (q_low.isdigit() and q_low in h_num)):
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
        qw_norm_ar = normalize_arabic(qw_clean)
        best_word_score = 0

        for ti, tw in enumerate(t_words):
            tw_clean = clean_article(tw)
            tw_latin = normalize_translit(to_latin(tw_clean))
            tw_norm_ar = normalize_arabic(tw_clean)

            # Exact word match
            if qw == tw or (qw_clean and qw_clean == tw_clean) or (qw_norm_ar and qw_norm_ar == tw_norm_ar):
                s = 500
                if ti == 0 and qi == 0:
                    s += 50
                best_word_score = max(best_word_score, s)
            # Prefix match
            elif (
                (tw.startswith(qw) or (qw_clean and tw_clean.startswith(qw_clean))) and len(qw_clean) >= 3
            ) or (
                (qw_norm_ar and tw_norm_ar.startswith(qw_norm_ar)) and len(qw_norm_ar) >= 3
            ):
                s = 300
                if ti == 0 and qi == 0:
                    s += 30
                best_word_score = max(best_word_score, s)
            # Substring word match
            elif (
                (tw.find(qw) != -1 or (qw_clean and tw_clean.find(qw_clean) != -1))
                or (qw_norm_ar and tw_norm_ar.find(qw_norm_ar) != -1)
            ):
                best_word_score = max(best_word_score, 250)
            else:
                # Phonetic token match
                tw_norm = phonetic_normalize(tw_clean)
                if qw_norm and tw_norm:
                    is_phonetic_match = (qw_norm == tw_norm) or (
                        'z' in qw_norm and qw_norm.replace('z', 'd') == tw_norm
                    )
                    if is_phonetic_match:
                        s = 400
                        if ti == 0 and qi == 0:
                            s += 50
                        if qw_latin and tw_latin:
                            if qw_latin == tw_latin:
                                s += 100
                            elif qw_latin[0] == tw_latin[0]:
                                s += 30
                        best_word_score = max(best_word_score, s)
                    elif len(qw_norm) >= 3 and tw_norm.startswith(qw_norm):
                        best_word_score = max(best_word_score, 200)

            # Compound token pair check (e.g. "abdullah" matching "عبد" + "الله")
            if ti + 1 < len(t_words):
                tw_pair = tw_clean + " " + clean_article(t_words[ti + 1])
                tw_pair_norm = phonetic_normalize(tw_pair).replace(" ", "")
                is_compound_match = (qw_norm == tw_pair_norm) or (
                    'z' in qw_norm and qw_norm.replace('z', 'd') == tw_pair_norm
                )
                if qw_norm and len(qw_norm) >= 4 and is_compound_match:
                    s = 450
                    if ti == 0 and qi == 0:
                        s += 50
                    best_word_score = max(best_word_score, s)

        if best_word_score > 0:
            matched_words += 1
            total_score += best_word_score

    if matched_words == len(q_words):
        return total_score

    return 0
