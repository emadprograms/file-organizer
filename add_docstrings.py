import os
import re
import glob

def process_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        m = re.match(r'^(\s*)def\s+([a-zA-Z0-9_]+)\((.*)\)(?:[^-:]*)?:(.*)$', line)
        if m and not line.strip().endswith(':\\'):
            indent = m.group(1)
            func_name = m.group(2)
            params = m.group(3)
            rest = m.group(4)
            
            has_return_type = '->' in line
            
            if not has_return_type:
                if func_name.startswith('test_'):
                    line = f"{indent}def {func_name}({params}) -> None:{rest}\n"
                elif 'fixture' in filepath or func_name.startswith('mock_') or 'setup' in func_name or 'teardown' in func_name:
                    if 'mock_' in func_name:
                        line = f"{indent}def {func_name}({params}) -> None:{rest}\n"
                    else:
                        line = f"{indent}def {func_name}({params}) -> Any:{rest}\n"
                else:
                    line = f"{indent}def {func_name}({params}) -> Any:{rest}\n"
            
            new_lines.append(line)
            
            if i + 1 < len(lines) and '"""' in lines[i+1]:
                i += 1
                continue
                
            human_name = func_name.replace('test_', '').replace('_', ' ')
            if func_name.startswith('test_'):
                docstring = f'{indent}    """\n{indent}    Test {human_name}.\n\n{indent}    Expected outcome:\n{indent}    The function should execute successfully and meet all assertions.\n{indent}    """\n'
            else:
                docstring = f'{indent}    """\n{indent}    Provide the {human_name} fixture/mock.\n\n{indent}    Returns:\n{indent}    The appropriate fixture or mock value.\n{indent}    """\n'
            
            new_lines.append(docstring)
            i += 1
            continue
            
        new_lines.append(line)
        i += 1
        
    with open(filepath, 'w') as f:
        f.writelines(new_lines)

files = glob.glob('tests/test_routing_*.py')
for f in files:
    process_file(f)

