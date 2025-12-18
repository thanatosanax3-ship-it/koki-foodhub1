from pathlib import Path
root = Path('core/templates')
bad = []
for p in root.rglob('*'):
    if p.is_file():
        try:
            b = p.open('rb').read(4)
            if not b:
                continue
            if b[0]==0xFF:
                bad.append((str(p),'jpeg-looking',b[:4]))
                continue
            if b.startswith(b'\x89PNG'):
                bad.append((str(p),'png-looking',b[:4])); continue
            try:
                p.open('r', encoding='utf-8').read()
            except Exception as e:
                bad.append((str(p),'not-utf8',str(e)))
        except Exception as e:
            bad.append((str(p),'read-error',str(e)))

if not bad:
    print('No binary/non-UTF8 files found in core/templates')
else:
    print('Found issues:')
    for i in bad:
        print(i)
