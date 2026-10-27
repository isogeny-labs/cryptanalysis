"""Independent checked-Sage replay of the four-source residual certificate."""
import hashlib
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, GF

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())
POST = json.loads((HERE / 'post-run.json').read_text())


def pinned(name):
    item = PLAN['frozen'][name]
    raw = (ROOT / item['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == item['sha256']
    return json.loads(raw)


def main():
    raw = (HERE / 'result.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == POST['result_sha256']
    result = json.loads(raw)
    p, q = PLAN['p'], PLAN['q']
    E = EllipticCurve(GF(p), [0, -1, 1, -10, -20])
    assert int(E.cardinality()) == 63275
    logs = pinned('class-logs.json')
    cls = next(x for x in pinned('class-result.json')['cases'] if x['p'] == p)
    T = E(*logs['anchor_point'])
    assert int(T.order()) == q
    base = [25 * E(x, y) for x, y in cls['class_points']]
    a = logs['q_logs']
    assert len(base) == len(a) == 40
    assert all(B == z * T for B, z in zip(base, a))

    # Sage group points, rather than the producer's modular sums, determine the residual set.
    triple_points = set()
    for indices in itertools.combinations(range(40), 3):
        for signs in itertools.product((-1, 1), repeat=3):
            triple_points.add(sum((s * base[i] for i, s in zip(indices, signs)), E(0)))
    table = {z * T: z for z in range(q)}
    assert len(table) == q
    missing = [z for z in range(q) if z * T not in triple_points]
    assert len(triple_points) == result['triple_coverage_points'] == 2503
    assert missing == result['triple_residual_scalars'] and len(missing) == 28

    witnessed = []
    for row in result['residual_rows']:
        z = row['scalar']
        assert z in missing and row['status'] == 'FOUND' and 1 <= row['probes'] <= 80
        witness = row['witness']
        assert witness is not None and len(witness) == 8
        indices = witness[::2]
        signs = witness[1::2]
        assert len(set(indices)) == 4 and all(0 <= i < 40 for i in indices)
        assert all(s in (-1, 1) for s in signs)
        assert sum((s * base[i] for i, s in zip(indices, signs)), E(0)) == z * T
        assert sum(s * a[i] for i, s in zip(indices, signs)) % q == z
        witnessed.append(z)
    assert witnessed == missing

    # Independent complete four-source coverage enumeration using scalar logs.
    covered = set()
    patterns = 0
    for indices in itertools.combinations(range(40), 4):
        for signs in itertools.product((-1, 1), repeat=4):
            covered.add(sum(s * a[i] for i, s in zip(indices, signs)) % q)
            patterns += 1
    assert patterns == result['four_patterns'] == 1462240
    assert len(covered) == result['four_coverage_points'] == q
    assert result['four_uncovered_scalars'] == []
    out = {'schema': 'hecke-d79-p63317-four-term-audit-v1', 'status': 'PASS',
           'p': p, 'q': q, 'triple_coverage_points': len(triple_points),
           'triple_residual_scalars': missing, 'residuals_verified_by_group': len(witnessed),
           'four_patterns': patterns, 'four_coverage_points': len(covered)}
    (HERE / 'audit.json').write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': 'PASS', 'residuals_verified': len(witnessed),
                      'four_coverage': len(covered)}))


if __name__ == '__main__':
    main()
