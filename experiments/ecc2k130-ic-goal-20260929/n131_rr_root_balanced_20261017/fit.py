"""Fit one exact quadratic certificate across both roots of four codes."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
OLD = ROOT / 'n41_rr_quadratic_separator_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main():
    start = time.monotonic()
    protocol = json.loads((D / 'protocol.json').read_text())
    assert protocol['producer_sha256'] == sha(Path(__file__))
    assert all(sha(Path(path)) == digest for path, digest in protocol['sources'].items())
    train = json.loads((OLD / 'transfer_result.json').read_text())
    holdout = json.loads((OLD / 'holdout_result.json').read_text())
    assert json.loads((OLD / 'transfer_audit_result.json').read_text())['status'] == 'N131_SYMBOLIC_TRANSFER_AUDIT_PASS'
    assert json.loads((OLD / 'holdout_audit_result.json').read_text())['status'] == 'N131_ALTERNATE_ROOT_INDEPENDENT_AUDIT_PASS'
    charts = {}
    for i in protocol['train_codes']:
        charts[2 * i] = train['values'][str(i)]
        charts[2 * i + 1] = holdout['rows'][i]['values']
    assert len(charts) == 8 and all(len(values) == 64 and all(values) for values in charts.values())
    screen = module('screen_balanced', OLD / 'screen.py')
    factor = module('factor_balanced', OLD / 'factor.py')
    n = 131
    screen.N = factor.N = n
    screen.QUADRATIC_FEATURES = factor.WIDTH = n + n * (n - 1) // 2
    linear = screen.run_order(charts, range(8), 1)
    quadratic = screen.run_order(charts, range(8), 2)
    assert quadratic['accepted_masks'] == list(range(8))
    poly = int(quadratic['certificate_hex'], 16)
    rows = factor.quadratic_rows(poly)
    remaining = [1 << i for i in range(n)]
    basis = []
    while True:
        choice = next(((i, j) for i in range(len(remaining))
                       for j in range(i + 1, len(remaining))
                       if factor.polar(rows, remaining[i], remaining[j])), None)
        if choice is None:
            break
        i, j = choice
        left, right = remaining[i], remaining[j]
        rest = [v for k, v in enumerate(remaining) if k not in (i, j)]
        next_rest = []
        for v in rest:
            adjusted = v
            if factor.polar(rows, v, right):
                adjusted ^= left
            if factor.polar(rows, v, left):
                adjusted ^= right
            next_rest.append(adjusted)
        basis.extend((left, right))
        remaining = next_rest
    rank = len(basis)
    basis.extend(remaining)
    inverse = factor.inverse_basis(basis)
    linear_mask = 0
    for i, v in enumerate(basis):
        if factor.monomial_eval(poly, v):
            linear_mask ^= inverse[i]
    products = [(inverse[2*k], inverse[2*k+1]) for k in range(rank//2)]
    for i in range(n):
        v = 1 << i
        assert factor.monomial_eval(poly,v) == factor.factored_eval(linear_mask,products,v)
        for j in range(i+1,n):
            w = v | (1 << j)
            assert factor.monomial_eval(poly,w) == factor.factored_eval(linear_mask,products,w)
    result = {'status': 'ROOT_BALANCED_FOUR_CODE_CERTIFICATE',
              'protocol_sha256': sha(D / 'protocol.json'),
              'linear': linear, 'quadratic': quadratic,
              'polar_rank': rank, 'and_gates': rank//2,
              'linear_mask_hex': hex(linear_mask),
              'product_masks_hex': [[hex(a),hex(b)] for a,b in products],
              'train_value_count': 512, 'wall_s': time.monotonic()-start}
    (D / 'result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({'status':result['status'],
                      'linear_charts':len(linear['accepted_masks']),
                      'quadratic_charts':len(quadratic['accepted_masks']),
                      'and_gates':rank//2,'wall_s':result['wall_s']}))


if __name__ == '__main__':
    main()
