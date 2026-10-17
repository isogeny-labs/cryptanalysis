"""Read-only audit of both matched-conflict topology orders and terminal race."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


first = json.loads((HERE / 'topology_result.json').read_text())
second = json.loads((HERE / 'topology_repeat_result.json').read_text())
assert first['status'] == 'COMPLETE_TOPOLOGY_CONFLICT_SCREEN'
assert second['status'] == 'COMPLETE_REVERSE_ORDER_TOPOLOGY_SCREEN'
assert first['protocol_sha256'] == sha(HERE / 'topology_protocol.json')
assert second['protocol_sha256'] == sha(HERE / 'topology_repeat_protocol.json')
rows = []
for prefix, result in (('topology', first), ('topology_repeat', second)):
    for row in result['rows']:
        name = row['arm']
        stdout_path = HERE / f'{prefix}_{name}.stdout'
        stderr_path = HERE / f'{prefix}_{name}.stderr'
        assert sha(stdout_path) == row['stdout_sha256']
        assert sha(stderr_path) == row['stderr_sha256']
        assert not stderr_path.read_bytes()
        lines = stdout_path.read_text().splitlines()
        assert row['exit_code'] == 0
        assert row['status_lines'] == ['s INDETERMINATE']
        assert sum(line.startswith('c rst') for line in lines) == row['restart_count'] == 336
        conflicts = [int(line.split(':', 1)[1].split()[0]) for line in lines
                     if line.startswith('c conflicts                :')]
        assert conflicts and len(set(conflicts)) == 1
        assert conflicts[0] == (100001 if name == 'three_plus_two' else 100002)
        assert row['formula_sha256'] == sha(HERE / ('n131_3p2.xcnf' if name == 'three_plus_two'
                                                 else 'n131_ordinary.xcnf'))
        classification = ('COMPLETE_WITH_TERMINAL_POLL_RACE'
                          if row['stop_reason'] == 'MONITOR_FAILURE' else 'COMPLETE')
        assert row['stop_reason'] in (None, 'MONITOR_FAILURE')
        rows.append({'order': prefix, 'arm': name, 'classification': classification,
                     'elapsed_ns': row['elapsed_ns'],
                     'conflicts': conflicts[0], 'restart_count': 336,
                     'sampled_peak_combined_rss_bytes': row['sampled_peak_combined_rss_bytes']})
assert len(rows) == 4
result = {'status': 'PASS_TOPOLOGY_TERMINAL_AUDIT', 'rows': rows,
          'first_result_sha256': sha(HERE / 'topology_result.json'),
          'repeat_result_sha256': sha(HERE / 'topology_repeat_result.json'),
          'auditor_sha256': sha(Path(__file__))}
with (HERE / 'topology_audit_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps(result, sort_keys=True))
