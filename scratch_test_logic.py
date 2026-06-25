import sys
sys.path.append('.')
from src.pipeline import Pipeline
from src.schemas import PageClassification, Category, DocumentGroup
import os
from unittest.mock import patch

def test():
    with patch.dict(os.environ, {"GEMINI_API_KEYS": "dummy_key"}):
        pipeline = Pipeline()
        raw_pages = [
            (1, PageClassification(
                category=Category.BASIC_DETAILS,
                residents=[f"Name {i}" for i in range(8)],
                house_number="123",
                date="2023-01-01",
                is_continuation=False
            ))
        ]
        canonical_mapping = {}
        
        # Copied function with prints
        def my_group(raw_pages, canonical_mapping_clean):
            documents = []
            current_primary_tenant = "UNKNOWN"
            prefix_buffer = []
            verified_residents = set()

            ANCHOR_CATEGORIES = {Category.BASIC_DETAILS, Category.KEY_HANDOVER, Category.CONTRACT}

            for _, page in raw_pages:
                if page.category in ANCHOR_CATEGORIES:
                    mapped = [canonical_mapping_clean.get(r.upper().strip(), r) for r in page.residents]
                    for m in mapped:
                        if m not in ("NONE", "UNKNOWN", ""):
                            verified_residents.add(m)

            for i, (page_index, page) in enumerate(raw_pages):
                is_continuation = getattr(page, 'is_continuation', False)
                lookahead_continuation = False
                if i + 1 < len(raw_pages):
                    next_page = raw_pages[i + 1][1]
                    if getattr(next_page, 'is_continuation', False):
                        lookahead_continuation = True

                effective_continuation = is_continuation or lookahead_continuation

                mapped_residents = [canonical_mapping_clean.get(r.upper().strip(), r) for r in page.residents]
                valid_mapped = [r for r in mapped_residents if r not in ("NONE", "UNKNOWN", "")]

                group_list = prefix_buffer if current_primary_tenant == "UNKNOWN" else documents
                print(f"Top: current_primary_tenant={current_primary_tenant}, page_category={page.category}, valid_mapped={valid_mapped}")
                print(f"Top: group_list is prefix_buffer? {group_list is prefix_buffer}")
                
                if effective_continuation and group_list:
                    page_primary_tenant = group_list[-1].primary_tenant
                    page.category = group_list[-1].category
                else:
                    if page.category == Category.AMAR_TAKHSEES:
                        page_primary_tenant = current_primary_tenant
                    elif page.category == Category.PERSONAL_DETAILS:
                        page_primary_tenant = current_primary_tenant
                    elif valid_mapped:
                        if current_primary_tenant in valid_mapped:
                            page_primary_tenant = current_primary_tenant
                        else:
                            if page.category in ANCHOR_CATEGORIES and len(valid_mapped) <= 10:
                                matched = False
                                for candidate in valid_mapped:
                                    words_current = set(current_primary_tenant.split())
                                    words_candidate = set(candidate.split())
                                    print(f"Checking intersection: {words_current.intersection(words_candidate)}, len={len(words_current.intersection(words_candidate))}, min={min(2, len(words_current), len(words_candidate))}")
                                    if len(words_current.intersection(words_candidate)) >= min(2, len(words_current), len(words_candidate)):
                                        matched = True
                                        print(f"Matched by intersection!")
                                        break
                                    elif pipeline.client.check_name_match(current_primary_tenant, candidate, page.category.value):
                                        matched = True
                                        print(f"Matched by LLM!")
                                        break
                                print(f"matched={matched}")
                                if matched:
                                    page_primary_tenant = current_primary_tenant
                                else:
                                    current_primary_tenant = valid_mapped[0]
                                    page_primary_tenant = current_primary_tenant
                                    
                                    if prefix_buffer:
                                        for doc in prefix_buffer:
                                            doc.primary_tenant = current_primary_tenant
                                        documents.extend(prefix_buffer)
                                        prefix_buffer.clear()
                            else:
                                candidate = valid_mapped[0]
                                words_current = set(current_primary_tenant.split())
                                words_candidate = set(candidate.split())
                                if len(words_current.intersection(words_candidate)) >= min(2, len(words_current), len(words_candidate)):
                                    page_primary_tenant = current_primary_tenant
                                elif pipeline.client.check_name_match(current_primary_tenant, candidate, page.category.value):
                                    page_primary_tenant = current_primary_tenant
                                else:
                                    if candidate in verified_residents:
                                        page_primary_tenant = candidate
                                    else:
                                        page_primary_tenant = current_primary_tenant
                    else:
                        page_primary_tenant = current_primary_tenant

                print(f"Mid: current_primary_tenant={current_primary_tenant}, page_primary_tenant={page_primary_tenant}")
                group_list = prefix_buffer if current_primary_tenant == "UNKNOWN" else documents
                print(f"Mid: group_list is prefix_buffer? {group_list is prefix_buffer}")

                merge_condition = False
                if group_list and group_list[-1].category == page.category and group_list[-1].primary_tenant == page_primary_tenant:
                    if effective_continuation:
                        merge_condition = True
                    elif page.date != "NONE" and group_list[-1].dates and group_list[-1].dates[-1] == page.date:
                        merge_condition = True

                if merge_condition:
                    group_list[-1].end_page = page_index
                    if page.date != "NONE":
                        group_list[-1].dates.append(page.date)
                else:
                    group_list.append(DocumentGroup(
                        start_page=page_index,
                        end_page=page_index,
                        house_number=page.house_number,
                        primary_tenant=page_primary_tenant,
                        category=page.category,
                        dates=[page.date] if page.date != "NONE" else []
                    ))

            if current_primary_tenant == "UNKNOWN" and prefix_buffer:
                documents = prefix_buffer + documents

            return documents
        
        docs = my_group(raw_pages, canonical_mapping)
        print(f"Number of docs: {len(docs)}")
        for i, doc in enumerate(docs):
            print(f"Doc {i}: {doc.primary_tenant}")

if __name__ == '__main__':
    test()
