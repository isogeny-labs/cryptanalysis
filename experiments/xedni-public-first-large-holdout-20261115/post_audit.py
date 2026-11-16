"""Check full census against the pinned Lean line and disjointness lemmas."""
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
    result=json.loads((HERE/'post-result.json').read_text())
    parent=json.loads((HERE/'result.json').read_text())
    assert result['post_protocol_sha256']==sha(HERE/'post-protocol.json')
    assert result['source_sha256']==sha(HERE/'post.py')
    assert protocol['audit_sha256']==sha(Path(__file__))
    assert protocol['lean_source_sha256']==sha(LEAN)
    vectors=[tuple(v) for v in json.loads(FAMILY.read_text())['selected']]
    assert len(vectors)==result['vector_count']==13
    dets=[a*d-b*c for (a,b),(c,d) in itertools.combinations(vectors,2)]
    assert len(dets)==result['pairwise_determinants']==78
    assert max(map(abs,dets))==result['max_abs_determinant']==60
    assert all(d!=0 for d in dets)
    assert len(parent['fields'])==len(result['rows'])==8
    for old,row in zip(parent['fields'],result['rows'],strict=True):
        p,q=old['field_prime'],old['subgroup_order']
        assert (p,q)==(row['field_prime'],row['subgroup_order'])
        assert all(a%q and b%q and (a+b)%q for a,b in vectors)
        assert all(d%q for d in dets)
        # admissible_hit_count gives q-1 events per vector;
        # distinct_directions_force_zero excludes an overlap on admitted pairs.
        assert row['full_admissible_pairs']==(q-1)*(q-2)
        assert row['predicted_events']==row['full_relation_events']==row['full_hit_pairs']==13*(q-1)
        assert row['overlap_pairs']==0
        assert row['sample_admitted_queries']==old['counts']['admitted_queries']
        assert row['sample_hit_events']==old['counts']['public_hits']
        expected=Fraction(old['counts']['admitted_queries']*13,q-2)
        assert row['uniform_reference_expected_sample_events']=={
            'numerator':expected.numerator,'denominator':expected.denominator}
    print(json.dumps({'schema':'xedni-public-first-large-holdout-post-audit-v1',
                      'status':'PASS','fields':8,
                      'full_admissible_pairs':sum(x['full_admissible_pairs'] for x in result['rows']),
                      'full_relation_events':sum(x['full_relation_events'] for x in result['rows']),
                      'sample_hit_events':sum(x['sample_hit_events'] for x in result['rows'])},sort_keys=True))

if __name__=='__main__':main()
