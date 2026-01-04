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
    t, server = run_rpc_server('127.0.0.1', 8000, None, None, None, None, database=db)
    print('RPC server started on 127.0.0.1:8000')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.shutdown()
        print('RPC server stopped')
