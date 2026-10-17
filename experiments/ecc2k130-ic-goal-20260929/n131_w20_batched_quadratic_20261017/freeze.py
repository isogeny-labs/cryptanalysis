"""Freeze a paired native N131 source-span oracle comparison."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
ROOT=D.parent
OLD=ROOT/'n131_w20_quadratic_algebra_20261014'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


paths={'batch_source':D/'batched.cpp','batch_binary':D/'batched',
       'baseline_source':OLD/'linearized.cpp','baseline_binary':OLD/'linearized',
       'fixture':ROOT/'n131_w20_inverse_membership_join_20261014'/'fixture.txt',
       'support':ROOT/'n131_w20_sevenpair_gate_20261010'/'support_w20.tsv',
       'valid':ROOT/'n131_w20_code_trace_bitset_20261014'/'valid_bitmap.bin',
       'baseline_positive':OLD/'result_positive.json',
       'baseline_ordinary':OLD/'result_ordinary.json',
       'n41_audit':ROOT/'n41_n131_linearized_quadratic_algebra_20261014'/'audit_result.json'}
record={'schema':1,'candidate_id':None,'curve_id':'EC1N131Ckb1heb5f1998f20b',
        'seed_mask':898618,'right_rotation':18,
        'compiler':'clang++ -O3 -std=c++17 -DNDEBUG',
        'sources':{key:{'path':str(path),'sha256':sha(path)} for key,path in paths.items()},
        'runner_sha256':sha(D/'run.py'),
        'order':[['baseline','positive'],['batch','positive'],
                 ['batch','ordinary'],['baseline','ordinary']],
        'worker_count':1,'cap_s_per_query':600,'rss_cap_bytes':4*1024**3,
        'timing_boundary':'binary startup, source-table construction, and target-dependent query are included in parent wall; binary emits exclusive setup_ns and query_ns'}
(D/'protocol.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(json.dumps({'protocol_sha256':sha(D/'protocol.json')}))
