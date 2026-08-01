import pylnk3
from pathlib import Path
target_path = "/Users/emadarshadalam/Documents/GitHub"
clean_target = "C:" + str(Path(target_path).resolve()).replace('/', '\\')
print(clean_target)
lnk = pylnk3.for_file(clean_target)
lnk.save("test_mac.lnk")
