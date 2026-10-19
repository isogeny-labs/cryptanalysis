"""Audit joint family-intersection proofs, source locks, and run receipts."""
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


protocols = ('protocol.json', 'bsgs_protocol.json', 'sparse_protocol.json',
             'special_prepare_protocol.json', 'special_protocol.json',
             'sparse_special_protocol.json',
             'zero_second_prepare_protocol.json', 'zero_second_protocol.json')
source_count = 0
for name in protocols:
    item = read(name)
    assert item['candidate_id'] is None
    for path, expected in item['sources'].items():
        assert sha(path) == expected, (name, path)
        source_count += 1
failure = read('first_attempt_failure.json')
assert failure['status'] == 'PRODUCER_FAILURE_JSON_SERIALIZATION'
assert failure['query_rows_written'] == 0
assert failure['protocol_sha256'] == sha(HERE / 'protocol_v1.json')
assert failure['script_sha256'] == sha(HERE / 'run_joint_v1.py')
assert read('protocol_v1.json')['sources'][str(HERE / 'run_joint.py')] == sha(HERE / 'run_joint_v1.py')
keys = json.loads(Path(read('protocol.json')['keys']).read_text())['keys']
original = read('result.json')
blocked = read('bsgs_result.json')
sparse = read('sparse_result.json')
special_keys = read('special_keys.json')
special = read('special_result.json')
sparse_special = read('sparse_special_result.json')
zero_keys = read('zero_second_keys.json')
zero = read('zero_second_result.json')
assert len(keys) == 8
assert original['first_x_count'] == original['second_x_count'] == 142
assert original['first_polynomial_sha256'] == blocked['first_polynomial_sha256'] == special['first_polynomial_sha256']
assert original['second_polynomial_sha256'] == blocked['second_polynomial_sha256'] == special['second_polynomial_sha256']
assert blocked['composition_block_size'] == special['composition_block_size'] == 12
assert sparse['annihilator_terms'] == sparse_special['annihilator_terms'] == zero['annihilator_terms'] == 9
assert sparse['annihilator_sha256'] == sparse_special['annihilator_sha256'] == zero['annihilator_sha256']
for panel in (original, blocked, sparse):
    assert len(panel['rows']) == len(keys)
    for key, row in zip(keys, panel['rows']):
        assert row['key_id'] == key['key_id']
        assert row['status'] == 'PASS_EXACT_KEY_AGREEMENT'
        assert row['oracle_member'] == row['exact_member'] == key['exact_member']
        assert row['norm_gcd_degree'] == (1 if key['exact_member'] else 0)
        assert row['first_state_group_subtractions'] <= 2
assert all(row['zero_second_x_gcd_degree'] == 0 for row in sparse['rows'])
assert special_keys['status'] == 'PASS_N41_SPECIAL_X_KEY_CENSUS'
assert len(special['rows']) == 1
edge = special['rows'][0]
assert edge['status'] == 'PASS_EXACT_KEY_AGREEMENT'
assert edge['special_first_x'] == 1 and edge['norm_gcd_degree'] == 0
assert edge['oracle_member'] == edge['exact_member'] == special_keys['keys'][0]['exact_member'] == False
assert edge['first_state_group_subtractions'] == 2
assert sparse_special['rows'][0]['special_first_x'] == 1
assert sparse_special['rows'][0]['oracle_member'] == False
assert zero_keys['status'] == 'PASS_N41_ZERO_SECOND_X_KEY_CENSUS'
assert zero_keys['keys'][0]['exact_member'] == False
assert zero['rows'][0]['zero_second_x_gcd_degree'] == 1
assert zero['rows'][0]['oracle_member'] == False
lean = (HERE / 'lean.stdout').read_text()
for theorem in ('norm_identity', 'norm_zero_iff_branch'):
    assert f"'QuadraticNorm.{theorem}' depends on axioms: [propext, Classical.choice, Quot.sound]" in lean
assert not (HERE / 'lean.stderr').read_text()
assert re.search(r'\b(?:sorry|admit|sorryAx)\b',
                 (HERE / 'QuadraticNorm.lean').read_text()) is None
annihilator_lean = (HERE / 'annihilator_lean.stdout').read_text()
assert "'LinearizedAnnihilator.extend_kernel_iff' depends on axioms: [propext, Classical.choice, Quot.sound]" in annihilator_lean
assert not (HERE / 'annihilator_lean.stderr').read_text()
assert re.search(r'\b(?:sorry|admit|sorryAx)\b',
                 (HERE / 'LinearizedAnnihilator.lean').read_text()) is None
result = {'status': 'PASS_N41_JOINT_NORM_GCD_TERMINAL_AUDIT',
          'candidate_id': None, 'protocols_verified': len(protocols),
          'source_hashes_verified': source_count,
          'ordinary_keys_verified_in_each_arm': len(keys),
          'special_keys_verified': len(special['rows']) + len(zero['rows']),
          'first_attempt_status': failure['status'],
          'script_sha256': sha(__file__)}
(HERE / 'terminal_audit.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
