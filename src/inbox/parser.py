import re
from src.core.schemas import ParsedCommand

def parse_filename_syntax(filename: str) -> ParsedCommand:
    """
    Parse a space-separated filename into a ParsedCommand.
    Format: [AREA] [HOUSE] [TENANT_HINT] [GROUP] [DATE] [TITLE]
    
    AREA may be multi-word (e.g. 'Safra D').
    TENANT_HINT may be multi-word (e.g. 'خالد عبود هزاع الخلف').
    GROUP is always a digit (1-13), 'G', or 'U'.
    DATE is always YYYY-MM-DD, 'U', or 'UnknownDate'.
    TITLE is everything after DATE.
    """
    if filename.lower().endswith(".pdf"):
        filename = filename[:-4]
    # Strip Proposed suffix if present
    if filename.endswith("Proposed"):
        filename = filename[:-9]

    tokens = filename.split()
    if len(tokens) < 5:
        raise ValueError("Invalid Format: too few tokens")

    # HOUSE: find the first 3+-digit numeric token (e.g. '703', '504').
    # If none found, fall back to token at index 1 (raw format: "U U U U U Title")
    house_idx = None
    for i, t in enumerate(tokens):
        if t.isdigit() and len(t) >= 3:
            house_idx = i
            break
    if house_idx is None:
        house_idx = 1  # raw format fallback

    area = " ".join(tokens[:house_idx])
    house = tokens[house_idx]

    # GROUP is the next token after tenant that is a digit (1-13), 'G', or 'U'
    group_idx = None
    for i in range(house_idx + 1, len(tokens)):
        t = tokens[i].upper()
        if t in ('G', 'U') or (t.isdigit() and 1 <= int(t) <= 13):
            group_idx = i
            break
    if group_idx is None:
        raise ValueError("Invalid Format: no group token found")

    tenant_hint = " ".join(tokens[house_idx + 1:group_idx]) or 'U'
    group = tokens[group_idx]

    # DATE is the next token after group — either YYYY-MM-DD, 'U', or 'UnknownDate'
    date_idx = group_idx + 1
    date = tokens[date_idx] if date_idx < len(tokens) else 'U'

    # TITLE is everything after DATE
    title = " ".join(tokens[date_idx + 1:]) if date_idx + 1 < len(tokens) else ""

    return ParsedCommand(
        area=area,
        house=house,
        tenant_hint=tenant_hint,
        group=group,
        date=date,
        title=title
    )
