"""Independent checked-Sage replay of varied-target public search prefixes."""
import hashlib
import json
import math
from pathlib import Path
from sage.all import EllipticCurve, GF

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / 'xedni-coefficient-holdout-20261115'
HOLD = HERE.parent / 'xedni-nonisomorphic-holdout-20261115'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def add_cost(k):
    k = abs(k)
    return k.bit_length() + k.bit_count()

protocol = json.loads((HERE/'protocol.json').read_text())
result = json.loads((HERE/'result.json').read_text())
selection = json.loads((HOLD/'selection.json').read_text())['selected']
assert result['protocol_sha256'] == sha(HERE/'protocol.json')
assert result['source_sha256'] == sha(HERE/'run.py')
assert protocol['parent_family_protocol_sha256'] == sha(PARENT/'protocol.json')
assert protocol['parent_family_source_sha256'] == sha(PARENT/'run.py')
assert protocol['holdout_selection_sha256'] == sha(HOLD/'selection.json')
vectors = [(a,b) for a in range(1,4) for b in range(-3,4) if b and math.gcd(a,abs(b)) == 1]
assert [list(v) for v in vectors] == json.loads((PARENT/'protocol.json').read_text())['coefficient_family']
assert len(result['fields']) == len(selection) == 8
fields = []
for row, (p,q) in zip(result['fields'],selection):
    assert (p,q) == (row['field_prime'],row['subgroup_order'])
    label = f'xedni-target-diversity-v1|{p}|{q}'.encode()
    d = 1 + int(hashlib.sha256(label).hexdigest(),16) % (q-1)
    assert row['fixture_scalar'] == d
    E = EllipticCurve(GF(p),[-1,-2]); G = E(2,2); Q = d*G
    assert int(E.cardinality()) == q and int(G.order()) == q
    raw = HERE/row['prefix_path']
    assert sha(raw) == row['prefix_sha256']
    saved = [json.loads(line) for line in raw.read_text().splitlines()]
    assert len(saved) == row['prefix_rows'] == row['first_family']['query_index_one_based']
    assert all(item['t'] == [0,i] for i,item in enumerate(saved))
    tests = admitted = add_calls = 0
    first = None
    for index,item in enumerate(saved):
        t1,t2 = item['t']
        U,V = Q-t1*G,Q-t2*G
        if U.is_zero() or V.is_zero() or U == V:
            assert item['status'] == 'excluded' and item['tests'] == []
            continue
        admitted += 1
        expected = []
        for a,b in vectors:
            group_relation = (a*U+b*V).is_zero()
            algebra_relation = ((a+b)*d-a*t1-b*t2) % q == 0
            assert group_relation == algebra_relation
            tests += 1
            add_calls += add_cost(a)+add_cost(b)+1
            expected.append([a,b,int(group_relation)])
            if group_relation:
                assert (a+b) % q != 0
                recovered = ((a*t1+b*t2)*pow((a+b)%q,-1,q)) % q
                assert recovered*G == Q
                first = {'t':[t1,t2], 'vector':[a,b], 'query_index_one_based':index+1,
                         'vector_tests_to_hit':tests, 'group_add_calls_to_hit':add_calls+index,
                         'admitted_queries_to_hit':admitted, 'recovered_scalar':recovered}
                break
        assert item['tests'] == expected
        assert item['status'] == ('hit' if first else 'nonrelation')
        if first: break
    assert first == row['first_family']
    fields.append({'field_prime':p,'subgroup_order':q,'fixture_scalar':d,
                   'first_query':first['query_index_one_based'],
                   'vector_tests':tests,'group_add_calls':first['group_add_calls_to_hit']})
print(json.dumps({'schema':'xedni-target-diversity-audit-v1','status':'PASS','fields':fields},sort_keys=True,indent=2))
