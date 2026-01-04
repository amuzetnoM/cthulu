"""Orchestrate a quick mTLS end-to-end test:
1. Generate test certs
2. Start RPC server stub with TLS and requiring client cert
3. Insert a test provenance row into discord/provenance.db
4. Run push_provenance_to_rpc.py with client cert and CA
5. Report success/failure and stop server
"""
import subprocess
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / '_dev' / 'mtls_test'
GEN = ROOT / 'scripts' / 'gen_mtls_test_certs.py'
RUN = ROOT / 'scripts' / 'run_rpc_stub.py'
PUSH = ROOT.parent / 'discord' / 'scripts' / 'push_provenance_to_rpc.py'

if __name__ == '__main__':
    # 1. generate certs
    print('Generating certs...')
    r = subprocess.run([sys.executable, str(GEN), '--out', str(OUT)])
    if r.returncode:
        print('Failed to generate certs')
        sys.exit(1)

    # 2. start RPC server stub with TLS enabled
    env = os.environ.copy()
    env['MTLS_ENABLED'] = 'true'
    env['MTLS_SERVER_CERT'] = str(OUT / 'server.cert.pem')
    env['MTLS_SERVER_KEY'] = str(OUT / 'server.key.pem')
    env['MTLS_CA_CERT'] = str(OUT / 'ca.cert.pem')

    print('Starting RPC server stub...')
    p = subprocess.Popen([sys.executable, str(RUN)], env=env)
    print('RPC pid', p.pid)

    try:
        time.sleep(2)
        # 3. Insert test provenance row into the discord local db
        print('Inserting test provenance row into local replica...')
        sys.path.insert(0, str(ROOT.parent / 'discord'))
        try:
            from scripts.test_provenance import test_insert
            test_insert()
        except Exception as e:
            print('Failed to insert via test_provenance helper:', e)
            # fallback to direct insert
            from provenance_db import get_db
            db = get_db()
            rowid = db.record_provenance({
                'timestamp': '2026-01-04T00:00:00Z',
                'signal_id': 'mtls-test',
                'client_tag': 'mtls-bot',
                'symbol': 'EURUSD',
                'side': 'BUY',
                'volume': 0.1,
                'metadata': {'notes': 'mtls test'}
            })
            print('Inserted fallback row', rowid)

        # 4. Run push script with client cert args
        env2 = os.environ.copy()
        env2['MTLS_CLIENT_CERT'] = str(OUT / 'client.cert.pem')
        env2['MTLS_CLIENT_KEY'] = str(OUT / 'client.key.pem')
        env2['MTLS_CA_CERT'] = str(OUT / 'ca.cert.pem')
        env2['OPS_API_URL'] = 'https://127.0.0.1:8000'

        print('Running push_provenance_to_rpc.py...')
        r2 = subprocess.run([sys.executable, str(PUSH)], env=env2, capture_output=True, text=True)
        print('stdout:\n', r2.stdout)
        print('stderr:\n', r2.stderr)
        if r2.returncode == 0 and 'Push result' in r2.stdout:
            print('mTLS push test succeeded')
        else:
            print('mTLS push test failed (nonzero exit or no Push result)')
    finally:
        print('Stopping RPC server...')
        p.terminate()
        try:
            p.wait(timeout=5)
        except Exception:
            p.kill()
        print('Done')
