"""Bind the bounded search, prime replays, control, and proof receipts."""
import json
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    source = read('../hecke-432-j1728-norm-power-20261026/power_certificate.json')
    original = int(source['pair_resultant_8']['remaining_cofactor'])
    p1 = read('pm1_result.json')
    composite = 178760799831235072777
    assert p1['status'] == 'COMPLETED_BOUNDED_PM1_SEARCH'
    assert {(r['bound'], r['base']) for r in p1['rows'] if int(r['gcd']) == composite} == {
        (100000, 2), (100000, 3), (1000000, 2), (1000000, 3)}
    assert original % composite == 0
    prime = read('prime_result.json')
    audit = read('audit_result.json')
    control = read('control_result.json')
    control_audit = read('control_audit_result.json')
    remaining = read('remaining_pm1_result.json')
    assert prime['status'] == 'PROVED_PRIME_SPLIT_AND_SOURCE_REPLAY'
    assert prime['prime_factors_proved']
    assert list(map(int, prime['prime_factors'])) == [414340033, 431435018569]
    assert int(prime['prime_factors'][0]) * int(prime['prime_factors'][1]) == composite
    assert all(int(source['pair_resultant_4']['root']) % int(p) != 0
               for p in prime['prime_factors'])
    assert int(prime['remaining_cofactor']) * composite == original
    assert len(prime['remaining_cofactor']) == 210
    assert audit['status'] == 'PASS_INDEPENDENT_TWO_PRIME_LOCAL_GCD_AND_EQUATION_AUDIT'
    assert [r['prime'] for r in audit['rows']] == prime['prime_factors']
    for measured, checked in zip(prime['rows'], audit['rows']):
        assert measured['rational_C_points'] == checked['source_points'] == 18
        assert measured['rational_CE_pairs'] == checked['rational_CE_pairs'] == 426
        assert measured['zero_branch_pairs'] == checked['branch_zero_pattern']['11'] == 6
        assert checked['branch_zero_pattern']['00'] == 420
        assert checked['base_factor_degrees'] == {'4': 144, '8': 282}
        assert sorted(r['rational_x_E_roots'] for r in measured['rows']) == [11] * 3 + [12] * 15
    assert control['status'] == 'PASS_SAME_CLASS_CONTROL_CLASSIFIED'
    assert control['prime_proved'] and control['absent_from_both_norm_roots']
    assert control_audit['status'] == 'PASS_INDEPENDENT_SAME_CLASS_CONTROL_GCD_AUDIT'
    assert control['row']['rational_C_points'] == control_audit['source_points'] == 18
    assert control_audit['rational_x_E_roots'] == 72
    assert control['row']['rational_CE_pairs'] == control_audit['rational_CE_pairs'] == 0
    assert remaining['status'] == 'COMPLETED_REMAINING_PM1'
    assert all(r['status'] == 'NO_PROPER_FACTOR' and r['gcd'] == '1'
               for r in remaining['rows'])
    assert read('result.json')['status'] == 'TIME_LIMIT'
    lean = (HERE / 'formal/lean-check.txt').read_text()
    assert 'Exit: 0' in lean and "octic_cofactor_split' depends on axioms: [propext]" in lean
    assert "pm1_divisor_split' depends on axioms: [propext]" in lean
    files = ['pm1_result.json', 'prime_result.json', 'audit_result.json',
             'control_result.json', 'control_audit_result.json',
             'remaining_pm1_result.json', 'formal/OcticFactors.lean']
    out = {'status': 'PASS_OCTIC_SPLIT_REPLAY_CONTROL_AND_LEAN',
           'prime_factors': prime['prime_factors'],
           'remaining_cofactor_digits': len(prime['remaining_cofactor']),
           'source_points_each': 18, 'exceptional_CE_pairs_each': 426,
           'same_class_control_CE_pairs': 0,
           'artifact_sha256': {name: sha256((HERE / name).read_bytes()).hexdigest()
                               for name in files}}
    (HERE / 'validation.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
