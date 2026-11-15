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
    rows = [json.loads(line) for line in (BASE / 'first_seven.jsonl').read_text().splitlines()]
    assert len(rows) == len({row['target_scalar'] for row in rows}) == 7
    assert all(row['status'] == 'timeout' and row['verified_relation_count'] == 0
               for row in rows)
    assert sum(row['query_details']['query_wall_ns'] for row in rows) == 4205138044831
    run = Path(v2['run_dir'])
    live = (run / 'precomputation_attempts.jsonl').read_bytes().splitlines(keepends=True)
    frozen = (BASE / 'first_seven.jsonl').read_bytes().splitlines(keepends=True)
    assert live[:7] == frozen
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
    assert (BASE / 'lean-toolchain').read_text().strip() == 'leanprover/lean4:v4.35.0'
    assert 'Lean (version 4.35.0' in (BASE / 'lean_version.txt').read_text()
    lean_log = (BASE / 'lean_check.stdout.txt').read_text()
    assert "'first_rank_check_needs_1098_productive_queries' does not depend on any axioms" in lean_log
    assert "'prospective_zero_tail_below_five_percent' does not depend on any axioms" in lean_log
    current = json.loads(subprocess.check_output(['python3', str(BASE / 'audit_v2.py')]))
    assert current['protocol_sha256'] == sha(BASE / 'protocol_v2.json')
    print('PASS_PROSPECTIVE_GATE_FROZEN', current['status'],
          current['attempts_completed'])


if __name__ == '__main__':
    main()
