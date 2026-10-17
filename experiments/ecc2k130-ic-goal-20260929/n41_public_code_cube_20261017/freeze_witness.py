"""Bind a retrospective satisfiable-cube control after all queries ended."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
OLD=D.parent/'n41_sixpair_shared_target_20261017'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
audit=json.loads((OLD/'join_audit_result.json').read_text())
g=json.loads((D.parent/'n41_w8_fixed_sum_table_20261009'/'geometry.json').read_text())
bits=[i for i in range(8) if i!=g['fixed_seed_sum_code'].bit_length()-1]
mask=audit['pair_rows'][0]['masks'][0]
code=sum(((mask>>bit)&1)<<j for j,bit in enumerate(bits))
record={'schema':1,'producer_sha256':sha(D/'witness_control.py'),
        'archive_sha256':sha(OLD/'join_audit_result.json'),
        'formula_sha256':sha(D/'rebuilt_public.xcnf'),
        'retrospective_witness_code':code,
        'campaign_result_sha256':sha(D/'campaign_result.json')}
(D/'witness_protocol.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(json.dumps({'retrospective_witness_code':code,
                  'witness_protocol_sha256':sha(D/'witness_protocol.json')}))
