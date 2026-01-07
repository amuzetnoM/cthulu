import json
import glob
import os
base = os.path.dirname(os.path.dirname(__file__))
pattern = os.path.join(base, 'configs', 'mindsets', '**', 'config_*.json')
files = glob.glob(pattern, recursive=True)
count = 0
for f in files:
    # skip files already example
    if f.endswith('.example.json'):
        continue
    try:
        with open(f, 'r', encoding='utf-8') as fh:
            j = json.load(fh)
    except Exception:
        continue
    # sanitize
    if 'mt5' in j:
        j['mt5'] = {
            'login': '${MT5_LOGIN}',
            'password': '${MT5_PASSWORD}',
            'server': '${MT5_SERVER}',
            'timeout': j.get('mt5', {}).get('timeout', 60000),
            'path': '${MT5_PATH}'
        }
    if 'database' in j:
        j['database'] = {'path': '${DATABASE_PATH}'}
    # add example note
    j['_example_note'] = 'This is an example config derived from %s. Replace placeholders and copy to runtime config.json.' % os.path.basename(f)
    out = f.replace('.json', '.example.json')
    with open(out, 'w', encoding='utf-8') as fh:
        json.dump(j, fh, indent=2)
    count += 1
print(f'Created {count} example files')
