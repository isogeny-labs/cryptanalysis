"""Read-only audit of frozen quartic-root controls and N131 panel."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


cfg = read('protocol.json')
for name, expected in cfg['sources'].items():
    path = Path(name)
    if not path.is_absolute():
        path = WORKSPACE / path
    assert sha(path) == expected, name
gate = read('n131_gate.json')
assert gate['status'] == 'FROZEN_N131_AFTER_N41_CONTROL'
for name, expected in gate['sources'].items():
    path = Path(name)
    if not path.is_absolute():
        path = WORKSPACE / path
    assert sha(path) == expected, name

for mode, query_count in (('n41_smoke', 1), ('n41', 562), ('n131', 150)):
    row = read(mode+'_result.json')
    run = read(mode+'_run_result.json')
    assert run['status'] == 'COMPLETE' and run['stop_reason'] is None
    assert run['candidate_id'] is None and row['candidate_id'] is None
    assert run['protocol_sha256'] == row['protocol_sha256'] == sha(HERE / 'protocol.json')
    assert run['stdout_sha256'] == sha(HERE / (mode+'.stdout'))
    assert run['stderr_sha256'] == sha(HERE / (mode+'.stderr'))
    assert run['sampled_peak_combined_rss_bytes'] < cfg['rss_cap_bytes']
    assert row['summary']['queries'] == len(row['rows']) == query_count
    assert row['summary']['field_roots_total'] == 4*query_count
    assert all(entry['quartic_degree'] == 4 and entry['field_roots'] == 4
               for entry in row['rows'])
    if mode == 'n41_smoke':
        assert row['matching_zero_pairs'] == {'0': [[253, 63]]}
    elif mode == 'n41':
        assert row['matching_zero_pairs'] == {'0': [[253, 63]], '1': []}
        assert row['source_codes_per_target'] == 281
    else:
        assert row['proposed_first_codes'] == 257
        assert row['valid_first_codes'] == 75
        assert row['positive_second_codes'] == [16722]
        assert [(entry['first_code'], hit['second_code']) for entry in row['rows']
                if entry['target_index'] == 1 for hit in entry['span_root_hits']] == []

assert read('runtime_attempt0.json')['sage_process_started'] is False
print(json.dumps({'status': 'PASS_QUARTIC_ROOT_FROZEN_AUDIT',
                  'n41_queries': 562, 'n131_queries': 150,
                  'n131_positive_codes': [3, 16722]}, sort_keys=True))
