#!/usr/bin/env python3
"""CT153 independent source-point verification and paired, fresh-process diagnostic.
No cryptographic solver implementation here. CT152 field equations reconstructed
separately; no fixture scalar is given to the C++ solving functions.
"""
import argparse
import hashlib
import json
import math
import platform
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path

P=223
ELL=2773073
SCALARS=(1,17,12345,159273,2300011,2773072)
G=((162,197,140),(45,11,207))
A2=(127,56,199); A4=(152,35,36); A6=(212,109,150)
ZERO=(0,0,0); ONE=(1,0,0)
def field_add(x,y):return tuple((a+b)%P for a,b in zip(x,y))
def field_neg(x):return tuple(-a%P for a in x)
def field_sub(x,y):return field_add(x,field_neg(y))
def field_mul(x,y):
    x0,x1,x2=x; y0,y1,y2=y
    return ((x0*y0+3*(x1*y2+x2*y1))%P,
            (x0*y1+x1*y0+3*x2*y2)%P,
            (x0*y2+x1*y1+x2*y0)%P)
def field_pow(x,n):
    a=ONE
    while n:
        if n&1:a=field_mul(a,x)
        x=field_mul(x,x);n//=2
    return a
def field_inv(x):
    if x==ZERO:raise ValueError('division by field zero')
    return field_pow(x,P**3-2)
def on(Q):
    if Q is None:return True
    x,y=Q; x2=field_mul(x,x)
    rhs=field_add(field_add(field_mul(x2,x),field_mul(A2,x2)),field_add(field_mul(A4,x),A6))
    return field_mul(y,y)==rhs
def add(Q,R):
    if Q is None:return R
    if R is None:return Q
    x,y=Q;u,v=R
    if x==u and field_add(y,v)==ZERO:return None
    if x==u:
        num=field_add(field_add(field_mul((3,0,0),field_mul(x,x)),field_mul((2,0,0),field_mul(A2,x))),A4)
        den=field_mul((2,0,0),y)
    else:num=field_sub(v,y);den=field_sub(u,x)
    m=field_mul(num,field_inv(den))
    xx=field_sub(field_sub(field_sub(field_mul(m,m),A2),x),u)
    return (xx,field_sub(field_mul(m,field_sub(x,xx)),y))
def scalar(Q,n):
    s=None
    while n:
        if n&1:s=add(s,Q)
        n>>=1
        if n:Q=add(Q,Q)
    return s

def read_run(exe,arm,k):
    begin=time.perf_counter_ns()
    p=subprocess.run([str(exe),'--arm',arm,str(k)],capture_output=True,text=True,timeout=15)
    wall=time.perf_counter_ns()-begin
    if p.returncode!=0:raise RuntimeError(f'{arm} {k} exit {p.returncode}: {p.stderr}')
    v=json.loads(p.stdout)
    if v['schema']!='ct153-q223-source-cold/v1' or v['arm']!=arm or v['fixture']!=k or v['recovered']!=k or not v['verified']:
        raise ValueError('mismatched source answer or schema')
    if v['subgroup_order']!=ELL or v['source_full_order']!=4*ELL or v['degree']!=3 or v['field']!=P:
        raise ValueError('source group replaced')
    q=tuple(tuple(a) for a in v['source_public'])
    if not on(q) or q!=scalar(G,k) or scalar(G,v['recovered'])!=q or scalar(q,ELL) is not None:
        raise ValueError('independent Python field/group public-output verification failed')
    for f in ('field_mul','field_inv','point_add','point_double','solver_ns','process_ns','peak_rss_kb'):
        if v[f]<0:raise ValueError('negative receipt field '+f)
    v['harness_wall_ns']=wall
    return v

