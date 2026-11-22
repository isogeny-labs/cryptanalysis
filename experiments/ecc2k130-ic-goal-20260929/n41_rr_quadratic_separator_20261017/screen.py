"""Exact quadratic no-zero certificates for N41 RR code/sign charts."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
RR_SOURCE = ROOT / 'n41_n131_sixpair_rr_root_span_20261016' / 'run.py'
SPEC = importlib.util.spec_from_file_location('rr_det', RR_SOURCE)
rr = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rr)
GEOMETRY = ROOT / 'n41_w8_fixed_sum_table_20261009' / 'geometry.json'
WITNESS = ROOT / 'n41_sixpair_shared_target_20261017' / 'join_audit_result.json'
N = 41
QUADRATIC_FEATURES = N + N * (N - 1) // 2


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def roots(block, mask):
    states = [row for row in block['states'] if row['a'] == mask]
    assert len(states) == 4
    by_x = {}
    for row in states:
        x, y = row['raw_sum']
        by_x.setdefault(x, set()).add(y)
    assert len(by_x) == 2 and all(len(ys) == 2 for ys in by_x.values())
    return [[[x, y] for y in sorted(by_x[x])] for x in sorted(by_x)]


def features(word, degree):
    assert degree in (1, 2) and word >> N == 0
    result = word
    if degree == 2:
        position = N
        for i in range(N):
            for j in range(i + 1, N):
                if (word >> i & 1) and (word >> j & 1):
                    result |= 1 << position
                position += 1
        assert position == QUADRATIC_FEATURES
    return result


def extend(basis, values, degree):
    width = N if degree == 1 else QUADRATIC_FEATURES
    trial = dict(basis)
    for value in values:
        if value == 0:
            return None
        row = features(value, degree) | (1 << width)
        while row & ((1 << width) - 1):
            pivot = (row & ((1 << width) - 1)).bit_length() - 1
            if pivot in trial:
                row ^= trial[pivot]
            else:
                trial[pivot] = row
                break
        else:
            if row >> width & 1:
                return None
    return trial


def certificate(basis, degree):
    width = N if degree == 1 else QUADRATIC_FEATURES
    chosen = 0
    for pivot in sorted(basis):
        row = basis[pivot]
        rhs = (row >> width) & 1
        lower = row & ((1 << pivot) - 1)
        chosen |= (rhs ^ ((lower & chosen).bit_count() & 1)) << pivot
    return chosen


def evaluate_certificate(coeff, value, degree):
    return (coeff & features(value, degree)).bit_count() & 1


def run_order(charts, order, degree):
    basis = {}
    accepted = []
    rows = []
    for mask in order:
        candidate = extend(basis, charts[mask], degree)
        if candidate is not None:
            basis = candidate
            accepted.append(mask)
        rows.append({'mask': mask, 'accepted': candidate is not None,
                     'rank_after': len(basis)})
    coeff = certificate(basis, degree)
    assert all(evaluate_certificate(coeff, value, degree) == 1
               for mask in accepted for value in charts[mask])
    return {'accepted_masks': accepted, 'rejected_masks': [r['mask'] for r in rows
                                                         if not r['accepted']],
            'rank': len(basis), 'certificate_hex': hex(coeff),
            'certificate_weight': coeff.bit_count(),
            'quadratic_terms': (coeff >> N).bit_count() if degree == 2 else 0,
            'rows': rows}


def greedy_order(charts, degree):
    remaining = set(charts)
    order = []
    basis = {}
    while remaining:
        options = []
        for mask in remaining:
            trial = extend(basis, charts[mask], degree)
            if trial is not None:
                options.append((len(trial) - len(basis), mask, trial))
        if not options:
            break
        _, chosen, basis = min(options, key=lambda item: (item[0], item[1]))
        order.append(chosen)
        remaining.remove(chosen)
    return order + sorted(remaining)


def main():
    start = time.monotonic()
    protocol = json.loads((D / 'protocol.json').read_text())
    for path, digest in protocol['sources'].items():
        assert sha(Path(path)) == digest, path
    assert protocol['producer_sha256'] == sha(Path(__file__))
    geometry = json.loads(GEOMETRY.read_text())
    witness = json.loads(WITNESS.read_text())
    target = witness['raw_target']
    assert target == protocol['target']
    field = rr.Field(N, (1 << N) | (1 << 3) | 1)
    fixed = []
    for slot in range(1, 6):
        point = witness['pair_rows'][slot]
        options = roots(geometry['blocks'][slot], point['masks'][0])
        matching = [root for root in options if point['raw_sum'] in root]
        assert len(matching) == 1
        fixed.append(matching[0][0])
    assert len(fixed) == 5
    charts = {}
    row_meta = {}
    for mask in protocol['root0_masks']:
        root = roots(geometry['blocks'][0], mask)[0]
        points = [root[0]] + fixed
        coeff = rr.coefficients([p[0] for p in points],
                                [p[1] for p in points], target, field)
        assert coeff is not None
        values = [rr.evaluate(coeff, sign) for sign in range(64)]
        assert all(values)
        charts[mask] = values
        row_meta[mask] = {'mask': mask, 'root': 0,
                          'coefficient_sha256': hashlib.sha256(json.dumps(coeff).encode()).hexdigest(),
                          'distinct_values': len(set(values))}
    assert len(charts) == len(protocol['root0_masks']) == 35
    positive_mask = protocol['positive_mask']
    positive_root = roots(geometry['blocks'][0], positive_mask)[1]
    assert witness['pair_rows'][0]['raw_sum'] in positive_root
    points = [positive_root[0]] + fixed
    positive_coeff = rr.coefficients([p[0] for p in points],
                                      [p[1] for p in points], target, field)
    assert positive_coeff is not None
    positive_values = [rr.evaluate(positive_coeff, sign) for sign in range(64)]
    zero_signs = [sign for sign, value in enumerate(positive_values) if value == 0]
    assert zero_signs
    assert extend({}, positive_values, 1) is None
    assert extend({}, positive_values, 2) is None

    panels = {}
    for degree in (1, 2):
        sorted_order = sorted(charts)
        panels[str(degree)] = {
            'sorted': run_order(charts, sorted_order, degree),
            'greedy': run_order(charts, greedy_order(charts, degree), degree)}
    result = {'status': 'QUADRATIC_FAMILY_SCREEN_COMPLETE',
              'protocol_sha256': sha(D / 'protocol.json'),
              'field_degree': N, 'quadratic_feature_width': QUADRATIC_FEATURES,
              'root0_chart_count': len(charts),
              'sign_values_per_chart': 64,
              'root0_values': {str(mask): values for mask, values in charts.items()},
              'root0_metadata': {str(mask): meta for mask, meta in row_meta.items()},
              'positive_chart': {'mask': positive_mask, 'root': 1,
                                 'determinants': positive_values,
                                 'zero_signs': zero_signs},
              'panels': panels, 'wall_s': time.monotonic() - start}
    (D / 'result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': result['status'],
                      'linear_sorted': len(panels['1']['sorted']['accepted_masks']),
                      'linear_greedy': len(panels['1']['greedy']['accepted_masks']),
                      'quadratic_sorted': len(panels['2']['sorted']['accepted_masks']),
                      'quadratic_greedy': len(panels['2']['greedy']['accepted_masks']),
                      'wall_s': result['wall_s']}))


if __name__ == '__main__':
    main()
