"""Read-only replay of the source-law scope audit."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    result = json.loads((HERE / 'result.json').read_text())
    paths = {
        'n41_protocol': ROOT / 'n41_indexed_two_block_20261017/protocol.json',
        'n41_freeze': ROOT / 'n41_indexed_two_block_20261017/freeze_sage.py',
        'n131_projection': ROOT / 'n131_projected_root_lookup_screen_20261015/prepare_sage.py',
        'n131_pair_source': ROOT / 'n131_fixed_seed_eight_pair_circuit_20261010/fixed_pair_circuit.py',
        'n131_fixed_source': ROOT / 'n131_fixed_offset_support_bound_20261017/protocol.json',
        'n131_fixed_result': ROOT / 'n131_fixed_offset_support_bound_20261017/result.json',
        'n131_allseed_report': ROOT / 'n131_w18_allseed_fourpair_20261012/RESULT.md',
    }
    assert result['status'] == 'PASS_SOURCE_LAW_SCOPE_AUDIT'
    assert result['source_sha256'] == {k: sha(v) for k, v in paths.items()}
    assert result['n41_panel_slot_seeds'] == [7, 85, 94, 171]
    assert result['n41_options_per_slot'] == [9]*4
    assert result['n131_fixed_table_seed'] == 212
    assert result['n131_fixed_table_valid_codes'] == 33191
    assert result['n131_allseed_signed_states_per_rotation'] == 34482792912
    print('PASS_SOURCE_LAW_SCOPE_VERIFY')


if __name__ == '__main__':
    main()
