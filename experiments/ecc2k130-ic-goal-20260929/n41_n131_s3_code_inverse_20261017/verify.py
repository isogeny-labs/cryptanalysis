"""Read-only terminal binding for direct S3 inverse evidence."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ALIGN = ROOT / 'n41_n131_w29_rotation_alignment_20261017'
QUOTIENT = ROOT / 'n41_n131_aligned_quotient_transfer_20261017'
QUARTIC = ROOT / 'n41_n131_two_code_quartic_inverse_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def check_protocol(name, paths):
    protocol = load(HERE / name)
    for key, path in paths.items():
        assert protocol['source_sha256'][key] == sha(path), (name, key)
    return protocol


check_protocol('protocol.json', {
    'script': HERE / 'run_sage.py',
    'runtime': HERE / 'sage_runtime_info.json',
    'states': ALIGN / 'aligned_states.json',
    'relation_audit': ALIGN / 'n41_audit_result.json',
    'panel': QUOTIENT / 'n41_panel_result.json',
    'panel_audit': QUOTIENT / 'n41_panel_audit_result.json',
    'quartic_result': QUARTIC / 'result.json',
})
check_protocol('audit_protocol.json', {
    'script': HERE / 'audit_field.py',
    'producer': HERE / 'result.json',
    'states': ALIGN / 'aligned_states.json',
    'panel': QUOTIENT / 'n41_panel_result.json',
})
check_protocol('n131_protocol.json', {
    'script': HERE / 'n131_probe_sage.py',
    'runtime': HERE / 'sage_runtime_info.json',
    'sample': QUOTIENT / 'n131_result.json',
    'sample_audit': QUOTIENT / 'n131_audit_result.json',
    'group_audit': QUOTIENT / 'n131_group_audit_result.json',
    'control': ALIGN / 'n131_aligned_control.json',
    'public': ALIGN / 'build_n131_result.json',
})
check_protocol('n131_audit_protocol.json', {
    'script': HERE / 'audit_n131_field.py',
    'producer': HERE / 'n131_result.json',
    'sample': QUOTIENT / 'n131_result.json',
    'control': ALIGN / 'n131_aligned_control.json',
})
check_protocol('trace_protocol.json', {
    'script': HERE / 'trace_census_sage.py',
    'runtime': HERE / 'sage_runtime_info.json',
    'n41_states': ALIGN / 'aligned_states.json',
    'n41_result': HERE / 'result.json',
    'n131_sample': QUOTIENT / 'n131_result.json',
    'n131_control': ALIGN / 'n131_aligned_control.json',
    'n131_result': HERE / 'n131_result.json',
})
n41 = load(HERE / 'result.json')
n41audit = load(HERE / 'audit_result.json')
n131 = load(HERE / 'n131_result.json')
n131audit = load(HERE / 'n131_audit_result.json')
trace = load(HERE / 'trace_result.json')
quartic = load(QUARTIC / 'result.json')
assert n41['status'] == 'PASS_N41_DIRECT_S3_SOURCE_CODE_INVERSE_PANEL'
assert n41['candidate_id'] is None and len(n41['queries']) == 65
assert n41['total_s3_quadratics'] == 9230
assert n41['total_s3_field_roots'] == 18460
assert n41['total_source_code_family_hits'] == 1
assert n41['queries'][0]['source_code_family_indices'] == [1529]
assert n41['queries'][0]['exact_group_family_indices'] == [1529]
assert all(not row['source_code_family_indices'] and not row['exact_group_family_indices']
           for row in n41['queries'][1:])
assert n41['protocol_sha256'] == sha(HERE / 'protocol.json')
assert n41audit['status'] == 'PASS_INDEPENDENT_FULL_N41_DIRECT_S3_INVERSE_PANEL'
assert n41audit['queries'] == 65 and n41audit['total_s3_quadratics'] == 9230
assert n41audit['total_s3_field_roots'] == 18460
assert n41audit['total_source_code_family_hits'] == 1
assert n41audit['source_sha256']['producer'] == sha(HERE / 'result.json')
assert len(quartic['queries']) == 5
for index in range(5):
    assert n41['queries'][index]['source_code_family_indices'] == \
        quartic['queries'][index]['source_code_family_indices']
    assert n41['queries'][index]['s3_field_roots'] == \
        quartic['queries'][index]['field_roots_enumerated']
assert n131['status'] == 'PASS_N131_DIRECT_S3_INVERSE_SOURCE_SAMPLE'
assert n131['candidate_id'] is None
assert n131['sampled_valid_codes'] == 512
assert n131['source_codes_with_controls'] == 514
assert len(n131['queries']) == 2
assert [row['s3_quadratics'] for row in n131['queries']] == [1028, 1028]
assert [row['field_roots'] for row in n131['queries']] == [2056, 2056]
assert n131['queries'][0]['sample_source_pair_hits'] == [[512, 513]]
assert n131['queries'][1]['sample_source_pair_hits'] == []
assert n131['protocol_sha256'] == sha(HERE / 'n131_protocol.json')
assert n131audit['status'] == 'PASS_INDEPENDENT_N131_DIRECT_S3_SOURCE_SAMPLE'
assert n131audit['queries'] == 2
assert n131audit['total_s3_quadratics'] == 2056
assert n131audit['total_field_roots'] == 4112
assert n131audit['source_pair_hits'] == [[[512, 513]], []]
assert n131audit['source_sha256']['producer'] == sha(HERE / 'n131_result.json')
assert trace['status'] == 'PASS_N41_N131_CURVE_TRACE_SEPARATION'
assert trace['n41']['normalized_rhs_checks'] == 9230
assert trace['n131']['normalized_rhs_checks'] == 2056
assert trace['n41']['nonzero_trace_count'] == trace['n131']['nonzero_trace_count'] == 0
assert trace['protocol_sha256'] == sha(HERE / 'trace_protocol.json')
for name in ('run.stderr', 'audit.stderr', 'n131.stderr', 'n131_audit.stderr',
             'trace.stderr', 'lean.stderr'):
    assert not (HERE / name).read_bytes(), name
for name in ('run.stdout', 'audit.stdout', 'n131.stdout', 'n131_audit.stdout',
             'trace.stdout'):
    assert b'PASS_' in (HERE / name).read_bytes(), name
lean = (HERE / 'S3Inverse.lean').read_text()
assert all(token not in lean for token in ('sorry', 'admit', 'sorryAx', 'axiom '))
assert (HERE / 'lean-toolchain').read_text().strip() == 'leanprover/lean4:v4.34.1'
axioms = (HERE / 'lean.stdout').read_text()
for theorem in ('s3_second_quadratic', 'halftrace_root_sound',
                'recover_second_product', 'normalized_rhs_separates',
                'normalized_rhs_trace_zero'):
    assert f"'S3Inverse.{theorem}' depends on axioms: [propext, Classical.choice, Quot.sound]" in axioms
assert "'S3Inverse.reciprocal_curve_trace_zero' does not depend on any axioms" in axioms

artifacts = [
    'protocol.json', 'audit_protocol.json', 'n131_protocol.json',
    'n131_audit_protocol.json', 'trace_protocol.json',
    'result.json', 'audit_result.json', 'n131_result.json',
    'n131_audit_result.json', 'trace_result.json', 'S3Inverse.lean',
    'lean.stdout', 'sage_runtime_info.json', 'RESULT.md', 'PROOF_MAP.md',
]
print(json.dumps({
    'status': 'PASS_TERMINAL_DIRECT_S3_CODE_INVERSE',
    'n41_queries': 65, 'n41_s3_quadratics': 9230,
    'n131_queries': 2, 'n131_s3_quadratics': 2056,
    'artifact_sha256': {name: sha(HERE / name) for name in artifacts},
}, sort_keys=True, indent=2))
