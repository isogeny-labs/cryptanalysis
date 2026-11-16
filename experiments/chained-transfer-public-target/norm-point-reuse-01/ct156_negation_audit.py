#!/usr/bin/env python3
"""Independent public-Q signed-BSGS finite-field verifier and balanced local diagnostic.

No original 695/701 Jacobian chain; source-only non-isolated evidence. [pcc:unverified]
"""
import argparse,hashlib,json,random,statistics,subprocess,time,platform
from pathlib import Path
import ct153_reference_audit as ref

def invoke(binary,Q,arm):
    coords=[str(v) for f in Q for v in f]
    t=time.perf_counter_ns()
    proc=subprocess.run([str(binary),*coords],capture_output=True,text=True,timeout=30)
    wall=time.perf_counter_ns()-t
    if proc.returncode or not proc.stdout:
        raise AssertionError(f'{arm} failed on {Q}: {proc.returncode} {proc.stderr}')
    rec=json.loads(proc.stdout)
    if rec['source_public']!=[list(f) for f in Q] or ref.scalar(ref.G,rec['recovered'])!=Q or not 0<rec['recovered']<ref.ELL:
        raise AssertionError(f'{arm} wrong public-point DLP')
    if rec['standing']!='pcc:unverified' or rec['solver_ns']>rec['process_ns'] or rec['process_ns']<=0:
        raise AssertionError('malformed receipt/monotonic clock')
    for k in ('field_mul','field_inv','point_add','point_double','steps','table_entries','peak_rss_kb'):
        if not isinstance(rec[k],int) or rec[k]<0:raise AssertionError(f'bad counter: {k}')
    rec['harness_wall_ns']=wall
    rec['arm_audit']=arm
    return rec

def rejection(binary,coords):
    p=subprocess.run([str(binary),*coords],capture_output=True,text=True,timeout=10)
    if p.returncode!=2 or not p.stderr.startswith('ct156 REJECTED:') or p.stdout:
        raise AssertionError(f'failed rejection: {coords!r}')

