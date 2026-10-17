"""Read-only verification of the fixed-offset source-capacity screen."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n131_projected_root_lookup_screen_20261015'
CURVE = ROOT / 'n131_w2_m15_official_single_target_4g_20261003/field_curve_record.json'
ALLSEED = ROOT / 'n131_w18_allseed_fourpair_20261012/RESULT.md'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    result = json.loads((HERE / 'result.json').read_text())
    assert protocol['status'] == 'FROZEN_N131_FIXED_OFFSET_SOURCE_COVERAGE_SCREEN'
    assert protocol['source_sha256'] == {
        'script': sha(HERE / 'count.py'),
        'table': sha(SOURCE / 'canonical_table.bin'),
        'table_receipt': sha(SOURCE / 'prepare_result.json'),
        'curve_record': sha(CURVE), 'allseed_report': sha(ALLSEED)}
    assert result['protocol_sha256'] == sha(HERE / 'protocol.json')
    assert result['status'] == 'PASS_FIXED_OFFSET_ARITY_SCREEN'
    n = result['valid_codes_independent_scan']
    r = int(result['subgroup_order'])
    assert n == 33191 and result['recorded_raw_roots'] == 2*n
    assert result['point_states_per_slot_upper'] == 4*n == 132764
    assert r == 680564733841876926932320129493409985129
    assert result['first_arity_with_ceiling_at_least_one'] == 8
    for row in result['rows']:
        m = row['slots']
        numerator = (4*n)**m
        assert row['labeled_assignment_upper'] == str(numerator)
        assert row['uniform_target_mean_upper_exact'] == f'{numerator}/{r}'
        assert row['below_one'] == (numerator < r)
    assert [row['slots'] for row in result['rows']] == list(range(4, 9))
    assert "'SupportBound.tuples_length' depends on axioms: [propext]" in (HERE / 'lean.stdout').read_text()
    assert "'SupportBound.seven_slot_capacity_below_group' does not depend on any axioms" in (HERE / 'lean.stdout').read_text()
    assert "'SupportBound.eight_slot_capacity_reaches_group' does not depend on any axioms" in (HERE / 'lean.stdout').read_text()
    assert not (HERE / 'lean.stderr').read_bytes()
    lean = (HERE / 'SupportBound.lean').read_text()
    assert all(x not in lean for x in ('sorry', 'admit', 'sorryAx', 'native_decide'))
    print('PASS_FIXED_OFFSET_SUPPORT_BOUND_VERIFY', n, result['first_arity_with_ceiling_at_least_one'])


if __name__ == '__main__':
    main()
