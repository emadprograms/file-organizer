import pylnk3
from src.utils.fs import create_shortcut
import os

create_shortcut("\\\\?\\C:\\Users\\dummy\\target.pdf", "dummy2.lnk")

try:
    with open("dummy2.lnk", "rb") as f:
        lnk = pylnk3.parse(f)
        print("Path:", lnk.path)
        print("Extra blocks:")
        for block in lnk.extra_blocks.keys():
            print(" -", block)
            if block == 'ENVIRONMENT_VARIABLES_LOCATION_BLOCK':
                print("   var target_ansi:", lnk.extra_blocks[block].target_ansi)
except Exception as e:
    print("Error:", e)
