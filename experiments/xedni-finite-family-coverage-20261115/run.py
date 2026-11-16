"""Exact finite-family coverage by inverting the frozen relation equation."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = HERE.parent/'xedni-coefficient-holdout-20261115'
HOLD = HERE.parent/'xedni-nonisomorphic-holdout-20261115'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    protocol = json.loads((HERE/'protocol.json').read_text())
    for key,path in (
        ('family_protocol_sha256',FAMILY/'protocol.json'),
        ('family_source_sha256',FAMILY/'run.py'),
        ('field_selection_sha256',HOLD/'selection.json'),
    ):
        assert protocol[key] == sha(path), key
    vectors = [tuple(x) for x in json.loads((FAMILY/'protocol.json').read_text())['coefficient_family']]
    assert len(vectors) == 14
    rows = []
    for p,q in json.loads((HOLD/'selection.json').read_text())['selected']:
        usable = [(j,a,b) for j,(a,b) in enumerate(vectors) if (a+b)%q != 0]
        assert len(usable) == 13
        first = {}
        for t in range(1,q):
            for j,a,b in usable:
                d = (b*t*pow((a+b)%q,-1,q))%q
                assert d != 0 and d != t
                if d not in first:
                    first[d] = {'scalar':d,'first_query':t+1,'offset':t,
                                'vector_index':j,'vector':[a,b]}
        assert len(first) == q-1
        path = HERE/f'p{p}-first.jsonl'
        path.write_text(''.join(json.dumps(first[d],sort_keys=True,separators=(',',':'))+'\n' for d in range(1,q)))
        counts = []
        for L in protocol['query_caps']:
            covered = sum(x['first_query'] <= L for x in first.values())
            counts.append({'query_cap':L,'covered_nonzero_targets':covered,
                           'total_nonzero_targets':q-1,
                           'union_bound':min(q-1,len(usable)*(L-1))})
        rows.append({'field_prime':p,'subgroup_order':q,
                     'effective_vectors':len(usable),'first_path':path.name,
                     'first_sha256':sha(path),'caps':counts,
                     'full_row_covered':len(first)})
    print(json.dumps({'schema':'xedni-finite-family-coverage-result-v1','status':'PASS',
                      'protocol_sha256':sha(HERE/'protocol.json'),
                      'source_sha256':sha(Path(__file__)),
                      'fields':rows},sort_keys=True,indent=2))

if __name__ == '__main__':
    main()
