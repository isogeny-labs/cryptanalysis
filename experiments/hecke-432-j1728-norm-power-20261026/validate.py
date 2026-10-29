"""Bind the power, prime-factor, large-prime, and Lean receipts."""
import json
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GATE = ROOT / 'experiments/hecke-432-j1728-sqrt2-resultants-20261026/bridge_gate.json'


def read(name):
    path = HERE / name
    return json.loads(path.read_text()), sha256(path.read_bytes()).hexdigest()


def main():
    protocol, protocol_hash = read('protocol.json')
    power, power_hash = read('power_certificate.json')
    power_audit, power_audit_hash = read('power_audit.json')
    large, large_hash = read('large_prime_result.json')
    large_audit, large_audit_hash = read('large_prime_audit.json')
    assert power['status'] == 'EXACT_NORM_POWER_AND_QUARTIC_FACTOR_CERTIFICATE'
    assert power_audit['status'] == 'PASS_INDEPENDENT_SAGE_NORM_POWER_AND_PRIME_FACTOR_AUDIT'
    assert large['status'] == 'PASS_REGISTERED_LARGE_PRIME_SOURCE_AND_BRANCH_REPLAY'
    assert large_audit['status'] == 'PASS_INDEPENDENT_LARGE_PRIME_GCD_AND_EQUATION_REPLAY'
    assert power['protocol_sha256'] == large['protocol_sha256'] == protocol_hash
    assert power_audit['quartic_root_prime_factors'] == [
        {'prime': str(p), 'exponent': e, 'proven_prime': True,
         'class_mod_24': p % 24}
        for p, e in protocol['frozen_factorization_of_quartic_cube_root']]
    p = protocol['large_prime']
    assert str(p) == large['prime'] == large_audit['prime']
    assert large['source_points'] == large_audit['source_points'] == 2
    assert large['rational_CE_pairs'] == large_audit['rational_CE_pairs'] == 2
    assert large['zero_branch_pairs'] == 2
    assert large_audit['root_factor_degrees'] == [4, 4]
    assert large_audit['polynomial_multiplications'] == 373
    gate = json.loads(GATE.read_text())
    assert sha256(GATE.read_bytes()).hexdigest() == protocol['input_sha256']['bridge_gate']
    residues = {row['name']: int(row['numerator']) % p == 0 for row in gate['norms']}
    assert [name for name, zero in residues.items() if zero] == ['pair_resultant_4']
    lean_path = HERE / 'formal/NormPowers.lean'
    lean_hash = sha256(lean_path.read_bytes()).hexdigest()
    out = {'status': 'PASS_NORM_POWER_AND_LARGE_PRIME_EVIDENCE',
           'protocol_sha256': protocol_hash,
           'artifact_sha256': {'power_certificate.json': power_hash,
                               'power_audit.json': power_audit_hash,
                               'large_prime_result.json': large_hash,
                               'large_prime_audit.json': large_audit_hash,
                               'formal/NormPowers.lean': lean_hash},
           'large_prime': str(p), 'large_prime_class_mod_24': p % 24,
           'large_prime_gate_failure': 'pair_resultant_4_numerator',
           'source_points': 2, 'rational_CE_pairs': 2,
           'zero_branch_pairs': 2,
           'octic_remaining_cofactor_digits': power['pair_resultant_8']['remaining_cofactor_digits']}
    (HERE / 'validation.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
