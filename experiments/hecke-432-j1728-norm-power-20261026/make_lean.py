"""Generate exact Lean numeral identities for the norm power certificates."""
import json
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GATE = ROOT / 'experiments/hecke-432-j1728-sqrt2-resultants-20261026/bridge_gate.json'


def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    audit_protocol = json.loads((HERE / 'audit_protocol.json').read_text())
    cp = HERE / 'power_certificate.json'
    assert sha256(GATE.read_bytes()).hexdigest() == protocol['input_sha256']['bridge_gate']
    assert sha256(cp.read_bytes()).hexdigest() == audit_protocol['power_certificate_sha256']
    cert = json.loads(cp.read_text())
    norms = {row['name']: row for row in json.loads(GATE.read_text())['norms']}
    lines = [
        'import Mathlib.Tactic.NormNum',
        'import Mathlib.Data.Nat.Prime.Defs',
        'import Mathlib.Algebra.Prime.Defs',
        '',
        'namespace J1728NormPowers',
        '',
    ]
    for name, theorem_name in [('base_unit', 'base_unit_sixth_power'),
                               ('pair_resultant_4', 'quartic_resultant_norm_cube'),
                               ('pair_resultant_8', 'octic_resultant_norm_cube')]:
        n = abs(int(norms[name]['numerator']))
        root = int(cert[name]['root'])
        exponent = cert[name]['exponent']
        assert root ** exponent == n
        lines += [
            f'/-- Exact saved norm numerator for `{name}` is an integer {exponent}th power. -/',
            f'theorem {theorem_name} :',
            f'    ({n} : ℕ) = ({root} : ℕ) ^ {exponent} := by',
            '  norm_num',
            '',
            f'#print axioms {theorem_name}',
            '',
        ]
    lines += [
        '/-- Taking a cube does not change the prime divisors of a natural number. -/',
        'theorem prime_divides_cube_iff {p n : ℕ} (hp : Nat.Prime p) :',
        '    p ∣ n ^ 3 ↔ p ∣ n := by',
        '  have hp_prime : Prime p := (Nat.prime_iff).mp hp',
        '  exact hp_prime.dvd_pow_iff_dvd (by decide : (3 : ℕ) ≠ 0)',
        '',
        '#print axioms prime_divides_cube_iff',
        '',
        'end J1728NormPowers',
    ]
    dest = HERE / 'formal/NormPowers.lean'
    dest.parent.mkdir(exist_ok=True)
    dest.write_text('\n'.join(lines) + '\n')
    print(json.dumps({'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
                      'lean_sha256': sha256(dest.read_bytes()).hexdigest(),
                      'declarations': 4}, sort_keys=True))


if __name__ == '__main__':
    main()
