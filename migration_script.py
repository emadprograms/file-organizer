
import os
import re
import glob

def migrate_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    
    # 1. Ensure 'import logging' is present
    if 'import logging' not in content:
        lines = content.splitlines()
        insert_pos = 0
        for i, line in enumerate(lines):
            if not line.startswith(('import ', 'from ')):
                insert_pos = i
                break
        lines.insert(insert_pos, 'import logging')
        content = '
'.join(lines)

    # 2. Ensure logger = logging.getLogger(f"file_organizer.{__name__}")
    logger_stmt = 'logger = logging.getLogger(f"file_organizer.{__name__}")'
    if logger_stmt not in content:
        content = re.sub(r'log\s*=\s*logging\.getLogger\(.*?\)', logger_stmt, content)
        if logger_stmt not in content:
            lines = content.splitlines()
            insert_pos = -1
            for i, line in enumerate(lines):
                if line.strip() == '' and i > 0:
                    insert_pos = i
                    break
            if insert_pos == -1:
                for i, line in enumerate(lines):
                    if not line.startswith(('import ', 'from ')):
                        insert_pos = i
                        break
            if insert_pos == -1:
                insert_pos = len(lines)
            lines.insert(insert_pos, logger_stmt)
            content = '
'.join(lines)

    # 3. Replace 'log.info' -> 'logger.info' etc.
    content = re.sub(r'\blog\.(info|debug|warning|error|exception|critical)\b', r'logger.\1', content)

    # 4. Purge raw prints in src/ (not console.print or vprint)
    if 'src/' in filepath:
        content = re.sub(r'(?<!\.)\bprint\s*\(', 'logger.info(', content)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    modified_files = []
    files = glob.glob('src/**/*.py', recursive=True) + glob.glob('tests/**/*.py', recursive=True)
    for f in files:
        if 'src/logger.py' in f:
            continue
        if migrate_file(f):
            modified_files.append(f)
    print(f"Modified {len(modified_files)} files.")
    for f in modified_files:
        print(f)

if __name__ == '__main__':
    main()
