"""Bind the falsified overlap prediction and corrected derivative replay."""
import json
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    first = read('result.json')
    assert first['status'] == 'PREDICTION_MISMATCH'
    assert first['prediction_matches'] == [False, False, True]
    expected = [
        ('414340033', 72, 141, 0, 426, 3),
        ('431435018569', 72, 141, 0, 426, 3),
        ('414340153', 72, 0, 0, 0, 0),
    ]
    for row, (p, q, o, intersection, lifts, zeros) in zip(first['results'], expected):
        assert (row['prime'], row['quartic_roots'], row['octic_roots'],
                row['overlap_roots'], row['E_lifts'], row['branch_zero_roots']) == (
                    p, q, o, intersection, lifts, zeros)
    corrected = read('multiplicity_result.json')
    audit = read('audit_result.json')
    assert corrected['status'] == 'PASS_FROZEN_DERIVATIVE_BRANCH_CRITERION'
    assert corrected['prediction_matches']
    assert audit['status'] == 'PASS_INDEPENDENT_DERIVATIVE_GCD_AND_BRANCH_AUDIT'
    assert len(corrected['results']) == len(audit['results']) == 4
    expected_repeats = [(0, 3, 3), (0, 3, 3), (0, 0, 0), (1, 0, 1)]
    root_total = 0
    for row, checked, (q_repeat, o_repeat, zero) in zip(
            corrected['results'], audit['results'], expected_repeats):
        assert row['criterion_matches']
        assert (row['quartic_repeated'], row['octic_repeated'], row['branch_zero']) == (
            q_repeat, o_repeat, zero)
        assert checked['prime'] == row['prime']
        assert checked['repeated_roots'] == checked['branch_zero_roots'] == zero
        root_total += checked['rational_factor_roots']
    assert root_total == 499
    holdout = read('holdout_result.json')
    assert holdout['status'] == 'QUARTIC_HOLDOUT_PREDICTION_MISMATCH'
    assert not holdout['prediction_matches']
    assert [r['prime'] for r in holdout['results']] == ['4196094289', '669968600281']
    assert all(r['classification']['rational_C_points'] == 0 and
               r['classification']['rational_CE_pairs'] == 0 and
               r['repeated_quartic_roots'] == 0 for r in holdout['results'])
    frobenius = read('frobenius_result.json')
    frobenius_audit = read('frobenius_audit_result.json')
    assert frobenius['status'] == 'PASS_SIX_PRIME_SOURCE_FROBENIUS_FACTORIZATION'
    assert frobenius_audit['status'] == 'PASS_INDEPENDENT_SIX_PRIME_FROBENIUS_GCD_AUDIT'
    assert [r['gcd_degrees_for_extensions_1_2_3'] for r in
            frobenius_audit['rows']] == [
                [18, 18, 18], [18, 18, 18], [18, 18, 18],
                [2, 18, 2], [0, 0, 18], [0, 0, 18]]
    assert [sorted(piece['degree'] for piece in row['factors'])
            for row in frobenius['rows']] == [
                [1] * 18, [1] * 18, [1] * 18, [1] * 2 + [2] * 8,
                [3] * 6, [3] * 6]
    lean = (HERE / 'formal/lean-check.txt').read_text()
    assert 'Exit: 0' in lean
    assert "repeated_root_iff_derivative_root' depends on axioms: [propext, Classical.choice, Quot.sound]" in lean
    files = ['protocol.json', 'result.json', 'multiplicity_protocol.json',
             'multiplicity_result.json', 'audit_protocol.json', 'audit_result.json',
             'holdout_protocol.json', 'holdout_result.json',
             'frobenius_protocol.json', 'frobenius_result.json',
             'frobenius_audit_protocol.json', 'frobenius_audit_result.json',
             'formal/RepeatedRoot.lean']
    out = {'status': 'PASS_FALSIFIED_OVERLAP_AND_CHECKED_DERIVATIVE_CRITERION',
           'rational_factor_roots_checked': root_total,
           'repeated_branch_zero_roots': 7,
           'quartic_holdout_source_points': [0, 0],
           'artifact_sha256': {name: sha256((HERE / name).read_bytes()).hexdigest()
                               for name in files}}
    (HERE / 'validation.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
