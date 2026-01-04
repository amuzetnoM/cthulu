from cthulu.rpc.server import run_rpc_server
import time

class DBStub:
    def __init__(self):
        self._id = 1
    def record_provenance(self, row):
        cur = self._id
        self._id += 1
        print('record_provenance called with', row)
        return cur

if __name__ == '__main__':
    db = DBStub()
    # Support optional TLS via environment variables
    import os
    sec_cfg = {}
    if os.getenv('MTLS_ENABLED', 'false').lower() in ('1','true','yes'):
        sec_cfg = {
            'tls_enabled': True,
            'tls_cert_path': os.getenv('MTLS_SERVER_CERT', 'c:/workspace/cthulu/_dev/mtls_test/server.cert.pem'),
            'tls_key_path': os.getenv('MTLS_SERVER_KEY', 'c:/workspace/cthulu/_dev/mtls_test/server.key.pem'),
            'require_client_cert': True,
            'client_ca_path': os.getenv('MTLS_CA_CERT', 'c:/workspace/cthulu/_dev/mtls_test/ca.cert.pem'),
            'tls_min_version': os.getenv('MTLS_MIN_VERSION', 'TLSv1.2'),
            'audit_enabled': True,
        }
    t, server = run_rpc_server('127.0.0.1', 8000, None, None, None, None, database=db, security_config=sec_cfg)
    print('RPC server started on 127.0.0.1:8000 (mtls=' + str(bool(sec_cfg)) + ')')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.shutdown()
        print('RPC server stopped')
