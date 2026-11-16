#!/usr/bin/env python3
"""Independent finite-curve audit of CT155 projective BSGS vs CT154 affine BSGS.

Original public Q coordinates are passed to subprocesses; fixture scalar stays
in the separate Python auditor. Local diagnostics are not signed PCC.
"""
import argparse, hashlib, json, random, statistics, subprocess, time, platform
from pathlib import Path
import ct153_reference_audit as ref

def run(binary, point, arm):
    coords=[str(z) for f in point for z in f]
    args=[str(binary), *(['--arm','bsgs'] if arm=='affine' else []), *coords]
    t=time.perf_counter_ns()
    p=subprocess.run(args,capture_output=True,text=True,timeout=10)
    measured=time.perf_counter_ns()-t
    if p.returncode: raise AssertionError(f'{arm} failed: {p.stderr}')
    rec=json.loads(p.stdout)
    if rec['source_public']!=[list(f) for f in point] or ref.scalar(ref.G,rec['recovered'])!=point:
        raise AssertionError('independently checked scalar mismatch')
    if rec['standing']!='pcc:unverified' or rec['solver_ns']>rec['process_ns']:
        raise AssertionError('receipt malformed')
    for fld in ('field_mul','field_inv','point_add','point_double','steps','table_entries','peak_rss_kb'):
        if not isinstance(rec[fld],int) or rec[fld]<0:raise AssertionError('bad cost '+fld)
    rec['harness_wall_ns']=measured
    rec['arm_audit']=arm
    return rec

def reject(binary,argv):
    p=subprocess.run([str(binary),*argv],capture_output=True,text=True,timeout=10)
    if p.returncode==0 or not p.stderr.startswith('ct155 REJECTED:'):
        raise AssertionError('invalid input was accepted: '+repr(argv))

