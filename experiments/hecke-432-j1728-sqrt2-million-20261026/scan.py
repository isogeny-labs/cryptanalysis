"""Exact modular screen for the frozen million-prime cap."""
import json
from hashlib import sha256
from pathlib import Path

from sympy import primerange

HERE = Path(__file__).resolve().parent


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_MILLION_CAP_SCAN'
    inputs = {}
    for name in ('input_bridge_gate', 'input_bounded_result'):
        record = protocol[name]
        path = Path(record['path'])
        digest = sha256(path.read_bytes()).hexdigest()
        assert digest == record['sha256']
        inputs[name] = json.loads(path.read_text())
    gate = inputs['input_bridge_gate']
    earlier = inputs['input_bounded_result']
    assert gate['status'] == 'EXACT_FULL_REDUCTION_BRIDGE_GATE'
    assert earlier['status'] == 'PASS_BOUNDED_11_MOD_24_GATE_ACCOUNTING'
    cap = protocol['prime_cap_exclusive']
    residue = protocol['prime_class_mod_24']
    denominator = int(gate['coefficient_denominator_lcm'])
    counts = {'below_20000': 0, 'from_20000': 0}
    exceptions = []
    for p in primerange(7, cap):
        p = int(p)
        if p % 24 != residue:
            continue
        counts['below_20000' if p < 20000 else 'from_20000'] += 1
        reasons = []
        if denominator % p == 0:
            reasons.append('coefficient_denominator')
        for norm in gate['norms']:
            for part in ('numerator', 'denominator'):
                if int(norm[part]) % p == 0:
                    reasons.append(norm['name'] + '_' + part)
        if reasons:
            exceptions.append({'prime': p, 'reasons': reasons})
    assert counts['below_20000'] == earlier['prime_cells']
    assert [row['prime'] for row in exceptions if row['prime'] < 20000] == [
        row['prime'] for row in earlier['direct_exception_cells']
    ]
    output = {
        'status': 'PASS_EXACT_MILLION_CAP_SCREEN',
        'scope': 'all primes 7<=p<1000000 congruent 11 mod 24',
        'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
        'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
        'prime_cells': sum(counts.values()),
        'prime_cells_below_20000': counts['below_20000'],
        'prime_cells_from_20000': counts['from_20000'],
        'norm_certified_good_cells': sum(counts.values()) - len(exceptions),
        'exception_cells': exceptions,
        'new_exception_cells': [row for row in exceptions if row['prime'] >= 20000],
    }
    (HERE / 'result.json').write_text(json.dumps(output, sort_keys=True, indent=2) + '\n')
    print(json.dumps({key: value for key, value in output.items()
                      if key in ('status', 'prime_cells', 'norm_certified_good_cells',
                                 'new_exception_cells')}, sort_keys=True))


if __name__ == '__main__':
    main()
