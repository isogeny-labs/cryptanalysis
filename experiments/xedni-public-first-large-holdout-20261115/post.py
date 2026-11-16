"""Exhaustive finite-field census for the frozen larger-order relation family."""
import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
FAMILY=ROOT/'xedni-coefficient-optimization-20261115/family-selection.json'
LEAN=ROOT/'xedni-coefficient-family-control-20261115/formal/CoefficientFamily.lean'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    protocol=json.loads((HERE/'post-protocol.json').read_text())
    parent=json.loads((HERE/'result.json').read_text())
    assert protocol['parent_result_sha256']==sha(HERE/'result.json')
    assert protocol['family_sha256']==sha(FAMILY)
    assert protocol['lean_source_sha256']==sha(LEAN)
    assert protocol['producer_sha256']==sha(Path(__file__))
    vectors=[tuple(v) for v in json.loads(FAMILY.read_text())['selected']]
    dets=[a*d-b*c for (a,b),(c,d) in itertools.combinations(vectors,2)]
    rows=[]
    for row in parent['fields']:
        p,q=row['field_prime'],row['subgroup_order']
        w=protocol['target_scalar']
        assert all(a%q and b%q and (a+b)%q for a,b in vectors)
        assert all(d%q for d in dets)
        queries=hits=overlaps=0
        for t1 in range(q):
            if t1==w:continue
            for t2 in range(q):
                if t2==w or t2==t1:continue
                queries+=1
                n=sum((a*(w-t1)+b*(w-t2))%q==0 for a,b in vectors)
                hits+=n
                overlaps+=n>1
        expected=Fraction(row['counts']['admitted_queries']*len(vectors),q-2)
        rows.append({'field_prime':p,'subgroup_order':q,
                     'full_admissible_pairs':queries,'full_relation_events':hits,
                     'full_hit_pairs':hits-overlaps,'overlap_pairs':overlaps,
                     'predicted_events':len(vectors)*(q-1),
                     'sample_admitted_queries':row['counts']['admitted_queries'],
                     'sample_hit_events':row['counts']['public_hits'],
                     'uniform_reference_expected_sample_events':
                         {'numerator':expected.numerator,'denominator':expected.denominator}})
    print(json.dumps({'schema':'xedni-public-first-large-holdout-post-v1',
                      'status':'PASS','post_protocol_sha256':sha(HERE/'post-protocol.json'),
                      'source_sha256':sha(Path(__file__)),
                      'vector_count':len(vectors),'pairwise_determinants':len(dets),
                      'max_abs_determinant':max(map(abs,dets)),
                      'rows':rows},sort_keys=True,indent=2))

if __name__=='__main__':main()
