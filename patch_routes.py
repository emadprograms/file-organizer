import re

with open('src/api/routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'from src.api.models import HouseResponse, VaultFileResponse, CategoryResponse, TimelineGroupResponse',
    'from src.api.models import HouseResponse, VaultFileResponse, CategoryResponse, TimelineGroupResponse, TreeItemResponse'
)

new_endpoint = """
@router.get("/api/tree", response_model=list[TreeItemResponse])
async def get_tree(request: Request):
    config = request.app.state.config
    areas_root = Path(config.areas_root_path)
    if not areas_root.exists():
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
        
    area_mappings = config.area_mappings or {}
    
    areas = {}
    
    def get_area_name(house_id: str) -> str:
        for a_name, a_prefix in area_mappings.items():
            if str(house_id).startswith(str(a_prefix)):
                return a_name
        return "Uncategorized Area"

    for entry in areas_root.iterdir():
        if entry.is_dir():
            house_dir_name = entry.name
            house_id = house_dir_name.split(" - ")[0] if " - " in house_dir_name else house_dir_name
            
            area_name = get_area_name(house_id)
            if area_name not in areas:
                areas[area_name] = TreeItemResponse(
                    id=f"area_{area_name}",
                    name=area_name,
                    type="area",
                    children=[]
                )
            
            house_node = TreeItemResponse(
                id=house_dir_name,
                name=house_dir_name,
                type="house",
                children=[]
            )
            
            state_path = entry / ".source_files" / f"{house_id}_state.json"
            tenants = set()
            if state_path.exists():
                try:
                    with open(state_path, "r", encoding="utf-8") as f:
                        state_data = json.load(f)
                        for group in state_data.get("grouped_documents", []):
                            tenant = group.get("primary_tenant")
                            if tenant:
                                tenants.add(tenant)
                except Exception:
                    pass
            
            for t in sorted(tenants):
                house_node.children.append(TreeItemResponse(
                    id=f"{house_dir_name}_{t}",
                    name=t,
                    type="tenant"
                ))
            
            areas[area_name].children.append(house_node)
            
    return list(areas.values())
"""

content = content + "\n" + new_endpoint

with open('src/api/routes.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched routes.py")