def outside_subgroup():
    for j in range(80):
        x=(j%ref.P,j//ref.P,0)
        x2=ref.field_mul(x,x)
        rhs=ref.field_add(ref.field_add(ref.field_mul(x2,x),ref.field_mul(ref.A2,x2)),ref.field_add(ref.field_mul(ref.A4,x),ref.A6))
        y=ref.field_pow(rhs,(ref.P**3+1)//4)
        q=(x,y)
        if ref.on(q) and ref.scalar(q,ref.ELL) is not None:return q
    raise AssertionError('negative fixture outside subgroup absent')

def neg_controls(binary):
    q=ref.scalar(ref.G,17); a=[str(z) for f in q for z in f]
    bad=a.copy();bad[3]=str((int(bad[3])+1)%223)
    other=[str(z) for f in outside_subgroup() for z in f]
    variants=[a[:-1], ['223',*a[1:]], ['-1',*a[1:]], ['abc',*a[1:]], ['+1',*a[1:]],bad,other,['000223',*a[1:]]]
    for variant in variants:reject(binary,variant)
    return len(variants)

def quantile_bootstrap(data,seed=155,repetitions=4000):
    rnd=random.Random(seed)
    medians=sorted(statistics.median(rnd.choice(data) for _ in data) for _ in range(repetitions))
    return [medians[99],medians[3899]]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--candidate',type=Path,required=True)
    ap.add_argument('--baseline',type=Path,required=True)
    ap.add_argument('--quick',action='store_true')
    ap.add_argument('--output',type=Path)
    args=ap.parse_args()
    c=args.candidate.resolve();b=args.baseline.resolve()
    test=subprocess.run([str(c),'--self-test'],capture_output=True,text=True,timeout=10,check=True)
    summary_test=json.loads(test.stdout)
    if summary_test!={'schema':'ct155-test/v1','jacobian_cases':10,'public_dlp_cases':6,'result':'pass','standing':'pcc:unverified'}:
        raise AssertionError('selftest receipt changed')
    controls=neg_controls(c)
    # Extra independently generated public scalar cases, not used to time the cohort.
    rnd=random.Random(15501)
    sample=[1,2,3,4,5,13,64,255,1665,1666,1667,ref.ELL-1]
    sample+=rnd.sample(range(1,ref.ELL),64 if args.quick else 256)
    for k in sample:
        public=ref.scalar(ref.G,k)
        rec=run(c,public,'projective')
        if rec['recovered']!=k:raise AssertionError('independent random scalar mismatch')
    targets=ref.SCALARS[:2] if args.quick else ref.SCALARS
    blocks=1 if args.quick else 4
    rows=[]
    for target_index,k in enumerate(targets):
        point=ref.scalar(ref.G,k)
        for blk in range(blocks):
            order=['affine','projective','projective','affine'] if blk%2==0 else ['projective','affine','affine','projective']
            for pos,arm in enumerate(order):
                r=run(b if arm=='affine' else c,point,arm)
                if r['recovered']!=k:raise AssertionError('fixture mismatch')
                r.update({'fixture_audit_only':k,'case_index':target_index,'block':blk,'position':pos})
                rows.append(r)
    diffs=[];drifts=[]; ratios=[]
    for k in targets:
        for block in range(blocks):
            rr=[x for x in rows if x['fixture_audit_only']==k and x['block']==block]
            vals={arm:[x['harness_wall_ns'] for x in rr if x['arm_audit']==arm] for arm in ('affine','projective')}
            if len(vals['affine'])!=2 or len(vals['projective'])!=2:raise AssertionError('unbalanced block')
            diffs.append(statistics.mean(vals['affine'])-statistics.mean(vals['projective']))
            ratios.append(statistics.mean(vals['affine'])/statistics.mean(vals['projective']))
            drifts.extend([abs(v[1]-v[0]) for v in vals.values()])
    median=lambda arm,name:statistics.median(x[name] for x in rows if x['arm_audit']==arm)
    result={'schema':'ct155-projective-source-audit/v1','standing':'[pcc:unverified]','scope':'CT152 E(F223^3) source; complete public-Q, not prime-field or Jacobian transfer',
            'prior_ct154_source_unchanged':True,'full_processes':len(rows),'independent_extra_cases':len(sample),'negative_controls':controls,
            'paired_blocks':len(diffs),'median_harness_wall_ns':{a:median(a,'harness_wall_ns') for a in ('affine','projective')},
            'median_solver_ns':{a:median(a,'solver_ns') for a in ('affine','projective')},
            'median_field_inv':{a:median(a,'field_inv') for a in ('affine','projective')},
            'median_field_mul':{a:median(a,'field_mul') for a in ('affine','projective')},
            'max_rss_kb':{a:max(x['peak_rss_kb'] for x in rows if x['arm_audit']==a) for a in ('affine','projective')},
            'paired_affine_minus_projective_median_wall_ns':statistics.median(diffs),
            'paired_affine_minus_projective_fixed_case_bootstrap95_ns':quantile_bootstrap(diffs),
            'paired_affine_over_projective_median_ratio':statistics.median(ratios),
            'aa_median_absolute_drift_ns':statistics.median(drifts),
            'source_sha256':{n:hashlib.sha256((Path(__file__).parent/n).read_bytes()).hexdigest() for n in ('ct153_original_cold_reference.cpp','ct154_public_point_reference.cpp','ct155_projective_bsgs.cpp','ct155_projective_audit.py')},
            'binary_sha256':{'baseline':hashlib.sha256(b.read_bytes()).hexdigest(),'candidate':hashlib.sha256(c.read_bytes()).hexdigest()},
            'host':platform.platform(),'compiler':'g++ -std=c++17 -O3 -Wall -Wextra -Werror',
            'limits':'non-isolated developer CPU; source-only; fixed-case CI not population; no signed PCC/actual Jacobian transfer/paid primitive prices'}
    result['rows_sha256']=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if args.output:args.output.write_text(json.dumps({'summary':result,'rows':rows},sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True,separators=(',',':')))
if __name__=='__main__':main()
