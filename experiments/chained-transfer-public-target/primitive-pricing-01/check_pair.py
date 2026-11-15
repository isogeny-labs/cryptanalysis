#!/usr/bin/env python3
"""Fail-closed CT126 ABBA microbenchmark auditor; NOT an ECDLP speedup validator."""
import argparse, copy, json, random, statistics as st
from pathlib import Path
ARMS=('original-1','reuse-1','reuse-2','original-2')
LABELS=('C169','C13_first','C13_second','D','direct_warm','retained_warm')
SCALARS=(1,2,17,12345,2771710)
def validate(x):
    assert x['schema']=='ct126-primitive-price/v1' and x['standing']=='[pcc:unverified]'
    assert (x['source_prime'],x['subgroup_prime'],x['complete_group_order'])==(223,2771711,11086844)
    assert x['scalar_fixture_count']==5 and x['rounds_recorded']==12 and x['warmup_rounds']==4
    assert type(x['setup_construct_ns']) is int and x['setup_construct_ns']>0
    ids=x['identity_checks']
    assert len(ids)==5 and tuple(v['scalar_fixture_only'] for v in ids)==SCALARS
    assert all(v['direct_equals_retained'] is True for v in ids)
    assert set(x['timed'])==set(LABELS)
    for k in LABELS:
        z=x['timed'][k]; assert set(z)=={'repetitions_per_block','raw_block_ns'}
        assert z['repetitions_per_block']==(64 if k in LABELS[:4] else 5)
        assert len(z['raw_block_ns'])==12
        assert all(type(v) is int and v>0 for v in z['raw_block_ns'])
def audit(runs):
    assert set(runs)==set(ARMS)
    for v in runs.values(): validate(v)
    same=runs['original-1']['identity_checks']
    assert all(r['identity_checks']==same for r in runs.values()), 'public output mismatch'
    def samples(arm,k):
        r=runs[arm]['timed'][k]
        return [v/r['repetitions_per_block'] for v in r['raw_block_ns']]
    result={}
    for k in LABELS:
        a=samples('original-1',k)+samples('original-2',k)
        b=samples('reuse-1',k)+samples('reuse-2',k)
        ma,mb=st.median(a),st.median(b)
        rng=random.Random(126+len(k)); boots=[]
        for _ in range(500):
            boots.append(st.median(rng.choices(a,k=len(a)))/st.median(rng.choices(b,k=len(b))))
        boots.sort()
        result[k]={'original_median_ns_per_call':ma,'reuse_median_ns_per_call':mb,
                   'original_over_reuse':ma/mb,'diagnostic_bootstrap_95_pct':[boots[12],boots[487]],
                   'original_AA':st.median(samples('original-1',k))/st.median(samples('original-2',k)),
                   'reuse_AA':st.median(samples('reuse-1',k))/st.median(samples('reuse-2',k))}
    for arm in ('original','reuse'):
        result['crossover_ns_'+arm]=(result['C169'][arm+'_median_ns_per_call']
            -result['C13_first'][arm+'_median_ns_per_call']-result['C13_second'][arm+'_median_ns_per_call'])
    return {'schema':'ct126-paired-diagnostic/v1','public_fixture_count':5,'prices':result,
        'status':'[pcc:unverified]; microtiming and warm transfers only; NO cold ECDLP cost advantage'}
def selftest():
    rec={'schema':'ct126-primitive-price/v1','standing':'[pcc:unverified]',
         'source_prime':223,'subgroup_prime':2771711,'complete_group_order':11086844,
         'scalar_fixture_count':5,'rounds_recorded':12,'warmup_rounds':4,'setup_construct_ns':10,
         'identity_checks':[{'scalar_fixture_only':k,'source_public':[1],
         'output_public':[5],'direct_equals_retained':True} for k in SCALARS],
         'timed':{k:{'repetitions_per_block':64 if k in LABELS[:4] else 5,
                 'raw_block_ns':[1000+i for i in range(12)]} for k in LABELS}}
    runs={k:copy.deepcopy(rec) for k in ARMS}
    assert audit(runs)['public_fixture_count']==5
    bad=copy.deepcopy(runs);bad['reuse-1']['identity_checks'][0]['output_public']=[6]
    try:audit(bad)
    except AssertionError:pass
    else:raise AssertionError('mutated output accepted')
    bad=copy.deepcopy(runs);bad['original-2']['timed']['D']['raw_block_ns'].pop()
    try:audit(bad)
    except AssertionError:pass
    else:raise AssertionError('missing sample accepted')
    return {'positive':'pass','mutated_output':'rejected','missing_sample':'rejected'}
def main():
    p=argparse.ArgumentParser();p.add_argument('directory',nargs='?',type=Path)
    p.add_argument('--self-test',action='store_true');args=p.parse_args()
    if args.self_test:print(json.dumps(selftest(),sort_keys=True));return
    if args.directory is None:p.error('directory required')
    d=args.directory
    assert (d/'sequence.txt').read_text().splitlines()==[
        'original:original-1','reuse:reuse-1','reuse:reuse-2','original:original-2']
    assert (d/'host.txt').is_file()
    runs={k:json.loads((d/(k+'.json')).read_text()) for k in ARMS}
    report=audit(runs)
    (d/'diagnostic.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps(report,sort_keys=True))
if __name__=='__main__':main()
