"""Read-only verification of the frozen target-conditioned N41 join."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


def main():
    protocol = load('protocol.json')
    audit_protocol = load('audit_protocol.json')
    result = load('run_result.json')
    audit = load('audit_result.json')
    assert protocol['status'] == 'FROZEN_BEFORE_PUBLIC_JOIN'
    assert protocol['candidate_id'] is None
    assert protocol['worker_count'] == 1
    assert protocol['parent_wall_cap_seconds'] == 600
    assert protocol['combined_rss_cap_bytes'] == 4 * 1024**3
    for row in (protocol, audit_protocol):
        for name, expected in row['source_sha256'].items():
            path = Path(name)
            if not path.is_absolute():
                path = ROOT / path
            assert sha(path) == expected, name
    assert result['status'] == 'HIT_PENDING_SAGE_REPLAY'
    assert result['protocol_sha256'] == sha(HERE / 'protocol.json')
    assert result['exit_code'] == 0 and result['stop_reason'] is None
    assert result['monitor_error'] is None
    assert result['parent_wall_seconds'] < protocol['parent_wall_cap_seconds']
    assert result['sampled_peak_combined_rss_bytes'] < protocol['combined_rss_cap_bytes']
    assert result['stdout_sha256'] == sha(HERE / 'join.stdout')
    assert result['stderr_sha256'] == sha(HERE / 'join.stderr')
    assert not (HERE / 'join.stderr').read_bytes()
    lines = (HERE / 'join.stdout').read_text().splitlines()
    assert [line for line in lines if line.startswith('HIT ')] == result['hit_lines']
    assert [line for line in lines if line.startswith('LEFT2_DONE ')] == result['left2_done_lines']
    assert [line for line in lines if line.startswith('RIGHT2_DONE ')] == result['right2_done_lines']
    assert [line for line in lines if line.startswith('ORIENTATION_DONE ')] == result['orientation_done_lines']
    assert len(result['left2_done_lines']) == len(result['right2_done_lines']) == 1
    assert int(result['left2_done_lines'][0].split()[1]) == 79424
    assert int(result['right2_done_lines'][0].split()[1]) == 79424
    hit = result['hit_lines'][0].split()
    assert len(hit) == 11 and hit[0] == 'HIT'
    assert int(hit[1]) == audit['orientation'] == 3
    assert list(map(int, hit[2:7])) == audit['state_ids']
    assert [int(row.split()[1]) for row in result['orientation_done_lines']] == [0, 1, 2]
    assert audit['status'] == 'PASS_INDEPENDENT_N41_2P1_PUBLIC_RELATION'
    assert audit['distinct_folded_columns'] == 10
    assert audit['raw_public_point'] == protocol['target_raw_point']
    assert audit['run_result_sha256'] == sha(HERE / 'run_result.json')
    assert audit['audit_protocol_sha256'] == sha(HERE / 'audit_protocol.json')
    assert audit['auditor_sha256'] == sha(HERE / 'audit_sage.py')
    assert "does not depend on any axioms" in (HERE / 'lean.stdout').read_text()
    assert not (HERE / 'lean.stderr').read_bytes()
    print(json.dumps({'status': 'PASS_N41_2P1_FROZEN_JOIN',
                      'public_point': audit['raw_public_point'],
                      'state_ids': audit['state_ids'],
                      'index_entries_per_side': 79424,
                      'parent_wall_seconds': result['parent_wall_seconds'],
                      'sampled_peak_combined_rss_bytes':
                      result['sampled_peak_combined_rss_bytes']}, sort_keys=True))


if __name__ == '__main__':
    main()
