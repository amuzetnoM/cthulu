from pathlib import Path
p = Path('observability/metrics.py')
text = p.read_text()
lines = text.splitlines()
res = []
for i,l in enumerate(lines):
    if l.strip().startswith('try:'):
        found = False
        for j in range(i+1, min(len(lines), i+40)):
            if lines[j].strip().startswith('except') or lines[j].strip().startswith('finally'):
                found = True
                break
        if not found:
            res.append(i+1)
print('orphan_try_lines:', res)
# Also print surrounding context for each orphan
for ln in res:
    start = max(1, ln-5)
    end = min(len(lines), ln+10)
    print('\nContext for line', ln)
    for k in range(start, end+1):
        print(f"{k:4d}: {lines[k-1]}")
