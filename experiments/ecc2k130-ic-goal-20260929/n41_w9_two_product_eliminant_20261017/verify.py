"""Verify frozen bindings and the terminal N41 two-product stage results."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


bindings = [
    ('protocol.json', 'result.json', {
        'script': HERE / 'build_sage.py',
        'runtime': HERE / 'sage_runtime_info.json',
        'states': ROOT / 'n41_n131_w29_rotation_alignment_20261017/aligned_states.json',
        'relation': ROOT / 'n41_n131_w29_rotation_alignment_20261017/n41_audit_result.json',
        'prior': ROOT / 'n41_w9_triple_box_s3_20261017/full_result.json',
    }),
    ('group_audit_protocol.json', 'group_audit_result.json', {
        'script': HERE / 'audit_group_sage.py',
        'runtime': HERE / 'group_audit_runtime_info.json',
        'states': ROOT / 'n41_n131_w29_rotation_alignment_20261017/aligned_states.json',
        'producer': HERE / 'result.json',
    }),
    ('resultant_audit_protocol_v2.json', 'resultant_audit_result_v2.json', {
        'script': HERE / 'audit_resultant_sage_v2.py',
        'runtime': HERE / 'resultant_audit_runtime_info_v2.json',
        'producer': HERE / 'result.json',
    }),
    ('root_probe_protocol_v2.json', 'root_probe_result_v2.json', {
        'script': HERE / 'root_probe_sage.py',
        'runtime': HERE / 'root_probe_runtime_info_v2.json',
        'states': ROOT / 'n41_n131_w29_rotation_alignment_20261017/aligned_states.json',
        'eliminant': HERE / 'result.json',
        'group_audit': HERE / 'group_audit_result.json',
        'resultant_audit': HERE / 'resultant_audit_result_v2.json',
    }),
    ('root_python_audit_protocol.json', 'root_python_audit_result.json', {
        'script': HERE / 'audit_root_python.py',
        'states': ROOT / 'n41_n131_w29_rotation_alignment_20261017/aligned_states.json',
        'eliminant': HERE / 'result.json',
        'root_probe': HERE / 'root_probe_result_v2.json',
    }),
]

for protocol_name, result_name, sources in bindings:
    protocol = read(protocol_name)
    result = read(result_name)
    assert result['protocol_sha256'] == sha(HERE / protocol_name), protocol_name
    assert all(protocol['source_sha256'][key] == sha(path)
               for key, path in sources.items()), protocol_name
    assert result['status'].startswith('PASS_'), result_name

producer = read('result.json')
group = read('group_audit_result.json')
algebra = read('resultant_audit_result_v2.json')
probe = read('root_probe_result_v2.json')
python = read('root_python_audit_result.json')
assert producer['candidate_id'] is None and producer['term_count'] == 13
assert producer['algebraic_zero_code_pairs'] == [[61, 16]]
assert group['signed_pair_assignments_checked'] == 80656
assert group['exact_state_witnesses'] == [[61, 16, 244, 66]]
assert algebra['all_coefficients_equal'] and algebra['final_term_count'] == 13
assert [row['method'] for row in probe['runs']] == ['scan', 'norm', 'norm', 'scan']
assert all(row['valid_code_hits'] == [[61, 16]] and
           row['subspace_field_roots'] == 1 for row in probe['runs'])
assert python['evaluations'] == 71 * 256
assert python['valid_code_hits'] == [[61, 16]]
assert read('root_probe_failure_v1.json')['status'] == 'PRODUCER_FAILURE_SAGE_NTL_ABORT'
assert read('resultant_audit_failure_v1.json')['status'] == 'PRODUCER_FAILURE_SERIALIZATION'

lean = (HERE / 'lean.stdout').read_text()
source = (HERE / 'TwoProductEliminant.lean').read_text()
for declaration in ('quadratic_common_root', 'linear_remainder_norm', 'two_product_sound'):
    assert f"'TwoProductEliminant.{declaration}' depends on axioms: " in lean
assert 'sorry' not in source and 'admit' not in source
assert not (HERE / 'lean.stderr').read_text()

print(json.dumps({'status': 'PASS_TERMINAL_BINDINGS',
                  'protocol_count': len(bindings),
                  'algebraic_zero_pairs': producer['algebraic_zero_code_pairs'],
                  'root_methods': [row['method'] for row in probe['runs']]}))
