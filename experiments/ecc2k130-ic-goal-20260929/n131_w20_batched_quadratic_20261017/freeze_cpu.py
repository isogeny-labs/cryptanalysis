"""Freeze a second paired run with child CPU accounting."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


prior=json.loads((D/'run_result.json').read_text())
assert prior['status']=='COMPLETE' and len(prior['rows'])==4
record={'schema':1,'prior_protocol_sha256':sha(D/'protocol.json'),
        'prior_result_sha256':sha(D/'run_result.json'),
        'runner_sha256':sha(D/'cpu_pair.py'),
        'order':[['baseline','ordinary'],['batch','ordinary'],
                 ['batch','positive'],['baseline','positive']],
        'worker_count':1,'cap_s_per_query':180,
        'rss_cap_bytes':4*1024**3,
        'measurement':'parent monotonic wall and per-child user/system CPU deltas from RUSAGE_CHILDREN'}
(D/'cpu_protocol.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(json.dumps({'protocol_sha256':sha(D/'cpu_protocol.json')}))
