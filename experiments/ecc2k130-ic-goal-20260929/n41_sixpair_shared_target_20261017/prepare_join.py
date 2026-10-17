"""Serialize the frozen 160 signed pair states in each of six slots."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
geometry_path=ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json'
g=json.loads(geometry_path.read_text())
assert g['rotations'][:6]==[0,6,12,18,24,30]
assert all(len(b['states'])==160 for b in g['blocks'][:6])
target=g['positive_control']['raw_target']
lines=[f'ECC2K41 6 160 {target[0]} {target[1]}']
for slot,block in enumerate(g['blocks'][:6]):
    for sid,state in enumerate(block['states']):
        a,b=state['a'],state['b']
        assert a in g['permitted_canonical_a'] and b==a^56
        assert state['columns']==[g['mask_columns'][str(a)],g['mask_columns'][str(b)]]
        row=['S',slot,sid,a,b,state['sign_a'],state['sign_b'],*state['columns'],*state['raw_sum']]
        lines.append(' '.join(map(str,row)))
data='\n'.join(lines)+'\n'
with (HERE/'join_input.tsv').open('x') as out:out.write(data)
result={'status':'PREPARED_N41_SIXPAIR_JOIN','state_count_per_slot':160,
        'public_raw_point':target,
        'input_sha256':hashlib.sha256(data.encode()).hexdigest(),
        'geometry_sha256':hashlib.sha256(geometry_path.read_bytes()).hexdigest()}
with (HERE/'join_prepare_result.json').open('x') as out:
    json.dump(result,out,sort_keys=True,indent=2);out.write('\n')
print(result['status'])
