"""Independent checked-Sage norm power and prime-factor verification."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import ZZ, prod

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GATE = ROOT / 'experiments/hecke-432-j1728-sqrt2-resultants-20261026/bridge_gate.json'


def main():
    pp = HERE / 'protocol.json'
    protocol = json.loads(pp.read_text())
    ap = HERE / 'audit_protocol.json'
    audit_protocol = json.loads(ap.read_text())
    cp = HERE / 'power_certificate.json'
    assert sha256(cp.read_bytes()).hexdigest() == audit_protocol['power_certificate_sha256']
    cert = json.loads(cp.read_text())
    assert sha256(GATE.read_bytes()).hexdigest() == protocol['input_sha256']['bridge_gate']
    norms = {row['name']: row for row in json.loads(GATE.read_text())['norms']}
    checked = []
    for name in ('base_unit', 'pair_resultant_4', 'pair_resultant_8'):
        record = cert[name]
        number = abs(ZZ(norms[name]['numerator']))
        root = ZZ(record['root'])
        sage_root, exact = number.nth_root(record['exponent'], truncate_mode=True)
        assert exact and sage_root == root and root ** record['exponent'] == number
        checked.append({'name': name, 'power_exponent': record['exponent'],
                        'root_digits': len(str(root))})
    factor_rows = []
    factors = cert['pair_resultant_4']['root_factorization']
    assert ZZ(prod(ZZ(p) ** e for p, e in factors)) == ZZ(cert['pair_resultant_4']['root'])
    for p, exponent in factors:
        assert ZZ(p).is_prime(proof=True)
        factor_rows.append({'prime': str(p), 'exponent': exponent,
                            'proven_prime': True, 'class_mod_24': p % 24})
    small = cert['pair_resultant_8']['factors_below_10000000']
    residual = ZZ(cert['pair_resultant_8']['remaining_cofactor'])
    assert residual > 0
    assert residual * prod(ZZ(p) ** e for p, e in small) == ZZ(cert['pair_resultant_8']['root'])
    assert all(ZZ(p).is_prime(proof=True) for p, e in small)
    out = {'status': 'PASS_INDEPENDENT_SAGE_NORM_POWER_AND_PRIME_FACTOR_AUDIT',
           'audit_protocol_sha256': sha256(ap.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'checked_powers': checked,
           'quartic_root_prime_factors': factor_rows,
           'octic_remaining_cofactor_digits': len(str(residual))}
    (HERE / 'power_audit.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'checked_powers': checked,
                      'quartic_prime_factors': len(factor_rows)}, sort_keys=True))


if __name__ == '__main__':
    main()
