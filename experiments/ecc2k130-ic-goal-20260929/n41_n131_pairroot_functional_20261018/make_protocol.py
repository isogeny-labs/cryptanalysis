"""Freeze the inputs and limits before either functional-root audit."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


shared = {'script': here/'audit_sage.py', 'runtime': here/'sage_runtime_info.json'}
inputs = {
    'n41': {
        'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
        'states': root/'n41_n131_w29_rotation_alignment_20261017/aligned_states.json',
        'fixture': root/'n41_w9_implicit_fivepair_tower_20261017/fixture.json',
        'w_table': root/'n41_w9_target_w_bdd_20261017/w_table.json',
    },
    'n131': {
        'curve_id': 'EC1N131Ckb1heb5f1998f20b',
        'sample': root/'n41_n131_aligned_quotient_transfer_20261017/n131_result.json',
        'previous': root/'n41_n131_s3_code_inverse_20261017/n131_result.json',
        'control': root/'n41_n131_w29_rotation_alignment_20261017/n131_aligned_control.json',
    },
}
for mode, record in inputs.items():
    out = here/f'{mode}_protocol.json'
    assert not out.exists()
    paths = {**shared, **{k:v for k,v in record.items() if k != 'curve_id'}}
    protocol = {'status': 'FROZEN_BEFORE_FUNCTIONAL_ROOT_AUDIT',
                'mode': mode, 'curve_id': record['curve_id'],
                'wall_cap_seconds': 120, 'rss_envelope_bytes': 4294967296,
                'sources': {str(v): sha(v) for v in paths.values()}}
    protocol.update({k: str(v) for k,v in record.items() if k != 'curve_id'})
    out.write_text(json.dumps(protocol, sort_keys=True, indent=2)+'\n')
    print(mode, sha(out))
