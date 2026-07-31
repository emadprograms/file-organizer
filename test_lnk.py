import pylnk3
from pylnk3 import create, LinkInfo, ExtraData, ExtraData_EnvironmentVariableDataBlock

def create_shortcut(target_path, link_path):
    if target_path.startswith(r"\\?\C:"):
        # Strip it to let pylnk3 build the local drive segments correctly
        clean_target = target_path[4:]
    else:
        clean_target = target_path
    
    lnk = pylnk3.for_file(clean_target)
    
    # Force the unicode path to have the long path prefix
    env_data_block = ExtraData_EnvironmentVariableDataBlock()
    env_data_block.target_ansi = target_path
    env_data_block.target_unicode = target_path
    lnk.extra_data = ExtraData(blocks=[env_data_block])
    lnk.link_flags.HasExpString = True
    
    lnk.save(link_path)

create_shortcut(r"\\?\C:\fake\long\target.pdf", "test2.lnk")
print(pylnk3.parse("test2.lnk").path)
