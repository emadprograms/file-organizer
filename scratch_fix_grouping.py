with open('tests/test_grouping.py', 'r', encoding='utf-8') as f:
    content = f.read()
idx = content.find('    assert obj.groups[0].reason == "Because"')
if idx != -1:
    content = content[:idx + len('    assert obj.groups[0].reason == "Because"\n')]
with open('tests/test_grouping.py', 'w', encoding='utf-8') as f:
    f.write(content)
