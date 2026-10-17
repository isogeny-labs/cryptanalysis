"""Freeze source selection and certificate before the prospective N131 holdout."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
ROOT=D.parent
ARCH=ROOT/'n41_n131_rr_code_family_span_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert json.loads((D/'audit_result.json').read_text())['status']=='BALANCED_SYMBOLIC_AUDIT_PASS'
sources=[ARCH/'panel_n131_v2.json',
         ROOT/'n41_n131_sixpair_rr_root_span_20261016'/'frozen_panels.json',
         D/'result.json',D/'audit_result.json']
record={'schema':1,'producer_sha256':sha(D/'prepare_holdout_sage.py'),
        'sources':{str(path):sha(path) for path in sources},
        'selection_start_mask':47,'selection_stop_mask_exclusive':256,
        'selection_seed_mask':898618,
        'selection_rule':'first ascending source-valid mask whose mate, subgroup folded orbit keys, and all twelve columns are distinct from four training codes and five suffix pairs',
        'holdout_roots':[0,1], 'holdout_signs':list(range(64)),
        'worker_count':1,'wall_cap_s':180,'rss_cap_bytes':4*1024**3}
(D/'holdout_prepare_protocol.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(json.dumps({'protocol_sha256':sha(D/'holdout_prepare_protocol.json')}))
