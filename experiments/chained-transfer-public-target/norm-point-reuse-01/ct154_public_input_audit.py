#!/usr/bin/env python3
"""Independent CT154 public-Q validation, negative controls and fresh-process study.

The C++ process sees only (x0,x1,x2,y0,y1,y2); the known scalar is held
in this auditor for after-the-fact independent verification. [pcc:unverified]
"""
import argparse
import hashlib
import importlib.util
import json
import platform
import random
import statistics
import subprocess
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('ct153_independent',HERE/'ct153_reference_audit.py')
ref=importlib.util.module_from_spec(spec)
spec.loader.exec_module(ref)
ARMS=('bsgs','rho','neg-rho')

def run(exe,arm,point,timeout=8):
    qargs=[str(c) for f in point for c in f]
    t0=time.perf_counter_ns()
    p=subprocess.run([str(exe),'--arm',arm,*qargs],capture_output=True,text=True,timeout=timeout)
    wall=time.perf_counter_ns()-t0
    if p.returncode:raise AssertionError(f'complete solver failed for {arm}: {p.stderr}')
    receipt=json.loads(p.stdout)
    if receipt['schema']!='ct154-q223-public-point/v1' or receipt['arm']!=arm:
        raise AssertionError('wrong output schema or arm')
    if receipt['source_public']!=[list(a) for a in point]:
        raise AssertionError('point was altered across solver boundary')
    if receipt['field']!=223 or receipt['degree']!=3 or receipt['subgroup_order']!=ref.ELL:
        raise AssertionError('source identity changed')
    if receipt['standing']!='pcc:unverified' or receipt['verified'] is not True:
        raise AssertionError('invalid self-report fields')
    if not ref.on(point) or ref.scalar(point,ref.ELL) is not None:
        raise AssertionError('public Q invalid on Python field/group law')
    if ref.scalar(ref.G,receipt['recovered'])!=point:
        raise AssertionError('recovered scalar is wrong by independent Python group law')
    for name in ('solver_ns','process_ns','field_mul','field_inv','point_add','point_double','steps','restarts','table_entries','peak_rss_kb'):
        if not isinstance(receipt[name],int) or receipt[name]<0:raise AssertionError(f'bad cost field {name}')
    if receipt['process_ns']<receipt['solver_ns']:raise AssertionError('invalid process accounting')
    receipt['harness_wall_ns']=wall
    return receipt

def must_reject(exe,args):
    p=subprocess.run([str(exe),*args],capture_output=True,text=True,timeout=8)
    if p.returncode==0 or 'ct154 REJECTED' not in p.stderr:
        raise AssertionError(f'control accepted: {args}')

