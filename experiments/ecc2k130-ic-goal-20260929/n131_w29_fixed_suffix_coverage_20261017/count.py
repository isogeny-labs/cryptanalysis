"""Exact cardinality audit for a W29 two-pair completion oracle."""
import hashlib
import json
from fractions import Fraction
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCES = {
    'n41_source': ROOT / 'n41_n131_w29_rotation_alignment_20261017/aligned_states.json',
    'n131_sample': ROOT / 'n41_n131_aligned_quotient_transfer_20261017/n131_result.json',
    's3_panel': ROOT / 'n41_n131_s3_code_inverse_20261017/result.json',
    'advice_theorem': ROOT / 'n131_target_advice_bound_20261013/AdviceBound.lean',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ceil_div(a, b):
    return (a + b - 1) // b


def ceil_log2(n):
    return (n - 1).bit_length()


protocol = json.loads((HERE / 'protocol.json').read_text())
assert not (HERE / 'result.json').exists()
assert protocol['status'] == 'FROZEN_BEFORE_FIXED_SUFFIX_COUNT'
assert sha(Path(__file__)) == protocol['source_sha256']['script']
for name, path in SOURCES.items():
    assert sha(path) == protocol['source_sha256'][name], name

n41 = json.loads(SOURCES['n41_source'].read_text())
n131 = json.loads(SOURCES['n131_sample'].read_text())
s3 = json.loads(SOURCES['s3_panel'].read_text())
assert n41['curve_id'] == protocol['n41']['curve_id']
assert n41['usable_edges'] == 71 and n41['states_per_slot'] == 284
assert n131['code_bit_width'] == 28 and n131['samples'] == 512
assert s3['curve_id'] == n41['curve_id'] and s3['source_codes'] == 71
assert len(s3['queries']) == 65
assert s3['queries'][0]['exact_group_family_indices'] == [1529]
assert all(not q['exact_group_family_indices'] for q in s3['queries'][1:])

N41 = n41['usable_edges']
N131 = 1 << n131['code_bit_width']
S41 = 4 * N41
S131 = 4 * N131
M41 = 16 * comb(N41, 2)
M131 = 16 * comb(N131, 2)
R41 = protocol['n41']['subgroup_order']
R131 = protocol['n131']['subgroup_order']
K = protocol['hypothetical_fixed_suffixes_per_advice']
assert N41 == 71 and N131 == 268435456
assert R41 == 549756390943
assert R131 == 680564733841876926932320129493409985129
assert K == 600_000_000_000

one = Fraction(M131, R131)
many = Fraction(K * M131, R131)
miss_panel_reference = Fraction(64 * M41, R41)
advice_values_for_half = ceil_div(R131, 2 * K * M131)
result = {
    'status': 'PASS_FIXED_SUFFIX_CARDINALITY_AUDIT',
    'candidate_id': None,
    'model': 'uniform subgroup target; each fixed suffix independent of target within an advice value; exact two-code completion; at most K suffixes per advice value',
    'n41': {
        'curve_id': n41['curve_id'], 'code_count': N41,
        'signed_states_per_slot': S41, 'max_two_code_completions_per_suffix': M41,
        'observed_panel': {'retrospective_relation_suffix_hits': 1,
                           'frozen_miss_suffixes': 64, 'miss_hits': 0},
        'target_independent_64_suffix_reference': {
            'numerator': miss_panel_reference.numerator,
            'denominator': miss_panel_reference.denominator,
        },
    },
    'n131': {
        'curve_id': protocol['n131']['curve_id'],
        'canonical_code_upper_bound': N131,
        'signed_states_per_slot_upper_bound': S131,
        'max_two_code_completions_per_suffix': M131,
        'one_suffix_uniform_coverage_bound': {
            'numerator': one.numerator, 'denominator': one.denominator},
        'hypothetical_suffixes_per_advice': K,
        'hypothetical_uniform_coverage_bound': {
            'numerator': many.numerator, 'denominator': many.denominator},
        'half_coverage_min_target_independent_suffixes': ceil_div(R131, 2 * M131),
        'half_coverage_min_advice_values_at_K': advice_values_for_half,
        'half_coverage_min_advice_bits_at_K': ceil_log2(advice_values_for_half),
        'numerical_certificate': {
            'billion_scaled_numerator': K * M131 * 10**9,
            'denominator': R131,
            'strictly_below_one_billionth': K * M131 * 10**9 < R131,
        },
    },
    'protocol_sha256': sha(HERE / 'protocol.json'),
    'source_sha256': {name: sha(path) for name, path in SOURCES.items()},
}
assert result['n131']['numerical_certificate']['strictly_below_one_billionth']
(HERE / 'result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({'status': result['status'],
                  'n131_pair_bound': M131,
                  'half_coverage_advice_bits': ceil_log2(advice_values_for_half)}))
