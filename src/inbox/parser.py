from src.core.schemas import ParsedCommand

def parse_filename_syntax(filename: str) -> ParsedCommand:
    """
    Parse a space-separated filename into a ParsedCommand.
    Format: [AREA] [HOUSE] [TENANT_HINT] [GROUP] [DATE] [TITLE]
    """
    if filename.lower().endswith(".pdf"):
        filename = filename[:-4]
    
    parts = filename.split(maxsplit=5)
    
    if len(parts) < 5:
        raise ValueError("Invalid Format")
    
    area, house, tenant_hint, group, date = parts[:5]
    title = parts[5] if len(parts) == 6 else ""
    
    return ParsedCommand(
        area=area,
        house=house,
        tenant_hint=tenant_hint,
        group=group,
        date=date,
        title=title
    )
