"""Audit frozen source, formula, solver, Lean, and certificate receipts."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((here / name).read_text())


for name in ('build_protocol.json', 'query_protocol.json',
             'sparse_build_protocol.json', 'sparse_query_protocol.json'):
    protocol = read(name)
    for path, expected in protocol['sources'].items():
        assert sha(path) == expected, (name, path)

for stem in ('', 'sparse_'):
    build = read(stem + 'build_result.json')
    query = read(stem + 'query_result.json')
    formula = here / (stem + 'formula.xcnf')
    assert build['formula_sha256'] == sha(formula)
    assert build['protocol_sha256'] == sha(here / (stem + 'build_protocol.json'))
    assert query['protocol_sha256'] == sha(here / (stem + 'query_protocol.json'))
    assert query['solver_stdout_sha256'] == sha(here / (stem + 'solver.stdout'))
    assert query['solver_stderr_sha256'] == sha(here / (stem + 'solver.stderr'))
    assert query['candidate_id'] is None and build['candidate_id'] is None
    assert query['worker_count'] == 1
    assert query['sampled_peak_combined_rss_bytes'] <= 4294967296

assert read('query_result.json')['status'] == 'BOUNDED_UNKNOWN'
assert read('query_result.json')['stop_reason'] == 'WALL_CAP'
assert read('sparse_query_result.json')['status'] == 'UNSAT_UNCERTIFIED'
assert read('sparse_query_result.json')['solver_terminal_unsat']
assert read('sparse_build_result.json')['and_gates'] == 784
assert read('build_result.json')['and_gates'] == 4751

for name in ('rank_result.json', 'enumeration_result.json'):
    for path, expected in read(name)['sources'].items():
        assert sha(path) == expected, (name, path)
assert read('verification_result.json')['source_result_sha256'] == sha(here / 'enumeration_result.json')
assert read('linear_certificate_sage_replay.json')['certificate_sha256'] == sha(here / 'linear_certificate.json')
assert read('linear_certificate.json')['source_sha256'] == sha(here / 'linear_certificate.py')
assert read('linear_certificate.json')['parity_mask'] == 1
assert read('linear_certificate_sage_replay.json')['status'] == 'PASS_SAGE_GF2_131_CONSTANT_COEFFICIENT_CERTIFICATE'
assert read('verification_result.json')['status'] == 'PASS_INDEPENDENT_PURE_PYTHON_REPLAY'
assert (here / 'lean_exit_code.txt').read_text().strip() == '0'
lean_log = (here / 'lean_check.log').read_text()
assert lean_log.count('depends on axioms:') == 7
assert 'sorryAx' not in lean_log and 'error:' not in lean_log

receipt = {
    'status': 'PASS_FROZEN_RECEIPT_AUDIT',
    'candidate_id': None,
    'curve_id': 'EC1N131Ckb1heb5f1998f20b',
    'direct_query_status': 'BOUNDED_UNKNOWN',
    'sparse_query_status': 'UNSAT_UNCERTIFIED',
    'linear_certificate_status': 'PASS_SAGE_GF2_131_CONSTANT_COEFFICIENT_CERTIFICATE',
    'independent_enumeration_status': 'PASS_INDEPENDENT_PURE_PYTHON_REPLAY',
    'lean_module_sha256': sha(here / 'PairException.lean'),
    'proof_log_sha256': sha(here / 'lean_check.log'),
}
(here / 'receipt_audit.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
print(json.dumps(receipt, sort_keys=True))
