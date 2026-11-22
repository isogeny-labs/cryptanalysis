"""Independently verify zero-yield query archives before a stop recommendation."""

import gzip
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
PROTOCOL = BASE / 'protocol_v4.json'
PREFIX = BASE / 'first_eight.jsonl'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def audit_zero_row(row, run):
    assert row['status'] == 'timeout' and row['verified_relation_count'] == 0
    details = row['query_details']
    assert details['formula_counts'] == {'vars': 232244, 'clauses': 228629,
                                         'xors': 171278}
    assert details['target_scalar_known_to_solver'] is False
    assert details['rss_gate_passed'] is True
    assert details['conservative_combined_peak_rss_bytes'] <= 4 * 1024**3
    assert len(details['attempts']) == 1
    solver = details['attempts'][0]
    assert solver['solver_stop_reason'] == 'parent_timeout'
    assert solver['solver_status'] == 'indeterminate'
    assert solver['solver_exit_code'] == -15
    found = set()
    for artifact in row['archived_solver_artifacts']:
        assert artifact['stored'] is True
        path = Path(artifact['path'])
        assert path.is_file() and path.resolve().is_relative_to(run.resolve())
        packed = path.read_bytes()
        raw = gzip.decompress(packed)
        assert sha(packed) == artifact['compressed_sha256']
        assert len(raw) == artifact['uncompressed_bytes']
        assert sha(raw) == artifact['uncompressed_sha256']
        found.add(path.name)
        if path.name == 'query.xcnf.gz':
            lines = raw.splitlines()
            assert lines[0] == b'p cnf 232244 399907'
            assert len(lines) == 399908
            assert sum(line.startswith(b'x') for line in lines[1:]) == 171278
            assert sha(raw) == details['target_formula_sha256']
        elif path.name == 'cryptominisat.stdout.txt.gz':
            assert b's SATISFIABLE' not in raw
            assert b's UNSATISFIABLE' not in raw
            assert not any(line.startswith(b'v ') for line in raw.splitlines())
    assert found == {'query.xcnf.gz', 'cryptominisat.stdout.txt.gz',
                     'cryptominisat.stderr.txt.gz'}


def main():
    protocol = json.loads(PROTOCOL.read_text())
    old = BASE / 'protocol_v3.json'
    assert protocol['amends_protocol_v3_sha256'] == sha(old.read_bytes())
    assert protocol['source_sha256']['auditor'] == sha(Path(__file__).read_bytes())
    assert protocol['source_sha256']['first_eight'] == sha(PREFIX.read_bytes())
    run = Path(protocol['run_dir'])
    lines = (run / 'precomputation_attempts.jsonl').read_bytes().splitlines(keepends=True)
    frozen = PREFIX.read_bytes().splitlines(keepends=True)
    assert lines[:8] == frozen and len(frozen) == 8
    rows = [json.loads(line) for line in lines]
    assert [row['relation_index'] for row in rows] == list(range(1, len(rows)+1))
    for row in rows[:8]:
        audit_zero_row(row, run)
    in_flight_at_freeze = rows[8] if len(rows) > 8 else None
    if in_flight_at_freeze is not None and in_flight_at_freeze['status'] == 'timeout':
        audit_zero_row(in_flight_at_freeze, run)
    prospective = rows[9:32]
    productive = [row['relation_index'] for row in prospective
                  if row['verified_relation_count'] > 0]
    non_timeout = [row['relation_index'] for row in prospective
                   if row['verified_relation_count'] == 0 and row['status'] != 'timeout']
    checked_zero = []
    for row in prospective:
        if row['verified_relation_count'] == 0 and row['status'] == 'timeout':
            audit_zero_row(row, run)
            checked_zero.append(row['relation_index'])
    if (run / 'result.json').exists() and len(rows) < 32:
        status = 'TERMINAL_BEFORE_PROSPECTIVE_GATE'
    elif in_flight_at_freeze is not None and in_flight_at_freeze['verified_relation_count'] > 0:
        status = 'CONTINUE_INFLIGHT_QUERY_PRODUCTIVE'
    elif in_flight_at_freeze is not None and in_flight_at_freeze['status'] != 'timeout':
        status = 'INELIGIBLE_INFLIGHT_QUERY_FAILURE'
    elif productive:
        status = 'CONTINUE_PRODUCTIVE_QUERY_OBSERVED'
    elif non_timeout:
        status = 'INELIGIBLE_NON_TIMEOUT_ZERO_ROW'
    elif len(prospective) < 23:
        status = 'PENDING_PROSPECTIVE_QUERIES'
    else:
        assert checked_zero == list(range(10, 33))
        status = 'RECOMMEND_STOP_AFTER_AUDITED_ZERO_YIELD_PANEL'
    result = {
        'kind': 'n131_d13_m12_prospective_precompute_yield_gate_v4',
        'status': status,
        'candidate_id': protocol['candidate_id'], 'run_id': protocol['run_id'],
        'protocol_sha256': sha(PROTOCOL.read_bytes()),
        'attempts_completed': len(rows),
        'excluded_inflight_query_index': 9,
        'excluded_inflight_query_status':
            in_flight_at_freeze['status'] if in_flight_at_freeze is not None else None,
        'prospective_attempts_completed': len(prospective),
        'productive_indices': productive, 'non_timeout_zero_indices': non_timeout,
        'independently_audited_zero_indices': checked_zero,
        'live_attempts_sha256': sha((run / 'precomputation_attempts.jsonl').read_bytes()),
    }
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
