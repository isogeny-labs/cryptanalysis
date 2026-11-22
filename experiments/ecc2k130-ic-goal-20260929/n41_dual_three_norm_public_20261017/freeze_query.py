"""Freeze the ordinary public N41 SAT query after witness control."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
SOLVER=Path('/opt/homebrew/bin/cryptominisat5')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


build=json.loads((D/'build_result.json').read_text())
receipt=json.loads((D/'build_retry_receipt.json').read_text())
assert build['status']=='N41_DUAL_NORM_PUBLIC_CIRCUIT_CONTROL_PASS'
assert receipt['status']=='COMPLETE'
assert build['formula_sha256']==sha(D/'public.xcnf')
record={'schema':1,'candidate_id':None,
        'curve_id':'EC1N41Ckb1h7d5e80d3c4d0',
        'public_raw_target':json.loads((D/'protocol.json').read_text())['public_raw_target'],
        'producer_sha256':sha(D/'run_query.py'),
        'formula_sha256':sha(D/'public.xcnf'),
        'build_result_sha256':sha(D/'build_result.json'),
        'build_receipt_sha256':sha(D/'build_retry_receipt.json'),
        'solver_path':str(SOLVER),'solver_sha256':sha(SOLVER),
        'flags':['--threads=1','--maxtime=180','--maxnummatrices=0',
                 '--zero-exit-status','--verb=1','--printsol=1'],
        'worker_count':1,'solver_cap_s':180,'parent_cap_s':190,
        'rss_cap_bytes':4*1024**3}
(D/'query_protocol.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(json.dumps({'protocol_sha256':sha(D/'query_protocol.json')}))
