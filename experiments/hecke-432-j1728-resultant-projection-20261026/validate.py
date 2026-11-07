"""Bind the exact resultant, finite reductions, independent audits, and Lean proof."""
import json
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    protocol = read('protocol.json')
    result = read('result.json')
    audit = read('audit_result.json')
    exact_protocol = read('exact_protocol.json')
    attempt = read('exact_attempt.json')
    exact = read('exact_result.json')
    exact_audit = read('exact_audit_result.json')
    assert protocol['status'] == 'FROZEN_BEFORE_RESULTANT_PROJECTION_REPLAY'
    assert result['status'] == 'PASS_RESULTANT_PROJECTION_AND_DERIVATIVE_BRIDGE'
    assert result['universal_resultant_formula_verified']
    assert result['source_points_checked'] == 56
    assert result['rational_roots_checked'] == 499
    assert result['coefficient_identities_match'] and result['derivative_criteria_match']
    assert audit['status'] == 'PASS_INDEPENDENT_EIGHT_TERM_RESULTANT_AUDIT'
    assert audit['source_points_checked'] == 56 and audit['rational_roots_checked'] == 499
    assert exact_protocol['status'] == 'FROZEN_BEFORE_EXACT_SOURCE_FIELD_RESULTANT_IDENTITY'
    assert attempt['status'] == 'COMPLETED' and attempt['returncode'] == 0
    assert exact['status'] == 'PASS_EXACT_SOURCE_FIELD_RESULTANT_IDENTITY'
    assert exact['source_field_degree'] == 18
    assert exact['resultant_degree'] == exact['xe_resolvent_degree'] == 12
    assert exact['scalar_coordinates_low_to_high'] == ['-16']
    assert exact['coefficient_identity']
    assert exact_audit['status'] == 'PASS_DIRECT_EXACT_RESULTANT_AND_FACTOR_AUDIT'
    assert exact_audit['direct_resultant_scalar'] == '-16'
    assert exact_audit['factor_degrees'] == [4, 8]
    assert exact_audit['factor_product_exact'] and exact_audit['factors_irreducible']
    assert len(result['rows']) == 56 and len(audit['rows']) == 56
    for row in result['rows']:
        p = int(row['prime'])
        assert row['scalar'] == str((-16) % p)
        assert row['coefficient_identity'] and row['root_derivative_criterion']
    lean = (HERE / 'formal/lean-check.txt').read_text()
    assert 'Exit: 0' in lean and 'sorryAx' not in lean
    assert "J1728Projection.sylvester_resultant_formula' depends on axioms:" in lean
    files = ['protocol.json', 'result.json', 'audit_protocol.json',
             'audit_result.json', 'exact_protocol.json', 'exact_attempt.json',
             'exact_result.json', 'exact_audit_protocol.json',
             'exact_audit_result.json', 'formal/UniversalResultant.lean']
    out = {'status': 'PASS_EXACT_RESULTANT_PROJECTION_LEAN_AND_FINITE_REPLAY',
           'exact_source_field_scalar': '-16',
           'source_field_degree': 18,
           'source_points_checked': 56,
           'rational_roots_checked': 499,
           'artifact_sha256': {name: sha256((HERE / name).read_bytes()).hexdigest()
                               for name in files}}
    (HERE / 'validation.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
