import hashlib, json
from pathlib import Path

root=Path('/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929')
base=root/'n41_four_code_suffix_quotient_20261024'
cfg=json.loads((base/'traversal_protocol.json').read_text())
for name,source in cfg['sources'].items():
    path=Path(source['path'])
    assert hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256'],name
geo=json.loads((root/'n41_w8_fixed_sum_table_20261009/geometry.json').read_text())
table=json.loads((base/'target_table.json').read_text())
cases=[json.loads(x) for x in (root/'n41_w8_two_code_affine_span_20261013/cases.jsonl').read_text().splitlines()]
assert len(geo['blocks'])==7 and len(cases)==1554
assert all(len(geo['blocks'][axis]['states'])==160 for axis in range(4))
assert len(table['rows'])==40 and all(len(row)==4 for row in table['rows'])
out=Path('/private/tmp/n41_fouraxis_native_input_20261025.tsv')
with out.open('w') as f:
    print('N41_4',160,*table['raw_target'],file=f)
    for axis in range(7):
        ids=range(160) if axis<4 else [table['suffix_state_ids'][axis-4]]
        for sid in ids:
            row=geo['blocks'][axis]['states'][sid]
            assert len(row['columns'])==2
            print('S',axis,sid,*row['columns'],*row['raw_sum'],file=f)
    for row in table['rows']:
        for entry in row:
            print('T',entry['state_id'],*entry['raw_point'],file=f)
    for case in cases:
        print('C',case['left_code'],case['right_code'],file=f)
print(json.dumps({'status':'PASS','input':str(out),'bytes':out.stat().st_size,
    'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'cases':len(cases),
    'target':table['raw_target']}))
