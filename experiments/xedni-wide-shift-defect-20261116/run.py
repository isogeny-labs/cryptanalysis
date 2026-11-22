"""Enumerate a frozen wider shift grid on fresh public relation hits."""
from sage.all import EllipticCurve, GF, QQ
from fractions import Fraction
from pathlib import Path
import gzip
import hashlib
import itertools
import json
import time

H = Path(__file__).resolve().parent
P = json.loads((H / 'protocol.json').read_text())
SOURCE = H.parent / 'xedni-height-selected-two-image-20261116'
for name, digest in P['parent_sha256'].items():
    assert hashlib.sha256((SOURCE / name).read_bytes()).hexdigest() == digest
assert json.loads((SOURCE / 'audit.json').read_text())['status'] == 'PASS'
START = time.monotonic()

def read_gz(name):
    return [json.loads(line) for line in gzip.open(SOURCE / name, 'rt')]

queries = {row['event_index']: row for row in read_gz('queries.jsonl.gz')}
hits = [row for row in read_gz('vectors.jsonl.gz') if row['public_relation']]
assert len(hits) == P['expected_admitted_hits']
assert all(queries[row['event_index']]['branch'] == 'distinct_x' for row in hits)

def center(z, p):
    return z - p if z > p // 2 else z

def parts(z):
    num, den = z.numerator, z.denominator
    return int(num() if callable(num) else num), int(den() if callable(den) else den)

def mod(z, p):
    n, d = parts(z)
    if d % p == 0:
        raise ValueError('nonintegral_reduction')
    return n * pow(d, -1, p) % p

def bits(z):
    n, d = parts(z)
    return max(abs(n).bit_length(), d.bit_length())

def candidate(p, U, V, shift):
    x1, y1 = [center(z, p) for z in U]
    x2, y2 = [center(z, p) for z in V]
    x1 += shift[0] * p
    y1 += shift[1] * p
    x2 += shift[2] * p
    y2 += shift[3] * p
    f1, f2 = y1*y1-x1*x1*x1, y2*y2-x2*x2*x2
    A = Fraction(f1-f2, x1-x2)
    B = Fraction(f1)-A*x1
    if 4*A**3+27*B**2 == 0:
        raise ValueError('singular_curve')
    if (mod(A,p),mod(B,p)) != (p-1,p-2):
        raise ValueError('wrong_coefficient_reduction')
    if (x1%p,y1%p) != tuple(U) or (x2%p,y2%p) != tuple(V):
        raise ValueError('wrong_point_reduction')
    return A,B,x1,y1,x2,y2,max(bits(z) for z in (A,B,x1,y1,x2,y2))

def packed(path, rows):
    raw = ''.join(json.dumps(r, sort_keys=True, separators=(',', ':'))+'\n' for r in rows).encode()
    blob = gzip.compress(raw, compresslevel=9, mtime=0)
    (H / path).write_bytes(blob)
    return {'path': path, 'rows': len(rows), 'raw_sha256': hashlib.sha256(raw).hexdigest(),
            'gzip_sha256': hashlib.sha256(blob).hexdigest(), 'gzip_bytes': len(blob)}

parts_meta = []
summaries = []
counts = {'admitted_hits': 0, 'candidate_attempts': 0, 'candidate_pass': 0,
          'candidate_failure': 0, 'rational_relation_hits': 0, 'rational_controls': 0}
for hit in hits:
    event, vi, a, b = (hit[k] for k in ('event_index','vector_index','a','b'))
    query = queries[event]
    p, U, V = query['p'], query['U'], query['V']
    E = EllipticCurve(GF(p), [-1,-2])
    assert (a*E(U)+b*E(V)).is_zero()
    rows = []
    for shift in itertools.product(P['shift_values'], repeat=4):
        rec = {'event_index': event, 'vector_index': vi, 'shift': list(shift)}
        counts['candidate_attempts'] += 1
        try:
            A,B,x1,y1,x2,y2,score = candidate(p,U,V,shift)
            C = EllipticCurve(QQ,[QQ(A.numerator)/QQ(A.denominator),
                                  QQ(B.numerator)/QQ(B.denominator)])
            P1, P2 = C(QQ(x1),QQ(y1)), C(QQ(x2),QQ(y2))
            assert [mod(P1[0],p),mod(P1[1],p)] == U
            assert [mod(P2[0],p),mod(P2[1],p)] == V
            assert (P1+(-P1)).is_zero()
            counts['rational_controls'] += 1
            R = a*P1+b*P2
            residual = None if R.is_zero() else [str(R[0]),str(R[1])]
            residual_bits = 0 if residual is None else max(bits(R[0]),bits(R[1]))
            residual_digest = hashlib.sha256(json.dumps(residual,separators=(',',':')).encode()).hexdigest()
            rec.update({'status':'pass','A':str(A),'B':str(B),'model_score_bits':score,
                        'relation_zero':R.is_zero(),'residual_score_bits':residual_bits,
                        'residual_digest':residual_digest})
            counts['candidate_pass'] += 1
            counts['rational_relation_hits'] += int(R.is_zero())
        except Exception as exc:
            rec.update({'status':'failure','error':f'{type(exc).__name__}: {exc}',
                        'model_score_bits':None,'relation_zero':None,
                        'residual_score_bits':None,'residual_digest':None})
            counts['candidate_failure'] += 1
        rows.append(rec)
    passed = [r for r in rows if r['status']=='pass']
    assert passed
    model_choice = min(passed, key=lambda r:(r['model_score_bits'],r['shift']))
    oracle_choice = min(passed, key=lambda r:(r['residual_score_bits'],r['model_score_bits'],r['shift']))
    centered = next(r for r in passed if r['shift']==[0,0,0,0])
    prior = next(r for r in passed if r['shift']==query['chosen_shift'])
    assert prior['model_score_bits']==query['score_bits']
    summaries.append({'event_index':event,'vector_index':vi,'p':p,'a':a,'b':b,
                      'attempts':len(rows),'pass':len(passed),'failures':len(rows)-len(passed),
                      'rational_relation_hits':sum(r['relation_zero'] for r in passed),
                      'model_choice':{'shift':model_choice['shift'],'model_score_bits':model_choice['model_score_bits'],
                                      'residual_score_bits':model_choice['residual_score_bits']},
                      'oracle_choice':{'shift':oracle_choice['shift'],'model_score_bits':oracle_choice['model_score_bits'],
                                       'residual_score_bits':oracle_choice['residual_score_bits']},
                      'centered_residual_score_bits':centered['residual_score_bits'],
                      'prior_residual_score_bits':prior['residual_score_bits']})
    parts_meta.append(packed(f'candidates.event{event:03d}.jsonl.gz',rows))
    counts['admitted_hits'] += 1
    if time.monotonic()-START > P['run_cap_seconds']:
        raise TimeoutError('frozen run cap exceeded')

result = {'schema':'xedni-wide-shift-defect-result-v1','status':'complete',
          'protocol_sha256':hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest(),
          'counts':counts,'summaries':summaries,'candidate_parts':parts_meta,
          'elapsed_wall_seconds':time.monotonic()-START}
(H/'run-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'counts':counts,
                  'elapsed_wall_seconds':result['elapsed_wall_seconds']},sort_keys=True))
