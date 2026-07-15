import re
import unicodedata
import logging
import json
from rapidfuzz import fuzz
from src.llm.llm import LLMClient
from src.core.models import PageData, TenantTimeline

logger = logging.getLogger(f"file_organizer.{__name__}")

def normalize_arabic_text(text: str) -> str:
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

def canonicalize_with_llm(unresolved_names: list[str], llm_client: LLMClient) -> dict[str, str]:
    if not unresolved_names:
        return {}
        
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

def build_tenant_timelines(pages: list[PageData], canonical_mapping: dict[str, str]) -> list[TenantTimeline]:
    anchor_categories = {"contract", "forms", "id_cards"}
    
    tenant_stats = {}
    for page in pages:
        raw_name = page.expected_tenant_name
        if not raw_name:
            continue
            
        canonical_name = canonical_mapping.get(raw_name, raw_name)
        if canonical_name not in tenant_stats:
            tenant_stats[canonical_name] = {"anchor_count": 0, "total_count": 0, "dates": []}
            
        stats = tenant_stats[canonical_name]
        stats["total_count"] += 1
        
        if page.category in anchor_categories:
            stats["anchor_count"] += 1
            
        if page.resolved_date:
            stats["dates"].append(page.resolved_date)
            
    timelines = []
    for name, stats in tenant_stats.items():
        if stats["anchor_count"] >= 1 and stats["total_count"] >= 5:
            if stats["dates"]:
                min_date = min(stats["dates"])
                max_date = max(stats["dates"])
                if min_date > max_date:
                    raise RuntimeError(f"min_date {min_date} > max_date {max_date}")
                logger.info(f"Qualified Tenant '{name}': {stats['total_count']} pages, {stats['anchor_count']} anchors -> Timeline: {min_date} to {max_date}")
                timelines.append(TenantTimeline(
                    canonical_name=name,
                    min_date=min_date,
                    max_date=max_date
                ))
            else:
                logger.info(f"Rejected Tenant '{name}': Missing valid dates.")
        else:
            logger.info(f"Rejected Tenant '{name}': {stats['total_count']} pages, {stats['anchor_count']} anchors (Failed threshold of >=1 anchors, >=5 pages)")
                
    return timelines
