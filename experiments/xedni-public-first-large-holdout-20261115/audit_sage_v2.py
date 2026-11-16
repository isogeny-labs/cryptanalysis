"""Independent scalar-equation and Sage point replay of every frozen query."""
import hashlib
import json
from pathlib import Path
from sage.all import EllipticCurve, GF, QQ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
COORD = ROOT / 'xedni-rank-one-coordinate-control-20261115/result.json'
FAMILY = ROOT / 'xedni-coefficient-optimization-20261115/family-selection.json'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def offsets(seed, p, q, i):
    out = []
    for axis in (0, 1):
        data = (str(seed) + ':' + str(p) + ':' + str(i) + ':' + str(axis)).encode()
        out.append(int(hashlib.sha256(data).hexdigest(), 16) % q)
    return out

def red(z, p):
    n, d = map(int, (z.numerator(), z.denominator()))
    assert d % p
    return n * pow(d, -1, p) % p

def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    result = json.loads((HERE / 'result.json').read_text())
    assert result['protocol_sha256'] == sha(HERE / 'protocol.json')
    assert result['source_sha256'] == sha(HERE / 'run_sage.py')
    assert result['sage_runtime_sha256'] == sha(HERE / 'sage-runtime-info.json')
    amendment = json.loads((HERE / 'audit-amendment.json').read_text())
    assert amendment['base_protocol_sha256'] == sha(HERE / 'protocol.json')
    assert amendment['original_audit_sha256'] == sha(HERE / 'audit_sage.py')
    assert amendment['failed_audit_stderr_sha256'] == sha(HERE / 'audit-v1.stderr')
    assert amendment['audit_v2_sha256'] == sha(Path(__file__))
    assert protocol['coordinate_control_sha256'] == sha(COORD)
    assert protocol['family_sha256'] == sha(FAMILY)
    vectors = [tuple(v) for v in json.loads(FAMILY.read_text())['selected']]
    coord = {r['field_prime']: r for r in json.loads(COORD.read_text())['rows']}
    audited = []
    for row in result['fields']:
        p, q = row['field_prime'], row['subgroup_order']
        assert p in protocol['field_panel'] and q == coord[p]['subgroup_order']
        E = EllipticCurve(GF(p), [0, 0, 0, -1, -2])
        G = coord[p]['subgroup_multiplier_m'] * E([2, 2])
        Q = protocol['target_scalar'] * G
        assert int(G.order()) == q and row['subgroup_multiplier'] == coord[p]['subgroup_multiplier_m']
        raw = HERE / row['events_path']
        assert sha(raw) == row['events_sha256']
        saved = [json.loads(line) for line in raw.read_text().splitlines()]
        cursor = filtered = admitted = tests = 0
        first = None
        for i in range(protocol['queries_per_field']):
            t1, t2 = offsets(protocol['schedule_seed'], p, q, i)
            U, V = Q - t1 * G, Q - t2 * G
            if t1 == t2 or t1 == protocol['target_scalar'] or t2 == protocol['target_scalar']:
                filtered += 1
                continue
            assert U != V and not U.is_zero() and not V.is_zero()
            admitted += 1
            for a, b in vectors:
                tests += 1
                hit = ((a+b)*protocol['target_scalar'] - a*t1 - b*t2) % q == 0
                assert hit == bool((a*U + b*V).is_zero())
                if not hit:
                    continue
                first = first or i+1
                assert cursor < len(saved)
                e = saved[cursor]; cursor += 1
                assert e['status'] == 'verified' and e['query_index_one_based'] == i+1
                assert e['t'] == [t1,t2] and e['vector'] == [a,b]
                T = pow(b % q,-1,q) * U
                assert e['inverse_b'] == pow(b % q,-1,q)
                assert b*T == U and (-a)*T == V
                x0,y0 = (int(T[0]) % p, int(T[1]) % p)
                x = x0 if x0 <= p//2 else x0-p
                y = y0 if y0 <= p//2 else y0-p
                assert e['lift_T'] == [x,y]
                B = y*y-x*x*x+x
                assert e['curve_B'] == B and (B+2)%p == 0
                C = EllipticCurve(QQ,[0,0,0,-1,B]); P = C([x,y])
                A,D = b*P,(-a)*P
                assert C.discriminant()!=0 and (a*A+b*D).is_zero()
                assert E([red(A[0],p),red(A[1],p)]) == U
                assert E([red(D[0],p),red(D[1],p)]) == V
                point_text=[str(A[0]),str(A[1]),str(D[0]),str(D[1])]
                digest=hashlib.sha256(json.dumps(point_text,separators=(',',':')).encode()).hexdigest()
                assert e['rational_points_sha256']==digest
                w=((a*t1+b*t2)*pow((a+b)%q,-1,q))%q
                assert e['recovered_scalar']==w and w*G==Q
        counts=row['counts']
        assert counts['queries']==protocol['queries_per_field']
        assert counts.get('filtered_queries', 0)==filtered
        assert counts['admitted_queries']==admitted
        assert counts['public_vector_tests']==tests==13*admitted
        assert counts['public_hits']==counts['verified']==cursor==len(saved)
        assert counts.get('failed',0)==0 and row['first_hit_query']==first
        audited.append({'field_prime':p,'subgroup_order':q,'queries':protocol['queries_per_field'],
                        'public_vector_tests':tests,'verified':cursor,'first_hit_query':first})
    assert len(audited)==len(protocol['field_panel'])==8
    print(json.dumps({'schema':'xedni-public-first-large-holdout-audit-v2',
                      'status':'PASS','protocol_sha256':sha(HERE/'protocol.json'),
                      'source_sha256':sha(Path(__file__)),
                      'sage_runtime_sha256':sha(HERE/'sage-runtime-info.json'),
                      'fields':audited},sort_keys=True,indent=2))

if __name__=='__main__':
    main()
