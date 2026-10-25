import os, glob

template_files = glob.glob('templates/**/*.html', recursive=True)
print(f'Found {len(template_files)} template files')
for f in template_files:
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    updated = content.replace('${{', '\u20b9{{')
    if updated != content:
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(updated)
        print(f'Fixed template: {f}')
    else:
        print(f'No dollar found: {f}')

py_fixes = ['reports/generator.py', 'audit_engine/rules.py']
for f in py_fixes:
    if not os.path.exists(f):
        continue
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    # Replace dollar in f-string patterns
    updated = content.replace('${', '\u20b9{')
    if updated != content:
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(updated)
        print(f'Fixed Python: {f}')
    else:
        print(f'No dollar found: {f}')

print('Currency replacement complete.')
