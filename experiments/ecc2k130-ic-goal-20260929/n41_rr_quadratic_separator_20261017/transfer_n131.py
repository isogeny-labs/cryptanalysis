"""Transfer the quadratic separator to the archived N131 four-chart panel."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
ARCHIVE = ROOT / 'n41_n131_rr_code_family_span_20261017'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    start = time.monotonic()
    protocol = json.loads((D / 'transfer_protocol.json').read_text())
    assert protocol['producer_sha256'] == sha(Path(__file__))
    for path, digest in protocol['sources'].items():
        assert sha(Path(path)) == digest, path
    panel = json.loads((ARCHIVE / 'panel_n131_v2.json').read_text())
    prior = json.loads((ARCHIVE / 'result_n131_v2.json').read_text())
    prior_audit = json.loads((ARCHIVE / 'audit_result_n131.json').read_text())
    assert prior_audit['status'] == 'PASS_INDEPENDENT_N131_DETERMINANT_RANK_REPLAY'
    assert len(panel['variants']) == len(prior['rows']) == len(prior_audit['rows']) == 4
    n = panel['field_degree']
    assert n == 131
    rr = module('rr_transfer', ROOT / 'n41_n131_sixpair_rr_root_span_20261016' / 'run.py')
    screen = module('quadratic_screen_transfer', D / 'screen.py')
    factor = module('quadratic_factor_transfer', D / 'factor.py')
    screen.N = factor.N = n
    screen.QUADRATIC_FEATURES = factor.WIDTH = n + n * (n - 1) // 2
    field = rr.Field(n, panel['field_modulus'])
    charts = {}
    metadata = []
    for i, variant in enumerate(panel['variants']):
        points = [variant['roots'][0][0]] + panel['fixed_points']
        coeff = rr.coefficients([p[0] for p in points], [p[1] for p in points],
                                panel['target'], field)
        assert coeff is not None
        digest = hashlib.sha256(json.dumps(coeff).encode()).hexdigest()
        assert digest == prior['rows'][i]['coefficient_sha256']
        assert digest == prior_audit['rows'][i]['coefficient_sha256']
        values = [rr.evaluate(coeff, sign) for sign in range(64)]
        assert all(values) and prior['rows'][i]['determinant_zero_sign_masks'] == []
        charts[i] = values
        metadata.append({'chart_index': i, 'sample_index': variant['sample_index'],
                         'coefficient_sha256': digest})
    linear = screen.run_order(charts, range(4), 1)
    quadratic = screen.run_order(charts, range(4), 2)
    assert len(linear['accepted_masks']) == 3
    assert len(quadratic['accepted_masks']) == 4
    poly = int(quadratic['certificate_hex'], 16)
    rows = factor.quadratic_rows(poly)
    remaining = [1 << i for i in range(n)]
    basis = []
    pairs_count = 0
    while True:
        choice = next(((i, j) for i in range(len(remaining))
                       for j in range(i + 1, len(remaining))
                       if factor.polar(rows, remaining[i], remaining[j])), None)
        if choice is None:
            break
        i, j = choice
        left, right = remaining[i], remaining[j]
        rest = [value for k, value in enumerate(remaining) if k not in (i, j)]
        next_rest = []
        for value in rest:
            adjusted = value
            if factor.polar(rows, value, right):
                adjusted ^= left
            if factor.polar(rows, value, left):
                adjusted ^= right
            assert factor.polar(rows, adjusted, left) == 0
            assert factor.polar(rows, adjusted, right) == 0
            next_rest.append(adjusted)
        basis.extend((left, right))
        pairs_count += 1
        remaining = next_rest
    basis.extend(remaining)
    inverse = factor.inverse_basis(basis)
    assert all(factor.polar(rows, basis[i], basis[j]) ==
               (i // 2 == j // 2 and i != j and i < 2 * pairs_count and j < 2 * pairs_count)
               for i in range(n) for j in range(n))
    linear_mask = 0
    for i, word in enumerate(basis):
        if factor.monomial_eval(poly, word):
            linear_mask ^= inverse[i]
    products = [(inverse[2 * k], inverse[2 * k + 1])
                for k in range(pairs_count)]
    for i in range(n):
        word = 1 << i
        assert factor.monomial_eval(poly, word) == factor.factored_eval(linear_mask, products, word)
        for j in range(i + 1, n):
            word |= 1 << j
            assert factor.monomial_eval(poly, word) == factor.factored_eval(linear_mask, products, word)
            word ^= 1 << j
    assert all(factor.factored_eval(linear_mask, products, value) == 1
               for values in charts.values() for value in values)
    result = {'status': 'N131_FOUR_CHART_QUADRATIC_TRANSFER',
              'protocol_sha256': sha(D / 'transfer_protocol.json'),
              'field_degree': n, 'target': panel['target'],
              'chart_metadata': metadata,
              'values': {str(i): values for i, values in charts.items()},
              'linear': linear, 'quadratic': quadratic,
              'polarization_rank': 2 * pairs_count, 'and_gates': pairs_count,
              'linear_mask_hex': hex(linear_mask),
              'product_masks_hex': [[hex(a), hex(b)] for a, b in products],
              'coefficient_checks': 1 + n + n * (n - 1) // 2,
              'wall_s': time.monotonic() - start}
    (D / 'transfer_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': result['status'],
                      'linear_charts': len(linear['accepted_masks']),
                      'quadratic_charts': len(quadratic['accepted_masks']),
                      'rank': result['polarization_rank'],
                      'and_gates': pairs_count, 'wall_s': result['wall_s']}))


if __name__ == '__main__':
    main()
