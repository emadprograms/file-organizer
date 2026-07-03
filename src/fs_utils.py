import re
import unicodedata

def sanitize_filename(filename: str) -> str:
    """
    Apply Unicode NFC normalization, strip Windows reserved characters,
    strip invisible Unicode control characters, and truncate the result to 200 characters.
    """
    # Unicode normalize NFC
    filename = unicodedata.normalize('NFC', filename)
    
    # Strip Windows reserved characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Strip invisible Unicode control characters (Cc and Cf)
    filename = ''.join(ch for ch in filename if unicodedata.category(ch) not in ('Cc', 'Cf'))
    
    # Truncate to 200 characters
    return filename[:200]
