from src.core.schemas import DocumentGroup

def group_pages(raw_pages, client=None) -> list[DocumentGroup]:
    """Group classified pages into cohesive document blocks.
    
    Args:
        raw_pages (list[tuple[int, any]]): The sequence of classified pages.
        client: The LLM client for semantic grouping.
        
    Returns:
        list[DocumentGroup]: The final grouped documents.
    """
    documents: list[DocumentGroup] = []
    
    # 1. Pre-group by Category AND Primary Tenant (The "Category & Tenant Wall")
    blocks = []
    if raw_pages:
        current_block = [raw_pages[0]]
        def get_sig(p):
            """Generate a signature for a page to determine block grouping."""
            return (p.category, p.residents[0] if p.residents else "NONE")
        
        current_sig = get_sig(raw_pages[0][1])
        for item in raw_pages[1:]:
            sig = get_sig(item[1])
            if sig == current_sig:
                current_block.append(item)
            else:
                blocks.append(current_block)
                current_block = [item]
                current_sig = sig
        if current_block:
            blocks.append(current_block)

    all_groups = [] # list of lists of (p_idx, p)
    chunk_size = 25
    
    for block in blocks:
        if len(block) == 1:
            all_groups.append([block[0]])
            continue
            
        block_groups: list[list[tuple[int, any]]] = [] # list of lists of (p_idx, p)
        for i in range(0, len(block), chunk_size):
            # Overlapping sliding window
            start_idx = max(0, i - 2) if i > 0 else 0
            chunk = block[start_idx:i+chunk_size]
            
            pages_data = []
            for p_idx, p in chunk:
                names_str = p.residents[0] if p.residents else "NONE"
                summary_str = p.summary
                pages_data.append([p_idx, names_str, summary_str])
            
            if client:
                result = client.check_bulk_semantic_grouping(pages_data)
                
                # Match LLM result groups back to our (p_idx, p) objects based on their order in the chunk
                for new_g_indices in result.groups:
                    if not new_g_indices: continue
                    # Build a list of actual items for this new group
                    new_g_items = []
                    for expected_idx in new_g_indices:
                        for item in chunk:
                            if item[0] == expected_idx and item not in new_g_items:
                                new_g_items.append(item)
                                break
                                
                    if not new_g_items: continue
                    
                    shared = False
                    for existing_g in block_groups:
                        # Check intersection by identity
                        if any(x in existing_g for x in new_g_items):
                            for x in new_g_items:
                                if x not in existing_g:
                                    existing_g.append(x)
                            # Sort by p_idx
                            existing_g.sort(key=lambda x: x[0])
                            shared = True
                            break
                    if not shared:
                        new_g_items.sort(key=lambda x: x[0])
                        block_groups.append(new_g_items)
            else:
                # If no client, fallback to single group for chunk
                block_groups.append(chunk)
                    
        all_groups.extend(block_groups)
        
    for group in all_groups:
        if not group: continue
        # group is a list of (p_idx, p)
        group.sort(key=lambda x: x[0])
        start_page = group[0][0]
        end_page = group[-1][0]
        
        primary_tenant = group[0][1].residents[0] if group[0][1].residents else "UNKNOWN"
            
        category = group[0][1].category
        dates = [p.date for p_idx, p in group if p.date != "NONE"]
        
        documents.append(DocumentGroup(
            start_page=start_page,
            end_page=end_page,
            primary_tenant=primary_tenant,
            category=category,
            dates=dates
        ))
        
    return documents
