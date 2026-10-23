"""Audit archived Hecke walks for the regular X0(11) point (16,60)."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve_from_j, GF

ROOT=Path('/Volumes/SSD990/cryptanalysis')
P=Path(__file__).resolve().parent
SHA=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
REGULAR='(16 : 60 : 1)'

def main():
    protocol=json.loads((P/'protocol.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_SAGE_TRACE_CENSUS'
    assert protocol['script_sha256']==SHA(P/'run.py')
    assert protocol['runtime_sha256']==SHA(P/'sage_runtime.json')
    for case in protocol['cases']:
        assert SHA(ROOT/case['path'])==case['sha256'],case['path']
        if case['source_path'] is not None:
            assert SHA(ROOT/case['source_path'])==case['source_sha256']
    primes={};cases=[]
    for case in protocol['cases']:
        p=case['p']
        if p not in primes:
            j=GF(p)(-121)
            curve=EllipticCurve_from_j(j)
            primes[p]={'j_mod_p':int(j),
                       'trace_abs':abs(int(curve.trace_of_frobenius())),
                       'endomorphism_conductor':int(curve.endomorphism_order().conductor())}
        value=primes[p]
        d=json.loads((ROOT/case['path']).read_text())
        present=REGULAR in d.get('column_points',[])
        same_trace=value['trace_abs']==case['u']
        c=value['endomorphism_conductor']
        conductor_compatible=same_trace and case['f']%c==0
        cases.append({'path':case['path'],'p':p,'u':case['u'],'dk':case['dk'],'f':case['f'],
                      'class_size':case['class_size'],'regular_point_present':present,
                      'regular_j_mod_p':value['j_mod_p'],
                      'regular_curve_trace_abs':value['trace_abs'],
                      'regular_curve_conductor':c,
                      'same_isogeny_class':same_trace,
                      'conductor_compatible':conductor_compatible,
                      'eligible_point_missing':conductor_compatible and not present and case['class_size']>0,
                      'source_has_broad_x16_guard':case['source_has_broad_x16_guard'],
                      'source_sha256':case['source_sha256'],'data_sha256':case['sha256']})
    result={'status':'EXACT_REGULAR_BRANCH_ARCHIVE_TRACE_CENSUS',
            'protocol_sha256':SHA(P/'protocol.json'),'script_sha256':SHA(P/'run.py'),
            'runtime_sha256':SHA(P/'sage_runtime.json'),
            'unique_primes':len(primes),'prime_facts':primes,'cases':cases,
            'eligible_missing_count':sum(x['eligible_point_missing'] for x in cases),
            'candidate_id':None,'timing_claim':None}
    (P/'RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'cases':len(cases),
                      'unique_primes':len(primes),
                      'eligible_missing':[x['path'] for x in cases if x['eligible_point_missing']]}))

if __name__=='__main__':main()
