"""Audit frozen free-code elimination, native census and solver controls."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def read(name):
    return json.loads((HERE / name).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for name in ('protocol.json', 'census_protocol.json',
             'circuit_protocol.json', 'solver_protocol.json', 'model_protocol.json'):
    cfg = read(name)
    for path, digest in cfg['sources'].items():
        assert sha(path) == digest, path
export = read('export_result.json')
assert export['input_sha256'] == sha(HERE / 'resultant_input.tsv')
assert export['target_count'] == 25 and export['source_codes'] == 281
assert export['terms_per_target'] == 13 and export['bidegree'] == [4, 4]
assert len(export['rows']) == 25
assert all(row['symbolic_remainder_verified'] and row['monomial_count'] == 13
           for row in export['rows'])
census = read('census_result.json')
assert read('census_receipt.json')['status'] == 'COMPLETE'
assert census['target_count'] == 25 and census['source_codes'] == 281
assert len(census['rows']) == 25
for index, row in enumerate(census['rows']):
    assert row['index'] == index
    assert row['target_point'] == export['rows'][index]['target_point']
    if index == 0:
        assert row['zero_pairs'] == [[253, 63]]
        assert row['direct_group_hit_code_pairs'] == 1
    else:
        assert row['raw_zero_code_pairs'] == 0
        assert row['direct_group_hit_code_pairs'] == 0
for index in (0, 1):
    circuit = read(f'circuit_{index}_result.json')
    counts = circuit['counts']
    assert counts['and_gates'] == 1781 and counts['variables'] == 2259
    assert counts['clauses'] == 6881 and counts['xor_rows'] == 458
    assert counts['sparse_mul_calls'] == 5 and counts['generic_mul_calls'] == 0
    assert circuit['formula_sha256'] == sha(HERE / ('positive.xcnf' if index == 0 else 'ordinary.xcnf'))
assert read('solver_0_result.json')['status'] == 'SAT_MODEL_UNVERIFIED'
assert read('solver_1_result.json')['status'] == 'UNSAT_UNCERTIFIED'
model = read('model_result.json')
assert model['status'] == 'PASS_N41_W11_FREECODE_SAT_MODEL_AND_GROUP'
assert model['codes'] == [253, 63] and model['exact_group_state_id_hits'] == [[278, 74]]
assert (model['cnf_checked'], model['native_xor_checked']) == (6881, 458)
assert 'sorryAx' not in (HERE / 'lean_check.log').read_text()
receipt = {'status': 'PASS_N41_W11_FREECODE_RESULTANT_EVIDENCE',
           'candidate_id': None,
           'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
           'target_count': 25, 'source_code_pairs_per_target': 281*281,
           'positive_model_and_group_verified': True,
           'ordinary_finite_domain_zero_rows': 24,
           'ordinary_solver_control': 'UNSAT_UNCERTIFIED_WITH_INDEPENDENT_FINITE_DOMAIN_CENSUS',
           'export_sha256': sha(HERE / 'export_result.json'),
           'census_sha256': sha(HERE / 'census_result.json'),
           'model_sha256': sha(HERE / 'model_result.json'),
           'scope': 'frozen hash, symbolic export, all finite code pairs, solver output and independent model replay'}
(HERE / 'verification_result.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
print(json.dumps({'status': receipt['status'], 'target_count': 25}, sort_keys=True))