def find_outside():
    for a in range(30):
        x=(a,0,0)
        x2=ref.field_mul(x,x)
        rhs=ref.field_add(ref.field_add(ref.field_mul(x2,x),ref.field_mul(ref.A2,x2)),ref.field_add(ref.field_mul(ref.A4,x),ref.A6))
        y=ref.field_pow(rhs,(ref.P**3+1)//4)
        q=(x,y)
        if ref.on(q) and ref.scalar(q,ref.ELL) is not None:return q
    raise AssertionError('expected outside-subgroup point not found')

def bootstrap(values,n=4000):
    rr=random.Random(154)
    samples=[]
    for _ in range(n):
        samples.append(statistics.median(values[rr.randrange(len(values))] for j in values))
    samples.sort()
    return [samples[100],samples[3899]]

def main():
    p=argparse.ArgumentParser()
    p.add_argument('binary',type=Path)
    p.add_argument('--quick',action='store_true')
    p.add_argument('--output',type=Path)
    args=p.parse_args()
    exe=args.binary.resolve()
    t=subprocess.run([str(exe),'--self-test'],capture_output=True,text=True,timeout=10)
    if t.returncode or json.loads(t.stdout)!={'schema':'ct154-self-test/v1','public_cases':6,'walk_invariant':True,'complete_solve':True}:
        raise AssertionError(f'C++ self-test failed {t.stderr}')
    q=ref.scalar(ref.G,17)
    if q is None:raise AssertionError('unexpected infinity')
    coords=[str(c) for f in q for c in f]
    outside=find_outside()
    wrong=[str(c) for f in outside for c in f]
    offcurve=coords.copy();offcurve[3]=str((int(offcurve[3])+1)%223)
    negatives=[
        ['--arm','bsgs',*coords[:-1]],
        ['--arm','nonsense',*coords],
        ['--arm','neg-rho','223',*coords[1:]],
        ['--arm','rho','-1',*coords[1:]],
        ['--arm','bsgs','abc',*coords[1:]],
        ['--arm','neg-rho',*offcurve],
        ['--arm','rho',*wrong],
        ['--arm','neg-rho','000223',*coords[1:]],
    ]
    for neg in negatives:must_reject(exe,neg)
    cases=ref.SCALARS[:2] if args.quick else ref.SCALARS
    blocks=1 if args.quick else 2
    rows=[]
    for k in cases:
        public=ref.scalar(ref.G,k)
        assert public is not None
        for block in range(blocks):
            order=('bsgs','rho','neg-rho','neg-rho','rho','bsgs')
            if block%2:order=('neg-rho','rho','bsgs','bsgs','rho','neg-rho')
            for pos,arm in enumerate(order):
                rec=run(exe,arm,public)
                if rec['recovered']!=k:raise AssertionError('known-answer scalar mismatch')
                rec['fixture_audit_only']=k
                rec['block']=block
                rec['position']=pos
                rows.append(rec)
    for k in cases:
        for block in range(blocks):
            sub=[z for z in rows if z['fixture_audit_only']==k and z['block']==block]
            if sorted(z['arm'] for z in sub)!=['bsgs','bsgs','neg-rho','neg-rho','rho','rho']:
                raise AssertionError('incomplete paired block')
    med=lambda arm,key:statistics.median(z[key] for z in rows if z['arm']==arm)
    pairs={name:[] for name in ('rho','neg-rho')}
    aa=[]
    for k in cases:
        for block in range(blocks):
            sub=[z for z in rows if z['fixture_audit_only']==k and z['block']==block]
            armvals={arm:[z['harness_wall_ns'] for z in sub if z['arm']==arm] for arm in ARMS}
            for arm,v in armvals.items():
                aa.append(abs(v[0]-v[1]))
            for arm in pairs:
                pairs[arm].append(statistics.mean(armvals['bsgs'])-statistics.mean(armvals[arm]))
    summary={
        'schema':'ct154-public-input-audited/v1','standing':'[pcc:unverified]',
        'scope':'E(F223^3) original CT152 source; public-point-only cold source solves; not transferred Jacobian',
        'records':len(rows),'targets':len(cases),'blocks_per_target':blocks,'negative_controls':len(negatives),
        'all_source_solutions_python_verified':True,'no_scalar_passed_to_cpp':True,
        'arm_median_harness_wall_ns':{arm:med(arm,'harness_wall_ns') for arm in ARMS},
        'arm_median_solver_ns':{arm:med(arm,'solver_ns') for arm in ARMS},
        'arm_median_field_inv':{arm:med(arm,'field_inv') for arm in ARMS},
        'arm_max_rss_kb':{arm:max(z['peak_rss_kb'] for z in rows if z['arm']==arm) for arm in ARMS},
        'bsgs_minus_other_median_pair_wall_ns':{arm:statistics.median(v) for arm,v in pairs.items()},
        'bsgs_minus_other_fixed_case_bootstrap95_ns':{arm:bootstrap(v) for arm,v in pairs.items()},
        'aa_abs_median_wall_ns':statistics.median(aa),
        'original_cpp_git_source':'ct153_original_cold_reference.cpp unchanged',
        'host':platform.platform(),'cxx':'g++ -std=c++17 -O3 -Wall -Wextra -Werror',
        'binary_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),
        'rows_sha256':hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        'limitations':'Unisolated developer CPU; source only, 6 fixed targets, not strongest rho or any transfer; no signed PCC',
    }
    if args.output:args.output.write_text(json.dumps({'summary':summary,'rows':rows},sort_keys=True,indent=2)+'\n')
    print(json.dumps(summary,sort_keys=True,separators=(',',':')))
if __name__=='__main__':main()
