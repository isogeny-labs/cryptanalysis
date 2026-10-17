"""Read-only source-law audit for the indexed-join transfer claim."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
N41 = ROOT / 'n41_indexed_two_block_20261017'
N131 = ROOT / 'n131_projected_root_lookup_screen_20261015'
BOUND = ROOT / 'n131_fixed_offset_support_bound_20261017'
ALLSEED = ROOT / 'n131_w18_allseed_fourpair_20261012'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed_literal(path):
    tree = ast.parse(path.read_text())
    values = [ast.literal_eval(node.value) for node in tree.body
              if isinstance(node, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == 'SEED' for t in node.targets)]
    assert len(values) == 1
    return values[0]


def main():
    inputs = {
        'n41_protocol': N41 / 'protocol.json',
        'n41_freeze': N41 / 'freeze_sage.py',
        'n131_projection': N131 / 'prepare_sage.py',
        'n131_pair_source': ROOT / 'n131_fixed_seed_eight_pair_circuit_20261010/fixed_pair_circuit.py',
        'n131_fixed_source': BOUND / 'protocol.json',
        'n131_fixed_result': BOUND / 'result.json',
        'n131_allseed_report': ALLSEED / 'RESULT.md',
    }
    protocol = json.loads(inputs['n41_protocol'].read_text())
    fixed = json.loads(inputs['n131_fixed_result'].read_text())
    assert protocol['status'] == 'FROZEN_INDEXED_TWO_BLOCK_N41_SOURCE_AND_TARGETS'
    assert len(protocol['options']) == 4
    assert all(len(slot) == 9 for slot in protocol['options'])
    seeds = [sorted({a ^ b for a, b in slot}) for slot in protocol['options']]
    assert seeds == [[7], [85], [94], [171]]
    assert fixed['status'] == 'PASS_FIXED_OFFSET_ARITY_SCREEN'
    # The canonical table's seed is explicit in its source producer.
    source_seed = seed_literal(inputs['n131_pair_source'])
    assert source_seed == 212
    assert all(source_seed not in slot for slot in seeds)
    report = inputs['n131_allseed_report'].read_text()
    assert '34,482,792,912' in report
    assert fixed['allseed_signed_pair_states_per_slot'] == 34482792912
    record = {
        'status': 'PASS_SOURCE_LAW_SCOPE_AUDIT',
        'source_sha256': {name: sha(path) for name, path in inputs.items()},
        'n41_panel_slot_seeds': [slot[0] for slot in seeds],
        'n41_options_per_slot': [len(slot) for slot in protocol['options']],
        'n131_fixed_table_seed': source_seed,
        'n131_fixed_table_valid_codes': fixed['valid_codes_independent_scan'],
        'n131_allseed_signed_states_per_rotation': 34482792912,
        'interpretation': 'N41 indexed control is a witness-centered subsample of four different all-seed slots; the N131 materialization and arity bounds concern a separate fixed-seed table.',
    }
    with (HERE / 'result.json').open('x') as out:
        json.dump(record, out, indent=2, sort_keys=True)
        out.write('\n')
    print(record['status'], record['n41_panel_slot_seeds'], source_seed)


if __name__ == '__main__':
    main()
