"""Read-only terminal check of frozen source, audit, and proof receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


def check_protocol(name, sources):
    protocol = load(name)
    for key, path in sources.items():
        assert protocol['source_sha256'][key] == sha(path), (name, key)
    return protocol


ROOT = HERE.parent
SRC = ROOT / 'n41_n131_w29_rotation_alignment_20261017'
N41_DESIGN = ROOT / 'n41_w9_lazy_source_20261017/circuit.py'
N131_DESIGN = ROOT / 'n41_n131_fivepair_w9_w29_20261017/circuit_n131_3p2.py'

check_protocol('protocol.json', {
    'script': HERE / 'n41_gate.py', 'design': N41_DESIGN,
    'states': SRC / 'aligned_states.json', 'audit': SRC / 'n41_audit_result.json'})
check_protocol('n41_sage_protocol.json', {
    'script': HERE / 'n41_gate_sage.py', 'design': N41_DESIGN,
    'states': SRC / 'aligned_states.json', 'audit': SRC / 'n41_audit_result.json',
    'runtime': HERE / 'sage_runtime_info.json'})
check_protocol('n41_panel_protocol.json', {
    'script': HERE / 'n41_gate_panel_sage.py', 'helper': HERE / 'n41_gate.py',
    'states': SRC / 'aligned_states.json',
    'public_witness_audit': SRC / 'n41_audit_result.json',
    'runtime': HERE / 'sage_runtime_info.json',
    'prior_census': HERE / 'n41_result.json'})
check_protocol('n131_protocol.json', {
    'script': HERE / 'n131_labels.py', 'design': N131_DESIGN,
    'branch_rank': SRC / 'branch_rank_result.json'})
check_protocol('n131_sage_protocol.json', {
    'script': HERE / 'n131_labels_sage.py', 'design': N131_DESIGN,
    'runtime': HERE / 'sage_runtime_info.json',
    'branch_rank': SRC / 'branch_rank_result.json'})
check_protocol('n41_audit_protocol.json', {
    'audit_script': HERE / 'audit_n41_fast.py',
    'producer': HERE / 'n41_result.json',
    'producer_protocol': HERE / 'n41_sage_protocol.json',
    'states': SRC / 'aligned_states.json'})
check_protocol('n41_panel_audit_protocol_v2.json', {
    'audit_script': HERE / 'audit_n41_panel_fast.py',
    'producer': HERE / 'n41_panel_result.json',
    'producer_protocol': HERE / 'n41_panel_protocol.json'})
check_protocol('n131_audit_protocol.json', {
    'audit_script': HERE / 'audit_n131_sage.py',
    'producer': HERE / 'n131_result.json',
    'producer_protocol': HERE / 'n131_sage_protocol.json',
    'runtime': HERE / 'sage_runtime_info.json'})
check_protocol('n131_group_audit_protocol_v2.json', {
    'group_audit_script': HERE / 'audit_n131_group_sage.py',
    'producer': HERE / 'n131_result.json',
    'runtime': HERE / 'sage_runtime_info.json'})

n41 = load('n41_result.json')
panel = load('n41_panel_result.json')
n41_audit = load('n41_audit_result.json')
panel_audit = load('n41_panel_audit_result.json')
n131 = load('n131_result.json')
n131_audit = load('n131_audit_result.json')
group_audit = load('n131_group_audit_result.json')
assert n41['status'] == 'PASS_EXACT_N41_TWO_CODE_QUOTIENT_GATE'
assert n41['two_code_families'] == 2485
assert n41['partial_additions'] == 39760
assert n41['quotient_surviving_indices'] == [1529, 2356]
assert n41['exact_surviving_indices'] == [1529]
assert n41['witness_family_index'] == 1529
assert n41_audit['status'] == 'PASS_INDEPENDENT_FULL_N41_QUOTIENT_CENSUS'
assert n41_audit['source_sha256']['producer'] == sha(HERE / 'n41_result.json')
assert n41_audit['label_hits'] == n41['quotient_surviving_indices']
assert panel['status'] == 'PASS_EXACT_N41_TWO_CODE_QUOTIENT_PANEL'
assert len(panel['miss_panel']) == 64 and panel['miss_panel_draws'] == 68
assert panel['miss_panel_quotient_survivors'] == 8
assert panel['miss_panel_exact_survivors'] == 0
assert panel_audit['status'] == 'PASS_INDEPENDENT_N41_QUOTIENT_SUFFIX_PANEL'
assert panel_audit['source_sha256']['producer'] == sha(HERE / 'n41_panel_result.json')
assert panel_audit['miss_panel_quotient_survivors'] == 8
assert panel_audit['miss_panel_exact_survivors'] == 0
assert n131['status'] == 'PASS_SAMPLED_N131_DEGREE_TWO_EXCLUSION'
assert n131['samples'] == 512 and n131['random_draws'] == 2100
assert n131['feature_rank'] == n131['feature_count'] == 407
assert n131['quotient_dimension'] == 47 and n131['all_labels_contradicted']
assert n131_audit['status'] == 'PASS_INDEPENDENT_N131_ROOTS_AND_DEGREE_TWO_EXCLUSION'
assert n131_audit['root_checks'] == 1024
assert n131_audit['quadratic_feature_rank'] == 407
assert n131_audit['left_nullity'] == 105
assert n131_audit['labels_with_nonzero_syndrome'] == 47
assert n131_audit['source_sha256']['producer'] == sha(HERE / 'n131_result.json')
assert group_audit['status'] == 'PASS_INDEPENDENT_N131_SOURCE_GROUP_BRIDGE'
assert group_audit['sampled_source_codes'] == 512
assert group_audit['pair_output_roots_checked'] == 1024
assert group_audit['source_sha256']['producer'] == sha(HERE / 'n131_result.json')
assert load('n41_interrupted.json')['status'] == 'INTERRUPTED_IMPLEMENTATION_COST'
assert load('n41_panel_audit_preflight.json')['status'] == 'PREFLIGHT_FAILURE'
assert load('n131_group_audit_preflight.json')['status'] == 'INTERRUPTED_IMPLEMENTATION_COST'
lean_source = (HERE / 'QuotientGate.lean').read_text()
lean_out = (HERE / 'lean.stdout').read_text()
assert not (HERE / 'lean.stderr').read_text()
assert all(token not in lean_source for token in ('sorry', 'admit', 'sorryAx', 'axiom '))
assert "'QuotientGate.sound_two_family_filter' does not depend on any axioms" in lean_out
assert "'QuotientGate.finite_feature_separation' depends on axioms: [propext, Classical.choice, Quot.sound]" in lean_out
assert "'QuotientGate.artin_schreier_curve_lift' depends on axioms: [propext, Classical.choice, Quot.sound]" in lean_out
assert (HERE / 'lean-toolchain').read_text().strip() == 'leanprover/lean4:v4.34.1'

artifacts = [
    'protocol.json', 'n41_sage_protocol.json', 'n41_panel_protocol.json',
    'n131_protocol.json', 'n131_sage_protocol.json',
    'n41_result.json', 'n41_panel_result.json', 'n41_audit_result.json',
    'n41_panel_audit_result.json', 'n131_result.json', 'n131_audit_result.json',
    'n131_group_audit_result.json', 'QuotientGate.lean', 'lean.stdout',
    'sage_runtime_info.json', 'RESULT.md', 'PROOF_MAP.md',
]
print(json.dumps({
    'status': 'PASS_TERMINAL_ALIGNED_QUOTIENT_TRANSFER',
    'n41_family_queries': 2485 + 64*2485,
    'n41_panel_quotient_survivors': 8,
    'n131_source_codes': 512,
    'n131_labels_excluded_degree_at_most_two': 47,
    'artifact_sha256': {name: sha(HERE / name) for name in artifacts},
}, sort_keys=True, indent=2))
