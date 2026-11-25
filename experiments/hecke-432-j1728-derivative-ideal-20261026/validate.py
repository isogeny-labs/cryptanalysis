"""Bind the cubic-gcd replay, independent Sage audit, and Lean proof."""
import json
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    protocol = read('protocol.json')
    result = read('result.json')
    audit_protocol = read('audit_protocol.json')
    audit = read('audit_result.json')
    assert protocol['status'] == 'FROZEN_BEFORE_CUBIC_QUADRATIC_GCD_REPLAY'
    assert result['status'] == 'PASS_FROZEN_CUBIC_QUADRATIC_GCD_CRITERION'
    assert result['prediction_matches']
    assert result['protocol_sha256'] == sha256((HERE / 'protocol.json').read_bytes()).hexdigest()
    assert audit_protocol['status'] == 'FROZEN_BEFORE_INDEPENDENT_SAGE_CUBIC_GCD_AUDIT'
    assert audit['status'] == 'PASS_INDEPENDENT_SAGE_CUBIC_GCD_AND_BRANCH_IDENTITY_AUDIT'
    assert audit['protocol_sha256'] == sha256(
        (HERE / 'audit_protocol.json').read_bytes()).hexdigest()
    assert [r['gcd_degree_histogram'] for r in result['results']] == [
        {'1': 210, '2': 3}, {'1': 210, '2': 3}, {'1': 72}, {'2': 1}]
    assert [r['root_count'] for r in result['results']] == [213, 213, 72, 1]
    assert [r['quadratic_rational_B_root_counts'] for r in audit['rows']] == [
        [2, 2, 2], [2, 2, 2], [], [0]]
    total = 0
    quadratic = 0
    for field, checked in zip(result['results'], audit['rows']):
        assert field['prime'] == checked['prime']
        assert field['root_count'] == checked['roots_checked']
        for row in field['rows']:
            total += 1
            assert row['prediction_matches']
            assert row['common_B_gcd_squarefree']
            assert row['common_B_gcd_degree'] in (1, 2)
            assert row['branch_values_zero'] == row['repeated_factor_root'] == (
                row['common_B_gcd_degree'] == 2)
            quadratic += row['common_B_gcd_degree'] == 2
    assert total == 499 and quadratic == 7
    lean = (HERE / 'formal/lean-check.txt').read_text()
    assert 'Exit: 0' in lean and 'sorryAx' not in lean
    for theorem in ('elimination_identity', 'branch_equation',
                    'two_common_roots_force_indeterminacy',
                    'indeterminate_branch_forces_cubic_on_remainder_roots',
                    'two_remainder_roots_common_iff_indeterminate'):
        assert f"BranchCollision.{theorem}' depends on axioms:" in lean
    files = ['protocol.json', 'result.json', 'audit_protocol.json',
             'audit_result.json', 'formal/BranchCollision.lean']
    out = {'status': 'PASS_CUBIC_GCD_BRANCH_BRIDGE_AND_LEAN',
           'rational_factor_roots_checked': total,
           'quadratic_common_B_factors': quadratic,
           'split_quadratics_at_octic_primes': 6,
           'irreducible_quadratics_at_quartic_prime': 1,
           'artifact_sha256': {name: sha256((HERE / name).read_bytes()).hexdigest()
                               for name in files}}
    (HERE / 'validation.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
