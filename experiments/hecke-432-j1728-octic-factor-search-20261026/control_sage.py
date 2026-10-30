"""Nearby p ≡ 1 (mod 24) control outside the saved norm divisors."""
import importlib.util
import json
from hashlib import sha256
from pathlib import Path

from sage.all import ZZ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'power_certificate': ROOT / 'experiments/hecke-432-j1728-norm-power-20261026/power_certificate.json',
    'prime_classifier': HERE / 'classify_primes_sage.py',
    'source_helpers': ROOT / 'experiments/hecke-432-j1728-norm-power-20261026/classify_large_sage.py',
    'factor_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'coordinate_map': ROOT / 'experiments/hecke-27-coordinate-bridge-20261025/coordinate_map.json',
    'resolvent': ROOT / 'experiments/hecke-432-relative-resolvent-20261025/relative_resolvent.json',
    'branch_formula': ROOT / 'experiments/hecke-432-b-coordinate-resolvent-20261025/branch_formula.json',
}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    path = HERE / 'control_protocol.json'
    protocol = json.loads(path.read_text())
    for name, source in INPUTS.items():
        assert sha256(source.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    p = ZZ(protocol['prime'])
    assert p.is_prime(proof=True) and p % 24 == 1
    power = json.loads(INPUTS['power_certificate'].read_text())
    assert ZZ(power['pair_resultant_4']['root']) % p != 0
    assert ZZ(power['pair_resultant_8']['root']) % p != 0
    classify = load('classify_primes', INPUTS['prime_classifier']).classify
    helpers = load('source_helpers', INPUTS['source_helpers'])
    field = json.loads(INPUTS['factor_certificate'].read_text())
    coord = json.loads(INPUTS['coordinate_map'].read_text())['source_j']
    resolvent = json.loads(INPUTS['resolvent'].read_text())['terms']
    branch = json.loads(INPUTS['branch_formula'].read_text())
    row = classify(p, field, coord, resolvent, branch, helpers)
    out = {'status': 'PASS_SAME_CLASS_CONTROL_CLASSIFIED',
           'protocol_sha256': sha256(path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'prime_proved': True, 'absent_from_both_norm_roots': True, 'row': row}
    (HERE / 'control_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({k: row[k] for k in ('prime', 'field_poly_rational_roots',
          'rational_C_points', 'rational_CE_pairs', 'zero_branch_pairs')},
          sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
