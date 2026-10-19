"""Audit frozen N41 resultant, field baseline, N131 control, and Lean proof."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / 'verification_protocol.json').read_text())
assert protocol['status'] == 'FROZEN_BEFORE_PAIR_RESULTANT_TERMINAL_AUDIT'
assert protocol['script_sha256'] == sha(Path(__file__))
for path, digest in protocol['sources'].items():
    assert sha(path) == digest, path
for name in ('protocol.json', 'field_compare_protocol.json', 'audit_protocol.json'):
    nested = json.loads((HERE / name).read_text())
    for path, digest in nested['sources'].items():
        assert sha(path) == digest, (name, path)

producer = json.loads((HERE / 'result.json').read_text())
comparison = json.loads((HERE / 'field_compare_result.json').read_text())
audit = json.loads((HERE / 'audit_result.json').read_text())
assert producer['status'] == 'PASS_EXHAUSTIVE_N41_PAIR_RESULTANT_EQUIVALENCE'
assert comparison['status'] == 'PASS_EXHAUSTIVE_N41_FIELD_BASELINE_COMPARISON'
assert audit['status'] == 'PASS_INDEPENDENT_PAIR_RESULTANT_AUDIT'
assert producer['candidate_id'] is comparison['candidate_id'] is audit['candidate_id'] is None
assert producer['code_pairs'] == comparison['code_pairs'] == audit['n41_code_pairs_checked'] == 39335
assert producer['filter_hits'] == producer['baseline_hits'] == \
       producer['exact_group_hits'] == comparison['accepted_pairs'] == \
       audit['n41_zero_pairs'] == [[425, 527]]
assert audit['n131_rotated_quadratics_verified'] == 2
assert audit['n131_constructed_resultant_zero']
assert comparison['order'] == ['resultant', 'four_roots', 'four_roots', 'resultant']
assert len(comparison['runs']) == 4
assert all(row['accepted_code_pairs'] == 1 for row in comparison['runs'])
proof = (HERE / 'lean.stdout').read_text()
for name in ('f3_eq_bilinear', 'bilinear_norm_eq_four_roots',
             'resultant_eq_four_f3', 'resultant_zero_iff_four_f3',
             'fixed_seed_pair_resultant_zero'):
    assert ("'PairResultant." + name +
            "' depends on axioms: [propext, Classical.choice, Quot.sound]") in proof
assert not (HERE / 'lean.stderr').read_bytes()
source = (HERE / 'PairResultant.lean').read_text()
assert not any(word in source for word in ('sorryAx', 'admit', 'sorry'))
result = {
    'status': 'PASS_PAIR_RESULTANT_TERMINAL_AUDIT', 'candidate_id': None,
    'n41_complete_code_pairs': 39335, 'n41_accepted_pair': [425, 527],
    'exact_norm_product_catalog_verified': True,
    'n131_constructed_positive_verified': True,
    'lean_proof_axioms': ['propext', 'Classical.choice', 'Quot.sound'],
    'protocol_sha256': sha(HERE / 'verification_protocol.json'),
}
(HERE / 'terminal_audit.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
