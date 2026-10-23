"""Checked-Sage trace/conductor classification of external frozen walks."""
from hashlib import sha256
from pathlib import Path
import json

from sage.all import EllipticCurve_from_j, GF

P=Path(__file__).resolve().parent
SHA=lambda q:sha256(q.read_bytes()).hexdigest()

def main():
    protocol=json.loads((P/'external_protocol.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_EXTERNAL_SAGE_TRACE_CENSUS'
    assert protocol['script_sha256']==SHA(P/'external_run.py')
    assert protocol['runtime_sha256']==SHA(P/'sage_runtime.json')
    facts={};rows=[]
    for case in protocol['cases']:
        path=Path(case['path'])
        assert SHA(path)==case['sha256']
        p=case['p']
        if p not in facts:
            j=GF(p)(-121);curve=EllipticCurve_from_j(j)
            facts[p]={'j_mod_p':int(j),
                      'trace_abs':abs(int(curve.trace_of_frobenius())),
                      'endomorphism_conductor':int(curve.endomorphism_order().conductor())}
        record=facts[p]
        same=record['trace_abs']==case['u']
        compatible=same and case['f']%record['endomorphism_conductor']==0
        rows.append({**case,'regular_curve_trace_abs':record['trace_abs'],
                     'regular_curve_conductor':record['endomorphism_conductor'],
                     'same_isogeny_class':same,'conductor_compatible':compatible,
                     'eligible_point_missing':compatible and not case['regular_point_present'] and case['class_size']>0})
    result={'status':'EXACT_EXTERNAL_REGULAR_BRANCH_TRACE_CENSUS',
            'protocol_sha256':SHA(P/'external_protocol.json'),
            'script_sha256':SHA(P/'external_run.py'),
            'unique_primes':len(facts),'prime_facts':facts,'cases':rows,
            'eligible_missing_count':sum(r['eligible_point_missing'] for r in rows),
            'candidate_id':None,'timing_claim':None}
    (P/'external_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'cases':len(rows),'unique_primes':len(facts),
                      'eligible_missing':[r['path'] for r in rows if r['eligible_point_missing']]}))

if __name__=='__main__':main()
