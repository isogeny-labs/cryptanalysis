#!/usr/bin/env sage -python
"""Exact target-conditioned inverse of the third N41 pair product on 33 panels."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path

import psutil
from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GEOMETRY = ROOT / 'n41_w8_fixed_sum_table_20261009/geometry.json'
CASES = ROOT / 'n41_w8_two_code_affine_span_20261013/cases.jsonl'
PANELS = ROOT / 'n41_w8_three_code_target_gate_20261013/result.json'
PUBLIC = ROOT / 'n41_w8_fixedseed_ordinary_join_20261013/protocol.json'
CURVE = ROOT / 'n41_w8_fixed_sum_table_20261009/audit.py'

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    assert digest(__file__) == protocol['producer_sha256']
    assert digest(HERE / 'sage_runtime_info.json') == protocol['runtime_sha256']
    for rel, expected in protocol['inputs'].items():
        assert digest(ROOT / rel) == expected, rel
    assert not (HERE / 'result.json').exists()
    setup_start = time.monotonic_ns()
    geometry = json.loads(GEOMETRY.read_text())
    panels = json.loads(PANELS.read_text())['panels']
    public = json.loads(PUBLIC.read_text())
    spec = importlib.util.spec_from_file_location('n41_curve_audit', CURVE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    curve, elem, integer = module.sage_curve()
    field = curve.base_field()
    one, zero = field.one(), field.zero()
    third = geometry['blocks'][2]
    source_products = {}
    source_columns = []
    for code in range(40):
        state = third['states'][4 * code]
        bits = 0
        for k, basis in enumerate(third['product_basis']):
            if state['a'] >> k & 1:
                bits ^= basis
        assert bits not in source_products
        source_products[bits] = code
        source_columns.append(set(state['columns']))
    assert len(source_products) == 40 and 1 not in source_products
    prefix_columns = [[set(block['states'][4 * code]['columns']) for code in range(40)]
                      for block in geometry['blocks'][:2]]
    case_roots = []
    with CASES.open() as stream:
        for line in stream:
            row = json.loads(line)
            i, j = row['left_code'], row['right_code']
            for raw in row['reciprocal_coordinates']:
                v = elem(raw)
                assert v != one
                u = v / (one + v)
                case_roots.append((i, j, u, u*u, (u+one)**2, u*(u+one)))
    assert len(case_roots) == 1554 * 8
    target = curve(elem(public['raw_target'][0]), elem(public['raw_target'][1]))
    seed_square = elem(third['s'])**2
    # Identity in GF(2)[A,B,D,S,r], including the exceptional value r=1.
    symbolic = PolynomialRing(GF(2), names=('A','B','D','S','r'))
    A0, B0, D0, S0, r0 = symbolic.gens()
    extension = PolynomialRing(symbolic, 'd')
    d0 = extension.gen()
    resultant = ((1+r0)*d0*d0+r0*d0+S0).resultant(A0*d0*d0+B0*d0+D0)
    M0 = (1+r0)*B0+r0*A0
    N0 = (1+r0)*D0+S0*A0
    norm = (1+r0)*N0*N0+r0*N0*M0+S0*M0*M0
    assert norm == (1+r0)*resultant
    assert resultant == (D0+S0*A0)**2+S0*B0**2 \
        +r0*B0*(D0+S0*(A0+B0))+r0**2*D0*(A0+B0+D0)
    setup_ns = time.monotonic_ns() - setup_start

    def inverse_roots(c0, c1, c2):
        if c2 == zero:
            if c1 == zero:
                return None if c0 == zero else ()
            return (c0/c1,)
        if c1 == zero:
            return ((c0/c2).sqrt(),)
        b = c1/c2
        a = (c0/c2)/(b*b)
        y, q = zero, a
        for _ in range(21):
            y += q
            q = q**4
        if y*y+y != a:
            return ()
        return (b*y, b*(y+one))

    points = {}
    def point(block, state_id):
        key = (block, state_id)
        if key not in points:
            x, y = geometry['blocks'][block]['states'][state_id]['raw_sum']
            points[key] = curve(elem(x), elem(y))
        return points[key]

    all_hits, full_matches, panel_rows = [], [], []
    target_start = time.monotonic_ns()
    for panel_index, panel in enumerate(panels):
        panel_start = time.monotonic_ns()
        ids = panel['suffix_state_ids']
        suffix = sum((point(k, sid) for k, sid in enumerate(ids, 3)), curve(0))
        suffix_columns = set().union(*(set(geometry['blocks'][k]['states'][sid]['columns'])
                                       for k, sid in enumerate(ids, 3)))
        residual = target - suffix
        assert residual != curve(0) and residual[0] != one
        t = one/(residual[0]+one)
        t2, tp12, tau = t*t, (t+one)**2, t*(t+one)
        counts = {'queries': 0, 'degree_0': 0, 'degree_1': 0, 'degree_2': 0,
                  'field_roots': 0, 'source_product_hits': 0,
                  'admissible_hits': 0, 'full_point_matches': 0}
        for i, j, u, u2, up12, utau in case_roots:
            A = t2 + utau*tau + tp12
            B = utau*tau
            D = up12*t2 + u2*tp12
            c0 = (D+seed_square*A)**2+seed_square*B**2
            c1 = B*(D+seed_square*(A+B))
            c2 = D*(A+B+D)
            counts['queries'] += 1
            counts['degree_' + str(2 if c2 else (1 if c1 else 0))] += 1
            roots = inverse_roots(c0, c1, c2)
            assert roots is not None
            for r in roots:
                assert c0+c1*r+c2*r*r == zero
                counts['field_roots'] += 1
                code = source_products.get(integer(r))
                if code is None:
                    continue
                counts['source_product_hits'] += 1
                if not source_columns[code].isdisjoint(prefix_columns[0][i]
                                                        | prefix_columns[1][j]
                                                        | suffix_columns):
                    continue
                counts['admissible_hits'] += 1
                all_hits.append([panel_index, i, j, code, integer(u), integer(r)])
                for left_id in range(4*i, 4*i+4):
                    for right_id in range(4*j, 4*j+4):
                        prefix = point(0, left_id)+point(1, right_id)
                        if prefix == curve(0) or prefix[0] == one \
                                or one/(prefix[0]+one) != u:
                            continue
                        for third_id in range(4*code, 4*code+4):
                            if prefix+point(2, third_id)+suffix == target:
                                counts['full_point_matches'] += 1
                                full_matches.append([panel_index, left_id, right_id,
                                                     third_id, ids])
        panel_rows.append({'panel_index': panel_index, 'kind': panel['kind'],
                           'suffix_state_ids': ids, 'residual_chart': integer(t),
                           'counts': counts, 'target_dependent_ns': time.monotonic_ns()-panel_start})
    target_ns = time.monotonic_ns()-target_start
    result = {'status': 'PASS_N41_FULL_PANEL_QUADRATIC_INVERSE', 'candidate_id': None,
              'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
              'setup_ns': setup_ns, 'target_dependent_ns': target_ns,
              'panels': panel_rows, 'coordinate_hits': all_hits,
              'full_matches': full_matches,
              'peak_process_rss_sample_bytes': psutil.Process().memory_info().rss,
              'protocol_sha256': digest(HERE / 'protocol.json')}
    (HERE / 'result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print({'status': result['status'], 'panels': len(panel_rows),
           'queries': sum(x['counts']['queries'] for x in panel_rows),
           'coordinate_hits': all_hits, 'full_matches': full_matches,
           'target_dependent_s': round(target_ns/1e9, 3)})

if __name__ == '__main__':
    main()