def negative_controls(binary):
    Q=ref.scalar(ref.G,17);c=[str(v) for f in Q for v in f]
    bad=c.copy();bad[3]=str((int(bad[3])+1)%223)
    # Use an independently generated off-subgroup rational source point.
    nonsubgroup=None
    for a in range(200):
        x=(a%223,a//223,0)
        xx=ref.field_mul(x,x)
        rhs=ref.field_add(ref.field_add(ref.field_mul(xx,x),ref.field_mul(ref.A2,xx)),ref.field_add(ref.field_mul(ref.A4,x),ref.A6))
        y=ref.field_pow(rhs,(223**3+1)//4)
        Qx=(x,y)
        if ref.on(Qx) and ref.scalar(Qx,ref.ELL) is not None:
            nonsubgroup=[str(v) for f in Qx for v in f];break
    if not nonsubgroup:raise AssertionError('failed to generate outside-subgroup point')
    controls=[c[:-1],['223',*c[1:]],['-1',*c[1:]],['abc',*c[1:]],['+1',*c[1:]],bad,nonsubgroup,['000223',*c[1:]]]
    for x in controls:rejection(binary,x)
    return len(controls)

def bootstrap(differences,seed=156,n=4000):
    r=random.Random(seed)
    dist=sorted(statistics.median(r.choice(differences) for _ in differences) for _ in range(n))
    return [dist[99],dist[3899]]

def check_mutations():
    # Independent pure arithmetic coverage proof: every scalar k can be expressed
    # as 2mi + j (signed j) in the tested giant range, not just sample successes.
    n=ref.ELL;m=1
    while 2*m*m<n:m+=1
    bound=(n+m)//(2*m)+1
    for k in range(n):
        i=(k+m)//(2*m);j=k-2*m*i
        if not (0<=i<=bound and -m<=j<=m):raise AssertionError('range coverage false')
    return {'m':m,'giant_bound':bound,'all_exponents_covered':n}

def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path);p.add_argument('--quick',action='store_true');a=p.parse_args()
    b=a.baseline.resolve();c=a.candidate.resolve();s=json.loads(subprocess.check_output([str(c),'--self-test'],text=True,timeout=30))
    assert s['result']=='pass' and s['public_dlps']==16
    ctl=negative_controls(c)
    coverage=check_mutations()
    rnd=random.Random(15601)
    fixed=[1,2,3,5,13,64,255,1177,1178,1179,2355,2356,2357,ref.ELL-1,ref.ELL-2,ref.ELL-3]
    sample=fixed+rnd.sample(range(1,ref.ELL),64 if a.quick else 256)
    for k in sample:
        Q=ref.scalar(ref.G,k)
        if invoke(c,Q,'signed')['recovered']!=k:raise AssertionError('independent sample mismatch')
    targets=ref.SCALARS[:2] if a.quick else ref.SCALARS
    blocks=1 if a.quick else 4
    rows=[]
    for ix,k in enumerate(targets):
        Q=ref.scalar(ref.G,k)
        for block in range(blocks):
            order=['baseline','candidate','candidate','baseline'] if block%2==0 else ['candidate','baseline','baseline','candidate']
            for pos,arm in enumerate(order):
                rec=invoke(b if arm=='baseline' else c,Q,arm)
                if rec['recovered']!=k:raise AssertionError('public-target known answer differs')
                rec.update({'fixture_audit_only':k,'target_index':ix,'block':block,'position':pos})
                rows.append(rec)
    paired=[];ratio=[];drift=[]
    for k in targets:
        for block in range(blocks):
            sub=[z for z in rows if z['fixture_audit_only']==k and z['block']==block]
            groups={arm:[z['harness_wall_ns'] for z in sub if z['arm_audit']==arm] for arm in ('baseline','candidate')}
            if any(len(z)!=2 for z in groups.values()):raise AssertionError('unbalanced block')
            avg={key:statistics.mean(z) for key,z in groups.items()}
            paired.append(avg['baseline']-avg['candidate']);ratio.append(avg['baseline']/avg['candidate'])
            drift.extend(abs(z[0]-z[1]) for z in groups.values())
    median=lambda arm,k:statistics.median(z[k] for z in rows if z['arm_audit']==arm)
    keys=['harness_wall_ns','solver_ns','field_inv','field_mul','steps','table_entries']
    names=['baseline','candidate']
    summary={'schema':'ct156-q223-signed-x-audit/v1','standing':'[pcc:unverified]',
      'scope':'original q223 E(F223^3) complete source public-Q; not Jacobian or prime field',
      'full_processes':len(rows),'paired_blocks':len(paired),'independent_extra_cases':len(sample),
      'negative_controls':ctl,'coverage':coverage,
      'medians':{key:{arm:median(arm,key) for arm in names} for key in keys},
      'max_rss_kb':{arm:max(z['peak_rss_kb'] for z in rows if z['arm_audit']==arm) for arm in names},
      'paired_baseline_minus_candidate_median_wall_ns':statistics.median(paired),
      'paired_fixed_fixture_bootstrap95_ns':bootstrap(paired),
      'paired_baseline_over_candidate_median_ratio':statistics.median(ratio),
      'aa_median_absolute_drift_ns':statistics.median(drift),
      'binary_sha256':{arm:hashlib.sha256((b if arm=='baseline' else c).read_bytes()).hexdigest() for arm in names},
      'source_sha256':{f:hashlib.sha256((Path(__file__).parent/f).read_bytes()).hexdigest() for f in ['ct153_original_cold_reference.cpp','ct155_projective_bsgs.cpp','ct156_negation_bsgs.cpp','ct156_negation_audit.py']},
      'compiler':'g++ -std=c++17 -O3 -Wall -Wextra -Werror','host':platform.platform(),
      'limits':'unisolated developer CPU; fixed-case bootstrap only; no signed PCC, full transfer or admitted native pricing'}
    summary['rows_sha256']=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if a.output:a.output.write_text(json.dumps({'summary':summary,'rows':rows},indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,sort_keys=True))
if __name__=='__main__':main()
