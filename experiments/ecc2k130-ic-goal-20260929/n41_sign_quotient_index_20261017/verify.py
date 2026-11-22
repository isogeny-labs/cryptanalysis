"""Read-only integrity and status check for the sign-quotient experiment."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
t = json.loads((D / 'terminal.json').read_text())
for path, digest in t['files'].items():
    assert sha(D / path) == digest, path
p = json.loads((D / 'protocol.json').read_text())
r = json.loads((D / 'run_result.json').read_text())
b = json.loads((D / 'bench_result.json').read_text())
a = json.loads((D / 'audit_result.json').read_text())
assert p['candidate_id'] is None and p['worker_count'] == 1
assert sha(Path(p['input_path'])) == p['input_sha256'] == t['source_input_sha256']
assert sha(D / 'sign_join.cpp') == p['source_sha256']
assert sha(D / 'run.py') == p['runner_sha256']
assert sha(D.parent / 'n41_sixpair_shared_target_20261017' / 'join_exact.cpp') == p['included_source_sha256']
assert r['status'] == 'HIT_PENDING_INDEPENDENT_REPLAY' and r['stop_reason'] is None
assert a['status'] == 'PASS_INDEPENDENT_N41_SIXPAIR_PUBLIC_RELATION'
assert a['raw_target'] == p['public_raw_target'] and a['distinct_columns'] == 12
assert b['bench_source_sha256'] == sha(D / 'bench.py')
assert [x['variant'] for x in b['rows']] == ['sorted', 'sign', 'sign', 'sorted']
for row in b['rows']:
    i, v = row['order'], row['variant']
    assert row['exit_code'] == 0
    assert sha(D / f'bench_{i}_{v}.stdout') == row['stdout_sha256']
    assert sha(D / f'bench_{i}_{v}.stderr') == row['stderr_sha256']
    assert [int(x) for x in row['hit_line'].split()[1:7]] == [12, 122, 116, 47, 128, 34]
assert not b['rows'][0]['monitor_degraded'] and not b['rows'][1]['monitor_degraded']
assert 'lookupEitherSign' in (D / 'lean.stdout').read_text()
print('PASS sign quotient integrity, independent replay receipt, paired runs, Lean receipt')
