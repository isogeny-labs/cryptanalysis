"""Bind the prospective source and held certificate before evaluating signs."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
ROOT=D.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert json.loads((D/'holdout_prepare_receipt.json').read_text())['status']=='COMPLETE'
sources=[D/'holdout_source.json',D/'result.json',D/'audit_result.json',
         ROOT/'n41_n131_sixpair_rr_root_span_20261016'/'run.py']
record={'schema':1,'producer_sha256':sha(D/'holdout.py'),
        'sources':{str(path):sha(path) for path in sources},
        'first_slot_roots':[0,1],'sign_masks':list(range(64)),
        'fitted_certificate':'root balanced four-code 16-AND circuit'}
(D/'eval_protocol.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(json.dumps({'protocol_sha256':sha(D/'eval_protocol.json')}))
