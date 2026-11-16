"""Run frozen public vector family on deterministic, varied target scalars."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / 'xedni-coefficient-holdout-20261115'
HOLD = HERE.parent / 'xedni-nonisomorphic-holdout-20261115'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def scalar(p, q):
    label = f'xedni-target-diversity-v1|{p}|{q}'.encode()
    return 1 + int.from_bytes(hashlib.sha256(label).digest(), 'big') % (q - 1)

def load_group():
    spec = importlib.util.spec_from_file_location('xedni_frozen_group', PARENT / 'run.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    for key, path in (
        ('parent_family_protocol_sha256', PARENT / 'protocol.json'),
        ('parent_family_source_sha256', PARENT / 'run.py'),
        ('holdout_selection_sha256', HOLD / 'selection.json'),
    ):
        assert protocol[key] == sha(path), key
    vectors = [tuple(c) for c in json.loads((PARENT / 'protocol.json').read_text())['coefficient_family']]
    assert len(vectors) == 14
    group = load_group()
    fields = []
    for p, q in json.loads((HOLD / 'selection.json').read_text())['selected']:
        d = scalar(p, q)
        G = (2 % p, 2 % p)
        Q = group.mul(d, G, p)
        assert Q is not None
        minus_G = group.neg(G, p)
        group.ADD_COUNT = 0
        tests = admitted = 0
        rows = []
        hit = None
        U = Q
        for t1 in range(q):
            if hit: break
            V = Q
            for t2 in range(q):
                index = t1 * q + t2 + 1
                if U is None or V is None or U == V:
                    rows.append({'t': [t1,t2], 'status': 'excluded', 'tests': []})
                else:
                    admitted += 1
                    checks = []
                    for a,b in vectors:
                        relation = group.add(group.mul(a,U,p), group.mul(b,V,p), p) is None
                        tests += 1
                        checks.append([a,b,int(relation)])
                        if relation:
                            C = (a+b) % q
                            assert C != 0
                            recovered = ((a*t1+b*t2)*pow(C,-1,q)) % q
                            adds = group.ADD_COUNT
                            assert group.mul(recovered,G,p) == Q
                            hit = {'t':[t1,t2], 'vector':[a,b], 'query_index_one_based':index,
                                   'vector_tests_to_hit':tests, 'group_add_calls_to_hit':adds,
                                   'admitted_queries_to_hit':admitted, 'recovered_scalar':recovered}
                            break
                    rows.append({'t':[t1,t2], 'status':'hit' if hit else 'nonrelation', 'tests':checks})
                if hit: break
                V = group.add(V,minus_G,p)
            if not hit: U = group.add(U,minus_G,p)
        assert hit is not None and hit['recovered_scalar'] == d
        path = HERE / f'p{p}-prefix.jsonl'
        path.write_text(''.join(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n' for row in rows))
        fields.append({'field_prime':p, 'subgroup_order':q, 'fixture_scalar':d,
                       'first_family':hit, 'prefix_rows':len(rows),
                       'prefix_path':path.name, 'prefix_sha256':sha(path)})
    print(json.dumps({'schema':'xedni-target-diversity-result-v1','status':'PASS',
                      'protocol_sha256':sha(HERE/'protocol.json'),
                      'source_sha256':sha(Path(__file__)),
                      'parent_family_protocol_sha256':sha(PARENT/'protocol.json'),
                      'fields':fields},sort_keys=True,indent=2))

if __name__ == '__main__':
    main()
