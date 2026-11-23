"""Read-only replay of the frozen prospective stopping protocol."""

import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((BASE / name).read_text())


def main():
    v1 = read('protocol.json')
    v2 = read('protocol_v2.json')
    v3 = read('protocol_v3.json')
    v4 = read('protocol_v4.json')
    assert v2['amends_protocol_sha256'] == sha(BASE / 'protocol.json')
    assert v2['source_sha256'] == {
        'auditor': sha(BASE / 'audit_v2.py'),
        'first_seven': sha(BASE / 'first_seven.jsonl'),
        'lean_arithmetic': sha(BASE / 'FutilityArithmetic.lean'),
        'freeze_v2': sha(BASE / 'freeze_v2.py')}
    assert v1['first_seven_sha256'] == sha(BASE / 'first_seven.jsonl')
    assert v1['audit_source_sha256'] == sha(BASE / 'audit.py')
    assert v1['lean_source_sha256'] == sha(BASE / 'FutilityArithmetic.lean')
    assert v1['freeze_source_sha256'] == sha(BASE / 'freeze.py')
    assert v1['prospective_attempt_indices'] == v2['prospective_attempt_indices'] == [8, 30]
    assert v1['run_id'] == v2['run_id']
    assert v3['amends_protocol_v2_sha256'] == sha(BASE / 'protocol_v2.json')
    assert v3['source_sha256']['auditor'] == sha(BASE / 'audit_v3.py')
    assert v3['source_sha256']['first_eight'] == sha(BASE / 'first_eight.jsonl')
    assert v4['amends_protocol_v3_sha256'] == sha(BASE / 'protocol_v3.json')
    assert v4['source_sha256'] == {
        'auditor': sha(BASE / 'audit_v4.py'),
        'first_eight': sha(BASE / 'first_eight.jsonl'),
        'lean_arithmetic': sha(BASE / 'FutilityArithmetic.lean'),
        'freeze_v4': sha(BASE / 'freeze_v4.py'),
        'v3_failure': sha(BASE / 'audit_v3_failure.json')}
    assert v4['prospective_attempt_indices'] == [10, 32]
    assert v4['excluded_inflight_query_index'] == 9
    assert v4['run_id'] == v1['run_id']
    rows = [json.loads(line) for line in (BASE / 'first_seven.jsonl').read_text().splitlines()]
    assert len(rows) == len({row['target_scalar'] for row in rows}) == 7
    assert all(row['status'] == 'timeout' and row['verified_relation_count'] == 0
               for row in rows)
    assert sum(row['query_details']['query_wall_ns'] for row in rows) == 4205138044831
    run = Path(v4['run_dir'])
    live = (run / 'precomputation_attempts.jsonl').read_bytes().splitlines(keepends=True)
    frozen = (BASE / 'first_seven.jsonl').read_bytes().splitlines(keepends=True)
    assert live[:7] == frozen
    frozen_eight = (BASE / 'first_eight.jsonl').read_bytes().splitlines(keepends=True)
    assert live[:8] == frozen_eight
    if len(live) >= 8:
        row8 = json.loads(live[7])
        assert datetime.fromisoformat(v2['frozen_utc']) < datetime.fromisoformat(
            row8['completed_utc'])
    initial = read('freeze_audit_v2.json')
    assert initial['status'] == 'PENDING_PROSPECTIVE_QUERIES'
    assert initial['attempts_completed'] == 7
    assert initial['protocol_sha256'] == sha(BASE / 'protocol_v2.json')
    assert initial['live_attempts_sha256'] == sha(BASE / 'first_seven.jsonl')
    first_prospective = read('first_prospective_audit.json')
    assert first_prospective['status'] == 'PENDING_PROSPECTIVE_QUERIES'
    assert first_prospective['attempts_completed'] == 8
    assert first_prospective['independently_audited_zero_indices'] == [8]
    assert first_prospective['live_attempts_sha256'] == \
        hashlib.sha256(b''.join(live[:8])).hexdigest()
    failure = read('audit_v3_failure.json')
    assert failure['status'] == 'AUDITOR_KEY_ERROR_BEFORE_PANEL'
    initial_v4 = read('freeze_audit_v4.json')
    assert initial_v4['status'] == 'PENDING_PROSPECTIVE_QUERIES'
    assert initial_v4['attempts_completed'] == 8
    assert initial_v4['excluded_inflight_query_index'] == 9
    assert initial_v4['protocol_sha256'] == sha(BASE / 'protocol_v4.json')
    assert initial_v4['live_attempts_sha256'] == sha(BASE / 'first_eight.jsonl')
    if len(live) >= 10:
        row10 = json.loads(live[9])
        assert datetime.fromisoformat(v4['frozen_utc']) < datetime.fromisoformat(
            row10['query_details']['attempts'][0]['solver_process_start_utc'])
    assert (BASE / 'lean-toolchain').read_text().strip() == 'leanprover/lean4:v4.35.0'
    assert 'Lean (version 4.35.0' in (BASE / 'lean_version.txt').read_text()
    lean_log = (BASE / 'lean_check.stdout.txt').read_text()
    assert "'first_rank_check_needs_1098_productive_queries' does not depend on any axioms" in lean_log
    assert "'prospective_zero_tail_below_five_percent' does not depend on any axioms" in lean_log
    current = json.loads(subprocess.check_output(['python3', str(BASE / 'audit_v4.py')]))
    assert current['protocol_sha256'] == sha(BASE / 'protocol_v4.json')
    print('PASS_PROSPECTIVE_GATE_FROZEN', current['status'],
          current['attempts_completed'])


if __name__ == '__main__':
    main()
