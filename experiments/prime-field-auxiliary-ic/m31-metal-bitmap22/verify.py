#!/usr/bin/env python3
"""Independent affine answer and paired certificate check for the 20/22 panel."""
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'m31-metal-four-sum'))
from independent_check import G,mul

manifest=json.loads((HERE/'MANIFEST.json').read_text())
rows=[json.loads(x) for x in (HERE/'RAW.jsonl').read_text().splitlines()]
assert len(rows)==30
pairs={}
for row in rows:
    assert row['returncode']==0 and not row['timeout']
    out=json.loads(row['stdout'])
    assert out['status']=='solved' and out['Q']==row['Q']
    assert out['seed']==row['seed']==manifest['seeds'][row['seed_index']]
    assert out['bitmap_bits']==row['bitmap_bits']
    assert mul(out['scalar'],G)==tuple(row['Q'])
    pairs.setdefault((row['target'],row['seed_index']),{})[row['bitmap_bits']]=out
assert len(pairs)==15
for key,pair in pairs.items():
    assert set(pair)=={20,22},key
    for field in ['scalar','certificate_digest','queries','relations','rank']:
        assert pair[20][field]==pair[22][field],(key,field)
print(json.dumps({'arms':30,'pairs':15,'independent_public_group_checks':30,
                  'complete_field_digest_matches':15,'status':'pass'}))
