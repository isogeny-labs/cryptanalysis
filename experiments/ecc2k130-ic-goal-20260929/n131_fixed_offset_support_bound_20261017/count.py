"""Source-bound uniform-target coverage screen for fixed-offset N131 codes."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n131_projected_root_lookup_screen_20261015'
CURVE = ROOT / 'n131_w2_m15_official_single_target_4g_20261003/field_curve_record.json'
ALLSEED = ROOT / 'n131_w18_allseed_fourpair_20261012/RESULT.md'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, obj):
    with (HERE / name).open('x') as out:
        json.dump(obj, out, sort_keys=True, indent=2)
        out.write('\n')


def paths():
    return {'script': Path(__file__), 'table': SOURCE / 'canonical_table.bin',
            'table_receipt': SOURCE / 'prepare_result.json',
            'curve_record': CURVE, 'allseed_report': ALLSEED}


def freeze():
    save('protocol.json', {
        'status': 'FROZEN_N131_FIXED_OFFSET_SOURCE_COVERAGE_SCREEN',
        'candidate_id': None, 'curve_id': 'EC1N131Ckb1heb5f1998f20b',
        'source_sha256': {k: sha(v) for k, v in paths().items()},
        'states_per_code_upper': 4,
        'reason': 'two recorded pair-output x roots per valid code, each with at most two signed curve points',
        'target_law': 'uniform point in the recorded prime-order subgroup; fixed source policy',
    })


def run():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    assert protocol['source_sha256'] == {k: sha(v) for k, v in paths().items()}
    receipt = json.loads((SOURCE / 'prepare_result.json').read_text())
    curve = json.loads(CURVE.read_text())
    order = int(curve['curve']['subgroup_order'])
    raw = (SOURCE / 'canonical_table.bin').read_bytes()
    assert sha(SOURCE / 'canonical_table.bin') == receipt['table_sha256']
    assert receipt['status'] == 'PASS_N131_CANONICAL_PROJECTED_ROOT_TABLE'
    assert len(raw) == (1 << 17)*68
    valid = sum(any(raw[i*68:i*68+34]) for i in range(1 << 17))
    assert valid == receipt['valid_codes'] == 33191
    assert receipt['raw_root_values'] == 2*valid
    max_states = protocol['states_per_code_upper']*valid
    rows = []
    for slots in range(4, 9):
        numerator = max_states**slots
        rows.append({'slots': slots, 'labeled_assignment_upper': str(numerator),
                     'uniform_target_mean_upper_exact': f'{numerator}/{order}',
                     'uniform_target_mean_upper_decimal': format(numerator/order, '.12g'),
                     'below_one': numerator < order})
    assert [row['below_one'] for row in rows] == [True, True, True, True, False]
    allseed_states = 34482792912
    assert str(allseed_states) in ALLSEED.read_text().replace(',', '')
    save('result.json', {
        'status': 'PASS_FIXED_OFFSET_ARITY_SCREEN', 'candidate_id': None,
        'protocol_sha256': sha(HERE / 'protocol.json'),
        'valid_codes_independent_scan': valid,
        'recorded_raw_roots': receipt['raw_root_values'],
        'point_states_per_slot_upper': max_states,
        'subgroup_order': str(order), 'rows': rows,
        'first_arity_with_ceiling_at_least_one': 8,
        'allseed_signed_pair_states_per_slot': allseed_states,
        'allseed_to_restricted_state_ratio_decimal': format(allseed_states/max_states, '.12g'),
    })
    print('PASS_FIXED_OFFSET_ARITY_SCREEN', valid, rows[0]['uniform_target_mean_upper_decimal'])


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'run')
    {'freeze': freeze, 'run': run}[sys.argv[1]]()
