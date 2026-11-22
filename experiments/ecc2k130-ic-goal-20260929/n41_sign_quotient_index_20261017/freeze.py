"""Freeze source and archived public-point input before native compilation."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
OLD=D.parent/'n41_sixpair_shared_target_20261017'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


archive=json.loads((OLD/'join_prepare_result.json').read_text())
assert sha(OLD/'join_input.tsv')==archive['input_sha256']
record={'schema':1,'candidate_id':None,
        'curve_id':'EC1N41Ckb1h7d5e80d3c4d0',
        'public_raw_target':archive['public_raw_point'],
        'source_sha256':sha(D/'sign_join.cpp'),
        'runner_sha256':sha(D/'run.py'),
        'included_source_sha256':sha(OLD/'join_exact.cpp'),
        'input_sha256':sha(OLD/'join_input.tsv'),
        'input_path':str(OLD/'join_input.tsv'),
        'geometry_sha256':archive['geometry_sha256'],
        'compile_command':['/usr/bin/clang++','-O3','-std=c++17','-DNDEBUG',
                           'sign_join.cpp','-o','sign_join'],
        'worker_count':1,'wall_cap_s':60,'rss_cap_bytes':4*1024**3}
(D/'protocol.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(json.dumps({'protocol_sha256':sha(D/'protocol.json')}))
