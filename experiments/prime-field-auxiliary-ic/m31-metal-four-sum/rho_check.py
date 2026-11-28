#!/usr/bin/env python3
"""Independent affine replay and matched identity check for rho distance run."""
import json
from pathlib import Path
import statistics
from independent_check import G,mul

HERE=Path(__file__).resolve().parent
rho=[json.loads(line) for line in (HERE/'RHO_RAW.jsonl').read_text().splitlines()]
ic=[json.loads(line) for line in (HERE/'CONFIRM2_RAW.jsonl').read_text().splitlines()]
seeds=json.loads((HERE/'CONFIRM2_MANIFEST.json').read_text())['seeds']
assert len(rho)==15
ratios=[]
for row in rho:
    assert row['returncode']==0 and not row['timeout'] and row['metrics']
    scalar=row['metrics']['recovered']; q=tuple(row['Q'])
    assert mul(scalar,G)==q
    matched=[x for x in ic if x['mode']=='metal' and x['target']==row['target'] and seeds[x['seed']]==row['seed']]
    assert len(matched)==1
    assert json.loads(matched[0]['stdout'])['scalar']==scalar
    ratios.append((matched[0]['wall_ns']/row['wall_ns'],matched[0]['cpu_ns']/row['cpu_ns']))
print(json.dumps({'rho_arms':15,'independent_group_checks':15,'matched_pairs':15,
                  'rho_median_wall_ms':statistics.median(x['wall_ns'] for x in rho)/1e6,
                  'rho_median_cpu_ms':statistics.median(x['cpu_ns'] for x in rho)/1e6,
                  'metal_over_rho_paired_wall':statistics.median(x for x,y in ratios),
                  'metal_over_rho_paired_cpu':statistics.median(y for x,y in ratios),
                  'status':'pass'}))
