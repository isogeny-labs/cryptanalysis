#!/usr/bin/env python3
"""Recheck matched archived rho answers and IC/rho identities."""
import json
from pathlib import Path
import statistics
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'m31-metal-four-sum'))
from independent_check import G,mul

ic={}
for line in (HERE/'XHASH_RAW.jsonl').read_text().splitlines():
    row=json.loads(line)
    if row['arm']=='xhash22':
        ic[row['target'],row['seed']]=row
rho=[json.loads(line) for line in (HERE/'RHO_RAW.jsonl').read_text().splitlines()]
assert len(ic)==len(rho)==15
ratios=[]
for row in rho:
    assert row['returncode']==0 and not row['timeout']
    scalar=row['metrics']['recovered']
    assert mul(scalar,G)==tuple(row['Q'])
    candidate=ic[row['target'],row['seed']]
    assert candidate['Q']==row['Q']
    assert json.loads(candidate['stdout'])['scalar']==scalar
    ratios.append((candidate['wall_ns']/row['wall_ns'],candidate['cpu_ns']/row['cpu_ns']))
print(json.dumps({'matched':len(ratios),'public_group_checks':len(rho),
                  'median_ic_over_rho_wall':statistics.median(x[0] for x in ratios),
                  'median_ic_over_rho_cpu':statistics.median(x[1] for x in ratios),
                  'status':'pass'}))
