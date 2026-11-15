#!/usr/bin/env python3
"""CT140 fail-closed independent toy ECDLP arithmetic + same-host cost audit.

Uses the separately authored CT136 Python curve arithmetic after byte guarding
its verifier; never imports or trusts C++ solver arithmetic or source timing
summaries. Diagnostic only, [pcc:unverified].
"""
import csv
import hashlib
import importlib.util
import json
import pathlib
import random
import statistics
import sys
import tempfile

BASE = pathlib.Path(__file__).resolve().parent
WIDTHS = (2,4,8,16)
SEEDS = (20261340,20261341,20261342,20261343)
COUNT = 32
SHA = 'ce3a9e5af959ad5ec3a81ce78151587a099fa8f86029bc7fa059bf9a384abc2f'
SRC = '20b0305d0b291602dd141a278c00459c47e78608f17e33bea6395a3106438921'
OLD_BASE = ('source_bsgs','source_neg_rho','target_glv_rho')

def need(value, reason):
    if not value: raise ValueError(reason)

def expected_order():
    return [(seed, WIDTHS[(j+i)%len(WIDTHS)])
            for j,seed in enumerate(SEEDS) for i in range(len(WIDTHS))]

def guarded_verifier():
    path=BASE/'ct136_verify.py'
    need(hashlib.sha256(path.read_bytes()).hexdigest()==SHA,'CT136 arithmetic auditor changed')
    spec=importlib.util.spec_from_file_location('ct136_verified_arithmetic',path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.preflight()
    return mod

def guarded_generated_sources():
    need(hashlib.sha256((BASE/'ct136_native.cpp').read_bytes()).hexdigest()==SRC,'CT136 source changed')
    from ct140_generate import generate
    for width in WIDTHS:
        path=BASE/'generated_ct140'/f'ct140_width{width}.cpp'
        need(path.read_text()==generate(width),'guarded generated source mismatch')
    return {str(w):hashlib.sha256((BASE/'generated_ct140'/f'ct140_width{w}.cpp').read_bytes()).hexdigest() for w in WIDTHS}

def normalize(raw,width,seed):
    need(width in WIDTHS and seed in SEEDS,'unknown panel')
    prefix=f'schema,ct140-width{width}-cold-v1\n'
    need(raw.startswith(prefix) and raw.count(prefix)==1,'schema/width')
    for p in ('source','target'):
        label=f'{p}_batch{width}_rho'
        need(raw.count(label)==2*COUNT+1, f'{p} batch label count')
    old=raw.replace(prefix,'schema,ct136-batched-cold-v1\n',1)
    return old.replace(f'source_batch{width}_rho','source_batch32_rho').replace(
        f'target_batch{width}_rho','target_batch32_rho')

def full_audit():
    verifier=guarded_verifier()
    source_hashes=guarded_generated_sources()
    seq=(BASE/'ct140_sequence.txt').read_text().splitlines()
    need(seq==[f'{seed}:{width}' for seed,width in expected_order()], 'missing/out-of-order processes')
    host=(BASE/'ct140_host.txt').read_bytes()
    need(b'g++' in host and b'Linux' in host,'missing compiler/host receipt')
    results=BASE/'ct140_results'
    names={f'width{w}-{seed}.csv' for w in WIDTHS for seed in SEEDS}
    need({x.name for x in results.glob('*.csv')}==names,'missing/extra CSV')
    data={};sha={};res={};targets={};all_sums={w:{} for w in WIDTHS};all_paired={}
    with tempfile.TemporaryDirectory(prefix='ct140-independent-') as folder:
        for seed,width in expected_order():
            stem=f'width{width}-{seed}';path=results/(stem+'.csv')
            raw=path.read_bytes();s=raw.decode('utf8')
            normalized=normalize(s,width,seed)
            dest=pathlib.Path(folder)/(stem+'.csv');dest.write_text(normalized)
            proof=verifier.audit(dest,seed,COUNT)
            rows=list(csv.reader(s.splitlines()))
            nameset={'source_bsgs','source_neg_rho','target_glv_rho',
                f'source_batch{width}_rho',f'target_batch{width}_rho'}
            need(set(proof['ns'])=={'source_bsgs','source_neg_rho','target_glv_rho','source_batch32_rho','target_batch32_rho'}, 'auditor arm set')
            label_map={'source_batch32_rho':f'source_batch{width}_rho',
                       'target_batch32_rho':f'target_batch{width}_rho'}
            mapped={label_map.get(arm,arm):n for arm,n in proof['ns'].items()}
            need(set(mapped)==nameset,'mapped arm set')
            for arm,n in mapped.items():
                all_sums[width][arm]=all_sums[width].get(arm,0)+n
            for ix in range(COUNT):
                segment=rows[3+ix*10:3+(ix+1)*10]
                ident=(segment[0][3],segment[0][5],segment[0][6])
                key=(seed,ix)
                if key in targets: need(targets[key]==ident, 'different public scalar/point across widths')
                else: targets[key]=ident
                by_arm={a:[] for a in nameset}
                for record in segment:
                    need(record[2] in by_arm,'wrong arm label')
                    by_arm[record[2]].append(int(record[7]))
                need(all(len(v)==2 for v in by_arm.values()),'two cold arm repeats')
                all_paired[(width,seed,ix)]={a:sum(v) for a,v in by_arm.items()}
            sha[stem]=hashlib.sha256(raw).hexdigest()
            timetext=(results/(stem+'.time')).read_text().strip()
            words={k:v for k,v in (s.split('=',1) for s in timetext.split())}
            need(set(words)=={'wall_seconds','maxrss_kb'},'time/RSS schema')
            wall=float(words['wall_seconds']);rss=int(words['maxrss_kb'])
            need(0<=wall<120 and 0<rss<2097152,'bounded host receipts')
            need((results/(stem+'.stderr')).is_file(),'stderr missing')
            res[stem]={'wall_seconds':wall,'maxrss_kb':rss}
    need(len(targets)==128,'distinct public targets count')
    need(len(set(targets.values()))==128,'duplicated public target')
    s=min((cost,width,arm) for width,block in all_sums.items() for arm,cost in block.items() if arm.startswith('source'))
    t=min((cost,width,arm) for width,block in all_sums.items() for arm,cost in block.items() if arm.startswith('target'))
    # Fixed whole-cohort arm, *never* per-target fastest (which would be an oracle).
    ids=list(targets)
    rng=random.Random(140);bootstrap=[]
    for _ in range(400):
        chosen=[ids[rng.randrange(len(ids))] for unused in ids]
        score_s=min(sum(all_paired[(w,*key)][arm] for key in chosen) for w,block in all_sums.items() for arm in block if arm.startswith('source'))
        score_t=min(sum(all_paired[(w,*key)][arm] for key in chosen) for w,block in all_sums.items() for arm in block if arm.startswith('target'))
        bootstrap.append(score_s/score_t)
    bootstrap.sort()
    def best(w,prefix): return min((v,a) for a,v in all_sums[w].items() if a.startswith(prefix))
    per_width={str(w):{'best_source':list(best(w,'source')),
                       'best_target':list(best(w,'target')),
                       'source_over_target':best(w,'source')[0]/best(w,'target')[0],
                       'headroom_ms_per_target':(best(w,'source')[0]-best(w,'target')[0])/128/1e6}
               for w in WIDTHS}
    # Fail-closed new independent dimensional check for inherited CT139 by_width typo.
    old=json.loads((BASE/'ct139-headroom.json').read_text())
    unit_fixes={}
    for caption,report in [('ct139_new',old['new']),('ct138_original',old['old'])]:
        for width,x in report['by_width'].items():
            correctly_scaled=(x['source_ns']-x['transferred_ns'])/128/1e6
            need(abs(x['extra_headroom_ms_per_target']-correctly_scaled*1e6)<1e-6,
                 'inherited per-width unit discrepancy changed (read-only original expected)')
            unit_fixes[f'{caption}_{width}']={
                'old_field_named_ms_contains_nanoseconds':x['extra_headroom_ms_per_target'],
                'corrected_extra_headroom_ms_per_target':correctly_scaled,
                'factor_of_units_error':1000000}
    need(abs(old['new']['transfer_extra_headroom_ms_per_target']-((old['new']['best_source'][0]-old['new']['best_transferred'][0])/128/1e6))<1e-12,
         'top-level CT139 ms field unexpectedly wrong')
    return {'schema':'ct140-low-lane-independent-audit/v1','standing':'[pcc:unverified]',
        'scope':'selected 31-bit CM-neighbor toy; NOT 695/701 original-prime full chain or strongest rho/IC',
        'widths':list(WIDTHS),'seeds':list(SEEDS),'public_targets':len(targets),
        'complete_scalar_recoveries':len(expected_order())*COUNT*10,
        'best_source_ns_width_arm':list(s),'best_target_ns_width_arm':list(t),
        'ratio_best_fixed_source_over_target':s[0]/t[0],
        'headroom_ms_per_target':(s[0]-t[0])/128/1e6,
        'paired_bootstrap_descriptive_95':[bootstrap[9],bootstrap[389]],
        'all_sums_ns':all_sums,'by_width':per_width,
        'ct139_inherited_unit_corrections':unit_fixes,'raw_sha256':sha,
        'source_hashes':source_hashes,'resources':res,
        'host_sha256':hashlib.sha256(host).hexdigest(),
        'caveat':'Unsigned producer host, no EKS, no original-prime runtime pricing, physical host independence unproven'}

def negatives():
    raw=(BASE/'ct140_results/width2-20261340.csv').read_text()
    problems={
        'wrong_schema':raw.replace('ct140-width2-cold-v1','ct140-width99-cold-v1',1),
        'wrong_target_label':raw.replace('target_batch2_rho','target_batch99_rho',1),
        'missing_arm': '\n'.join(raw.splitlines()[:-8])+'\n',
    }
    rejected=[]
    for name,value in problems.items():
        try:
            norm=normalize(value,2,20261340)
            with tempfile.TemporaryDirectory() as folder:
                f=pathlib.Path(folder)/'bad.csv';f.write_text(norm)
                guarded_verifier().audit(f,20261340,COUNT)
        except (ValueError,IndexError): rejected.append(name)
        else:raise ValueError('bad test passed: '+name)
    # A mislabeled raw ns value cannot satisfy the explicit ns->ms dimensional identity.
    test=1_192_640.125
    need(test/1e6==1.192640125 and test!=1.192640125,'dimensional control failed')
    rejected.append('nanoseconds_mislabeled_milliseconds')
    return rejected

if __name__=='__main__':
    try:
        rep=full_audit()
        rep['negative_controls_rejected']=negatives()
        output=BASE/'ct140_independent_audit.json'
        output.write_text(json.dumps(rep,sort_keys=True,indent=2)+'\n')
        print(json.dumps({'ratio':rep['ratio_best_fixed_source_over_target'],
            'best_source':rep['best_source_ns_width_arm'],
            'best_target':rep['best_target_ns_width_arm'],
            'ci':rep['paired_bootstrap_descriptive_95'],
            'headroom_ms_per_target':rep['headroom_ms_per_target'],
            'controls':rep['negative_controls_rejected']},sort_keys=True))
    except Exception as e:
        print('CT140 FAIL-CLOSED: '+str(e),file=sys.stderr)
        sys.exit(1)
