"""Prospective exact norm gate over the 1–10 million prime interval."""
import json
from hashlib import sha256
from pathlib import Path

from sympy import primerange

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'bridge_gate': ROOT / 'experiments/hecke-432-j1728-sqrt2-resultants-20261026/bridge_gate.json',
    'million_result': ROOT / 'experiments/hecke-432-j1728-sqrt2-million-20261026/result.json',
    'field_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'resolvent': ROOT / 'experiments/hecke-432-relative-resolvent-20261025/relative_resolvent.json',
    'branch_formula': ROOT / 'experiments/hecke-432-b-coordinate-resolvent-20261025/branch_formula.json',
    'coordinate_map': ROOT / 'experiments/hecke-27-coordinate-bridge-20261025/coordinate_map.json',
}


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_TEN_MILLION_GATE_SCAN'
    for name, path in INPUTS.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    gate = json.loads(INPUTS['bridge_gate'].read_text())
    prior = json.loads(INPUTS['million_result'].read_text())
    assert gate['status'] == 'EXACT_FULL_REDUCTION_BRIDGE_GATE'
    assert prior['status'] == 'PASS_EXACT_MILLION_CAP_SCREEN'
    cap = protocol['prime_cap_exclusive']
    previous_cap = 1000000
    D = int(gate['coefficient_denominator_lcm'])
    count = 0
    exceptions = []
    for raw in primerange(previous_cap, cap):
        p = int(raw)
        if p % 24 != protocol['prime_class_mod_24']:
            continue
        count += 1
        reasons = []
        if D % p == 0:
            reasons.append('coefficient_denominator')
        for norm in gate['norms']:
            for part in ('numerator', 'denominator'):
                if int(norm[part]) % p == 0:
                    reasons.append(norm['name'] + '_' + part)
        if reasons:
            exceptions.append({'prime': p, 'reasons': reasons})
    output = {
        'status': 'PASS_PROSPECTIVE_TEN_MILLION_GATE_SCAN',
        'scope': 'prime cells with 1000000<=p<10000000 and p congruent 11 mod 24',
        'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
        'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
        'new_prime_cells': count,
        'new_certified_good_cells': count - len(exceptions),
        'new_exception_cells': exceptions,
        'cumulative_prime_cells': prior['prime_cells'] + count,
        'cumulative_certified_good_cells': prior['norm_certified_good_cells'] + count - len(exceptions),
    }
    (HERE / 'scan_result.json').write_text(json.dumps(output, sort_keys=True, indent=2) + '\n')
    print(json.dumps({key: value for key, value in output.items()
                      if key in ('status', 'new_prime_cells', 'new_certified_good_cells',
                                 'new_exception_cells')}, sort_keys=True))


if __name__ == '__main__':
    main()