def require_failure(exe,arguments):
    p=subprocess.run([str(exe),*arguments],capture_output=True,text=True,timeout=15)
    if p.returncode==0 or 'REJECTED' not in p.stderr:raise ValueError('invalid CLI not rejected '+str(arguments))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('executable',type=Path)
    ap.add_argument('--quick',action='store_true',help='one ABBA block for 2 public targets, functional CI only')
    ap.add_argument('--output',type=Path)
    args=ap.parse_args()
    if not on(G) or scalar(G,ELL) is not None:raise ValueError('independent generator invalid')
    controls=subprocess.run([str(args.executable),'--self-test-negative'],capture_output=True,text=True,timeout=15)
    if controls.returncode!=0:raise ValueError('source negative-control execution failed: '+controls.stderr)
    verified_controls=json.loads(controls.stdout)
    if verified_controls!={'schema':'ct153-negative-controls/v1','a6_mutation':True,'off_curve_generator':True,'wrong_order':True,'out_of_subgroup_public':True}:
        raise ValueError('negative-control mutation record changed')
    for bad in (['--arm','bad','17'],['--arm','bsgs','0'],['--arm','rho','2773073'],['--arm','bsgs','-12'],['--arm','rho','wat']):
        require_failure(args.executable,bad)
    cases=SCALARS[:2] if args.quick else SCALARS
    blocks=1 if args.quick else 4
    rows=[]
    for k in cases:
        for b in range(blocks):
            arms=('bsgs','rho','rho','bsgs') if b%2==0 else ('rho','bsgs','bsgs','rho')
            for idx,arm in enumerate(arms):
                row=read_run(args.executable,arm,k)
                row['block']=b;row['position']=idx
                rows.append(row)
    for k in cases:
        public={tuple(map(tuple,r['source_public'])) for r in rows if r['fixture']==k}
        if len(public)!=1:raise ValueError('cross-arm public mismatch')
        for b in range(blocks):
            pair=[r for r in rows if r['fixture']==k and r['block']==b]
            if len(pair)!=4 or sorted(r['arm'] for r in pair)!=['bsgs','bsgs','rho','rho']:
                raise ValueError('incomplete ABBA/BAAB pair')
    deltas=[]
    aa=[]
    for k in cases:
        for b in range(blocks):
            block=[r for r in rows if r['fixture']==k and r['block']==b]
            a=[r['harness_wall_ns'] for r in block if r['arm']=='bsgs']
            z=[r['harness_wall_ns'] for r in block if r['arm']=='rho']
            deltas.append((a[0]+a[1])/2-(z[0]+z[1])/2)
            aa.extend([abs(a[0]-a[1]),abs(z[0]-z[1])])
    digest=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    # Within the six fixed public targets only: block-pair bootstrap, not population inference.
    rng=random.Random(153)
    medians=[]
    for _ in range(4000):
        draw=[deltas[rng.randrange(len(deltas))] for j in range(len(deltas))]
        medians.append(statistics.median(draw))
    medians.sort()
    ci=[medians[100],medians[3899]]
    summary={'schema':'ct153-audited-fresh-process-pairs/v1','standing':'[pcc:unverified]',
        'scope':'actual original q223 source E(F223^3), NOT actual transferred Jacobian, NOT optimized rho or IC',
        'count':len(rows),'targets':len(cases),'blocks_each':blocks,'negative_controls':9,
        'all_answers_independently_reverified':True,
        'paired_bsgs_minus_rho_wall_median_ns':statistics.median(deltas),
        'fixed_fixture_block_bootstrap95_pair_median_ns':ci,
        'fixed_fixture_block_bootstrap_scope':'4000 seeded resamples of fixed-target ABBA blocks (2 or 6); not target-population CI',
        'median_aa_abs_wall_drift_ns':statistics.median(aa),
        'bsgs_wall_median_ns':statistics.median(r['harness_wall_ns'] for r in rows if r['arm']=='bsgs'),
        'rho_wall_median_ns':statistics.median(r['harness_wall_ns'] for r in rows if r['arm']=='rho'),
        'bsgs_solver_median_ns':statistics.median(r['solver_ns'] for r in rows if r['arm']=='bsgs'),
        'rho_solver_median_ns':statistics.median(r['solver_ns'] for r in rows if r['arm']=='rho'),
        'bsgs_peak_rss_max_kb':max(r['peak_rss_kb'] for r in rows if r['arm']=='bsgs'),
        'rho_peak_rss_max_kb':max(r['peak_rss_kb'] for r in rows if r['arm']=='rho'),
        'bsgs_field_inv_median':statistics.median(r['field_inv'] for r in rows if r['arm']=='bsgs'),
        'rho_field_inv_median':statistics.median(r['field_inv'] for r in rows if r['arm']=='rho'),
        'compiler':'C++17 -O3 -Wall -Wextra -Werror',
        'host':platform.platform(),
        'binary_sha256':hashlib.sha256(args.executable.read_bytes()).hexdigest(),
        'rows_sha256':digest,
        'limits':'non-isolated developer CPU; fixed-case bootstrap only, no population CI or actual transfer; no independent signed PCC'}
    output={'summary':summary,'rows':rows}
    if args.output:args.output.write_text(json.dumps(output,sort_keys=True,indent=2)+'\n')
    print(json.dumps(summary,sort_keys=True,separators=(',',':')))
if __name__=='__main__':main()
