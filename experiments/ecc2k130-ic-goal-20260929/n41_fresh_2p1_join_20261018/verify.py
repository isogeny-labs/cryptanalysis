"""Read-only receipt and source-chain check for the fresh N41 relation."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


protocol = read('protocol.json')
audit_protocol = read('audit_protocol.json')
run = read('run_result.json')
audit = read('audit_result.json')
failure = read('attempt1_failure.json')
for cfg in (protocol, audit_protocol):
    for name, item in cfg['sources'].items():
        assert sha(item['path']) == item['sha256'], name
assert protocol['candidate_id'] is None
assert protocol['target_raw_point'] == [1476947961888, 1253336411133]
assert protocol['target_subgroup_point'] == [339942650206, 165641111719]
assert run['protocol_sha256'] == sha(HERE / 'protocol.json')
assert run['stdout_sha256'] == sha(HERE / 'join.stdout')
assert run['stderr_sha256'] == sha(HERE / 'join.stderr')
assert run['status'] == 'HIT_PENDING_SAGE_REPLAY'
assert run['exit_code'] == 0 and run['stop_reason'] is None
assert run['monitor_error'] is None and run['rss_samples'] > 0
assert run['parent_wall_seconds'] < protocol['parent_wall_cap_seconds']
assert run['sampled_peak_combined_rss_bytes'] < protocol['combined_rss_cap_bytes']
assert len(run['hit_lines']) == 1 and not run['miss_lines']
assert 'CHECK_PASS 1420 ' in (HERE / 'join.stdout').read_text()
assert 'LEFT2_DONE 79424 ' in (HERE / 'join.stdout').read_text()
assert 'RIGHT2_DONE 79424 ' in (HERE / 'join.stdout').read_text()
assert audit['status'] == 'PASS_INDEPENDENT_FRESH_N41_RELATION'
assert audit['run_result_sha256'] == sha(HERE / 'run_result.json')
assert audit['audit_protocol_sha256'] == sha(HERE / 'audit_protocol.json')
assert audit['auditor_sha256'] == sha(HERE / 'audit_sage.py')
assert audit['orientation'] == 0 and audit['state_ids'] == [122, 219, 255, 80, 188]
assert audit['raw_public_point'] == protocol['target_raw_point']
assert audit['subgroup_public_point'] == protocol['target_subgroup_point']
assert audit['distinct_folded_columns'] == 10 and audit['scalar_fixture_replay']
assert failure['status'] == 'PRODUCER_ENVIRONMENT_FAILURE'
assert failure['join_worker_started'] is False and failure['exit_code'] == 1
assert failure['protocol_sha256'] == sha(HERE / 'protocol.json')
assert failure['run_sha256'] == sha(HERE / 'run.py')
print('REPLAY_PASS: frozen input, native hit, monitored cap, independent Sage relation')
