"""Read-only terminal binding and independent exact-integer replay."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / 'protocol.json').read_text())
result = json.loads((HERE / 'result.json').read_text())
sources = {
    'script': HERE / 'count.py',
    'n41_source': ROOT / 'n41_n131_w29_rotation_alignment_20261017/aligned_states.json',
    'n131_sample': ROOT / 'n41_n131_aligned_quotient_transfer_20261017/n131_result.json',
    's3_panel': ROOT / 'n41_n131_s3_code_inverse_20261017/result.json',
    'advice_theorem': ROOT / 'n131_target_advice_bound_20261013/AdviceBound.lean',
}
assert all(sha(path) == protocol['source_sha256'][key] for key, path in sources.items())
assert result['source_sha256'] == {key: sha(path) for key, path in sources.items() if key != 'script'}
assert result['protocol_sha256'] == sha(HERE / 'protocol.json')
assert result['status'] == 'PASS_FIXED_SUFFIX_CARDINALITY_AUDIT'
assert result['candidate_id'] is None
assert protocol['n131']['curve_id'] == result['n131']['curve_id']
assert protocol['n41']['curve_id'] == result['n41']['curve_id']

# Independent arithmetic formulation: ordered distinct codes times eight
# counts each unordered code pair with sixteen sign/root choices once.
n = 2**28
m = 8 * n * (n-1)
r = 680564733841876926932320129493409985129
k = 600_000_000_000
assert m == result['n131']['max_two_code_completions_per_suffix']
assert 16 * (71 * 70 // 2) == result['n41']['max_two_code_completions_per_suffix']
assert result['n131']['one_suffix_uniform_coverage_bound'] == {
    'numerator': m, 'denominator': r}
assert result['n131']['hypothetical_uniform_coverage_bound'] == {
    'numerator': k*m, 'denominator': r}
assert result['n131']['half_coverage_min_target_independent_suffixes'] == (r+2*m-1)//(2*m)
need = (r+2*k*m-1)//(2*k*m)
assert need == 983826355
assert result['n131']['half_coverage_min_advice_values_at_K'] == need
assert result['n131']['half_coverage_min_advice_bits_at_K'] == (need-1).bit_length() == 30
assert k*m*10**9 < r
assert result['n131']['numerical_certificate']['billion_scaled_numerator'] == k*m*10**9
assert result['n41']['target_independent_64_suffix_reference'] == {
    'numerator': 64*39760, 'denominator': 549756390943}
assert result['n41']['observed_panel'] == {
    'retrospective_relation_suffix_hits': 1, 'frozen_miss_suffixes': 64,
    'miss_hits': 0}

lean = (HERE / 'Coverage.lean').read_text()
assert all(token not in lean for token in ('sorry', 'admit', 'sorryAx', 'axiom '))
assert (HERE / 'lean-toolchain').read_text().strip() == 'leanprover/lean4:v4.34.1'
axioms = (HERE / 'lean.stdout').read_text()
for theorem in ('successful_targets_le', 'bounded_advice_suffix_success'):
    assert f"'FixedSuffixCoverage.{theorem}' depends on axioms: [propext, Classical.choice, Quot.sound]" in axioms
assert "'FixedSuffixCoverage.reachable_length_le' depends on axioms: [propext, Quot.sound]" in axioms
for theorem in ('n131_pair_bound', 'n131_billion_scaled_bound'):
    assert f"'FixedSuffixCoverage.{theorem}' does not depend on any axioms" in axioms
for name in ('count.stderr', 'lean.stderr'):
    assert not (HERE / name).read_bytes(), name
assert b'PASS_FIXED_SUFFIX_CARDINALITY_AUDIT' in (HERE / 'count.stdout').read_bytes()

artifacts = ['protocol.json', 'count.py', 'result.json', 'Coverage.lean',
             'lean.stdout', 'RESULT.md', 'PROOF_MAP.md']
print(json.dumps({'status': 'PASS_FIXED_SUFFIX_TERMINAL',
                  'artifact_sha256': {name: sha(HERE / name) for name in artifacts}},
                 indent=2, sort_keys=True))
