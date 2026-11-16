"""Frozen greedy vector selection using calibration subgroup orders only."""
import hashlib
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent/'xedni-coefficient-holdout-20261115'
COVER=HERE.parent/'xedni-finite-family-coverage-20261115'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def coverage(a,b,q):
    return {(b*t*pow((a+b)%q,-1,q))%q for t in range(1,35)}

def main():
    protocol=json.loads((HERE/'protocol.json').read_text())
    for key,path in (
        ('parent_family_protocol_sha256',PARENT/'protocol.json'),
        ('parent_coverage_protocol_sha256',COVER/'protocol.json'),
        ('parent_coverage_result_sha256',COVER/'result.json'),
    ):assert protocol[key]==sha(path)
    qs=protocol['calibration_orders'];assert qs==[751,883,983,1103]
    candidates=sorted((a,b) for a in range(1,7) for b in range(-6,7)
                      if b and a+b and math.gcd(a,abs(b))==1)
    covered={q:set() for q in qs};chosen=[];rounds=[]
    for _ in range(13):
        ranked=[]
        for a,b in candidates:
            if (a,b) in chosen:continue
            new=sum(len(coverage(a,b,q)-covered[q]) for q in qs)
            ranked.append((-new,a,b))
        loss,a,b=min(ranked)
        chosen.append((a,b))
        for q in qs:covered[q]|=coverage(a,b,q)
        rounds.append({'vector':[a,b],'new_coverage':-loss,
                       'cumulative_by_order':{str(q):len(covered[q]) for q in qs}})
    old=json.loads((PARENT/'protocol.json').read_text())['coefficient_family']
    baseline=[x for x in old if sum(x)!=0]
    assert len(baseline)==len(chosen)==13
    print(json.dumps({'schema':'xedni-coefficient-optimization-family-v1','status':'PASS',
                      'protocol_sha256':sha(HERE/'protocol.json'),
                      'source_sha256':sha(Path(__file__)),
                      'candidate_count':len(candidates),'calibration_orders':qs,
                      'baseline':baseline,'selected':[list(x) for x in chosen],
                      'rounds':rounds},sort_keys=True,indent=2))

if __name__=='__main__':main()
