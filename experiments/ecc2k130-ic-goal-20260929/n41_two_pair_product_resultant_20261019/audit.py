"""Audit frozen N41 resultant receipts after archival relocation."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIGINAL = Path('/private/tmp/n41_two_pair_product_resultant_20261019')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_path(value):
    path = Path(value)
    if path == ORIGINAL or ORIGINAL in path.parents:
        return HERE / path.relative_to(ORIGINAL)
    return path


protocols = {}
checked = 0
for path in sorted(HERE.glob('*protocol.json')):
    row = json.loads(path.read_text())
    assert row['candidate_id'] is None, path
    for name, expected in row['sources'].items():
        source = local_path(name)
        assert source.is_file(), source
        assert sha(source) == expected, source
        checked += 1
    protocols[path.name] = sha(path)

results = {}
for path in sorted(HERE.glob('*result.json')):
    if path.name == 'audit_result.json':
        continue
    row = json.loads(path.read_text())
    assert row['candidate_id'] is None, path
    protocol_name = path.name.replace('_result.json', '_protocol.json')
    if protocol_name == 'resultant_protocol.json':
        protocol_name = 'derive_protocol.json'
    if protocol_name == 'holdout_retry_protocol.json':
        pass
    if protocol_name == 'holdout_verify_protocol.json':
        pass
    assert row['protocol_sha256'] == protocols[protocol_name], path
    results[path.name] = row['status']

for key in ('H0', 'H1', 'H2', 'H3'):
    assert f'{key}_resultant.stdout' in [p.name for p in HERE.iterdir()]
for key in ('H4', 'H5', 'H6', 'H7'):
    assert (HERE / f'{key}_resultant_retry.stdout').is_file()

retry = json.loads((HERE / 'holdout_retry_result.json').read_text())
assert len(retry['rows']) == 4
for row in retry['rows']:
    key = row['key_id']
    assert row['status'] == 'UNSAT_UNCERTIFIED'
    assert sha(HERE / f'{key}_resultant_retry.stdout') == row['stdout_sha256']
    assert sha(HERE / f'{key}_resultant_retry.stderr') == row['stderr_sha256']

for prefix in ('sat_build', 'holdout_build'):
    build = json.loads((HERE / f'{prefix}_result.json').read_text())
    for row in build['rows']:
        assert sha(HERE / f"{row['key_id']}_resultant.xcnf") == row['formula_sha256']
for prefix in ('sat_query',):
    query = json.loads((HERE / f'{prefix}_result.json').read_text())
    for row in query['rows']:
        key = row['key_id']
        assert sha(HERE / f'{key}_resultant.stdout') == row['stdout_sha256']
        assert sha(HERE / f'{key}_resultant.stderr') == row['stderr_sha256']
replay = json.loads((HERE / 'holdout_replay_result.json').read_text())
verify = json.loads((HERE / 'holdout_verify_result.json').read_text())
assert len(replay['rows']) == 4 and len(verify['rows']) == 8
assert all(r['witnesses'] for r in replay['rows'])
assert [r['resultant_zero_code_pairs'] for r in verify['rows']] == [1]*4+[0]*4
assert all(r['admissible_code_pairs'] == 4964 for r in verify['rows'])
assert all(r['verified_member'] == r['exact_member'] for r in verify['rows'])

failure = json.loads((HERE / 'holdout_first_attempt_failure.json').read_text())
assert failure['status'] == 'PRODUCER_FAILURE_DISK_ENOSPC'
assert failure['completed_prefix'][-1]['key_id'] == 'H4'
assert failure['completed_prefix'][-1]['status'] == 'PRODUCER_FAILURE_NO_TERMINAL_STATUS'
assert sha(HERE / 'query_holdout_sat.py') == failure['script_sha256']
assert protocols['holdout_query_protocol.json'] == failure['query_protocol_sha256']
for row in failure['completed_prefix']:
    key = row['key_id']
    assert sha(HERE / f'{key}_resultant.stdout') == failure['stdout_sha256'][key]

lean = (HERE / 'lean.stdout').read_text()
assert "depends on axioms: [propext, Classical.choice, Quot.sound]" in lean
assert (HERE / 'lean.stderr').read_text() == ''

summary = {'status':'PASS_ARCHIVED_N41_RESULTANT_AUDIT',
           'protocols':protocols, 'source_hashes_checked':checked,
           'results':results, 'holdout_code_pairs_per_key':4964,
           'lean_axioms':['propext','Classical.choice','Quot.sound']}
(HERE / 'audit_result.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':summary['status'],'protocol_count':len(protocols),
                  'source_hashes_checked':checked,'result_count':len(results)}))
