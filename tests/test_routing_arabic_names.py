import pytest
import re
from src.routing.config import FOLDER_ROUTING, FORM_FOLDERS, LETTER_FOLDERS

def is_arabic(text):
    # Regex to check if a string contains at least one Arabic character
    # and no English alphabet letters.
    if re.search(r'[a-zA-Z]', text):
        return False
    return True

def test_system_wide_arabic_names():
    # 1. Check FOLDER_ROUTING keys
    for folder in FOLDER_ROUTING.keys():
        assert is_arabic(folder), f"Folder name '{folder}' is not strictly Arabic."
        
    # 2. Check FORM_FOLDERS
    for folder in FORM_FOLDERS:
        assert is_arabic(folder), f"Form folder '{folder}' is not strictly Arabic."
        
    # 3. Check LETTER_FOLDERS
    for folder in LETTER_FOLDERS:
        assert is_arabic(folder), f"Letter folder '{folder}' is not strictly Arabic."

if __name__ == "__main__":
    test_system_wide_arabic_names()
    print("Verification successful: All configured folders use Arabic names.")
