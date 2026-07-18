import re
import unicodedata
import json
from rapidfuzz import fuzz
from src.llm.llm import LLMClient

def normalize_arabic_text(text: str) -> str:
    """Normalize Arabic text by removing diacritics and unifying characters.

    Strips diacritics, normalizes alef variants to a single alef, teh marbuta to heh, 
    and alef maksura to yeh. Reduces multiple whitespaces to a single space.

    Args:
        text (str): The raw Arabic string to normalize.

    Returns:
        str: The normalized Arabic string.
    """
    text = unicodedata.normalize('NFKC', text)
    # Strip diacritics
    text = re.sub(r'[\u0617-\u061A\u064B-\u0652]', '', text)
    # Normalize alef
    text = re.sub(r'[أإآ]', 'ا', text)
    # Normalize teh marbuta
    text = re.sub(r'ة', 'ه', text)
    # Normalize alef maksura / yeh
    text = re.sub(r'ى', 'ي', text)
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def cluster_names_fuzzily(names: set[str]) -> dict[str, str]:
    """Group similar strings together using fuzzy string matching.

    Args:
        names (set[str]): A set of names to be clustered.

    Returns:
        dict[str, str]: A dictionary mapping each original name to its clustered representative name.
    """
    names_list = sorted(list(names))
    normalized_map = {n: normalize_arabic_text(n) for n in names_list}
    
    assigned_clusters = []
    for name in names_list:
        norm = normalized_map[name]
        found = False
        for cluster in assigned_clusters:
            rep_name = cluster[0]
            rep_norm = normalized_map[rep_name]
            score = fuzz.ratio(norm, rep_norm)
            if score >= 85:
                cluster.append(name)
                found = True
                break
        if not found:
            assigned_clusters.append([name])
            
    mapping = {}
    for cluster in assigned_clusters:
        longest = sorted(cluster, key=lambda x: (-len(x), x))[0]
        for name in cluster:
            mapping[name] = longest
            
    return mapping

def canonicalize_with_llm(
    unresolved_names: list[str], 
    llm_client: LLMClient, 
    allowed_tenants: list[str] | None = None
) -> dict[str, str]:
    """Map raw tenant names to canonical identities using an LLM.

    Args:
        unresolved_names (list[str]): The raw names to canonicalize.
        llm_client (LLMClient): The LLM client to use for mapping.
        allowed_tenants (list[str] | None): Optional list of permitted canonical tenant names.

    Returns:
        dict[str, str]: A dictionary mapping each unresolved name to a canonical name.

    Raises:
        RuntimeError: If the LLM returns an invalid or incomplete response.
    """
    if not unresolved_names:
        return {}
        
    if allowed_tenants:
        allowed_list = json.dumps(allowed_tenants, ensure_ascii=False)
        prompt = f"""
Please map the following raw tenant names to unified canonical identities.
IMPORTANT: You MUST map each raw name STRICTLY to one of the following known identities:
{allowed_list}
Is this name similar to any of the names here?

Raw names:
{json.dumps(unresolved_names, ensure_ascii=False)}

Respond ONLY with a JSON dictionary where keys are the raw names and values are the canonical Arabic names from the allowed list.
"""
    else:
        prompt = f"""
Please map the following raw tenant names to unified canonical identities.
Merge transliterations and OCR errors into a single canonical name.
IMPORTANT: Output all canonical identities strictly in Arabic.

Raw names:
{json.dumps(unresolved_names, ensure_ascii=False)}

Respond ONLY with a JSON dictionary where keys are the raw names and values are the canonical Arabic names.
"""
    
    response_text = llm_client._route_llm_call(
        model=llm_client.default_model,
        contents=[prompt],
        response_schema=None,
        log_prefix="CanonicalizeLLM"
    )
    
    if not response_text:
        raise RuntimeError("LLM returned empty response")
        
    response_text = response_text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:-3].strip()
    elif response_text.startswith("```"):
        response_text = response_text[3:-3].strip()
        
    try:
        result_map = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"LLM returned malformed JSON: {e}\nResponse text: {response_text}") from e
        
    if not isinstance(result_map, dict):
        raise RuntimeError(f"LLM did not return a JSON object (got {type(result_map).__name__})")
    
    missing_keys = set(unresolved_names) - set(result_map.keys())
    if missing_keys:
        raise RuntimeError(f"LLM dropped names from the mapping: {missing_keys}")
    
    return result_map
