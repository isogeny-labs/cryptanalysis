"""Compare signed distinct-source coverage with the projected class sumset."""
import hashlib
import itertools
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
POST=json.loads((HERE/'post-run.json').read_text())


def pinned(name,key):
    raw=(HERE/name).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==POST[key]
    return json.loads(raw)


def main():
    logs=pinned('class-logs.json','class_logs_sha256')['q_logs']
    result=pinned('result.json','result_sha256')
    fixture=pinned('fixture.json','fixture_sha256')
    q=2531
    assert len(logs)==len(set(logs))==40 and all(logs)
    S=set(logs)
    assert all((-x)%q in S for x in S)
    signed={(a*logs[i]+b*logs[j])%q
            for i,j in itertools.combinations(range(40),2)
            for a,b in itertools.product((-1,1),repeat=2)}
    sumset={(logs[i]+logs[j])%q
            for i in range(40) for j in range(i,40)}
    assert signed==sumset and len(sumset)==result['index_distinct_points']==689
    target=fixture['scalar']
    assert target not in sumset and result['status']=='NO_RELATION'
    covered=sorted(sumset)
    output={'schema':'hecke-d79-p63317-sumset-audit-v1','status':'PASS','q':q,
            'class_log_count':40,'class_logs_distinct':True,'class_logs_nonzero':True,
            'negation_closed':True,'signed_pattern_count':3120,
            'unordered_sum_patterns':820,'distinct_covered_scalars':len(covered),
            'signed_equals_sumset':True,'target_scalar':target,
            'target_covered':False,'covered_scalars':covered,
            'coverage_sha256':hashlib.sha256(json.dumps(covered,separators=(',',':')).encode()).hexdigest()}
    (HERE/'sumset-audit.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS','signed_equals_sumset':True,
                      'covered':len(covered),'unordered_cap':820,'target_covered':False}))


if __name__=='__main__':
    main()
