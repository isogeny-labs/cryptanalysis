"""Freeze the prospective zero-yield panel after the first seven attempts."""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
RUN = Path('/Volumes/SSD990-2/ecc2k130-ic-runstore/d13-m12-20261115/IC1N131Ckb1fb1083108PDP12satRCdirectLAgaussTDdirectISO0h195ae7ea5e75W3c1992b7c92fR1')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    prefix = BASE / 'first_seven.jsonl'
    live = RUN / 'precomputation_attempts.jsonl'
    frozen_lines = prefix.read_bytes().splitlines(keepends=True)
    live_lines = live.read_bytes().splitlines(keepends=True)
    assert len(frozen_lines) == len(live_lines) == 7
    assert frozen_lines == live_lines
    rows = [json.loads(line) for line in live_lines]
    assert [row['relation_index'] for row in rows] == list(range(1, 8))
    assert all(row['status'] == 'timeout' and row['verified_relation_count'] == 0
               for row in rows)
    progress = json.loads((RUN / 'precompute_progress.json').read_text())
    assert progress['status'] == 'RUNNING' and progress['attempts_completed'] == 7
    assert progress['verified_relations'] == progress['rank'] == 0
    assert not (RUN / 'result.json').exists()
    os.kill(53627, 0)
    record = {
        'kind': 'n131_d13_m12_prospective_precompute_futility_protocol_v1',
        'status': 'FROZEN_AFTER_SEVEN',
        'frozen_utc': datetime.now(timezone.utc).isoformat(),
        'curve_id': 'EC1N131Ckb1heb5f1998f20b',
        'candidate_id': 'IC1N131Ckb1fb1083108PDP12satRCdirectLAgaussTDdirectISO0h195ae7ea5e75',
        'workload_id': '3c1992b7c92f',
        'run_id': RUN.name,
        'run_dir': str(RUN),
        'observed_prefix_attempt_count': 7,
        'observed_prefix_verified_rows': 0,
        'prospective_attempt_indices': [8, 30],
        'prospective_sample_size': 23,
        'productive_definition': 'verified_relation_count >= 1 in a completed preparation query',
        'decision_if_any_productive': 'continue frozen run',
        'decision_if_zero_productive': 'recommend stopping frozen run after attempt 30 and preserve a separate terminal sidecar; do not reinterpret timeout rows as unsatisfiable',
        'statistical_model': 'conditional exploratory Bernoulli check only if future query outcomes are independent and share a constant productive probability p',
        'minimum_productive_queries_for_first_rank_check': 1098,
        'first_rank_check_verified_rows': 4390,
        'maximum_models_per_query': 4,
        'preparation_attempt_cap': 8192,
        'null_productive_probability_lower_bound': '1098/8192',
        'zero_in_next_23_null_tail_upper_bound': '(7094/8192)^23 < 1/20',
        'claim_boundary': 'operational futility signal under stated sampling model, not a proof that future queries or the target are indecomposable',
        'first_seven_sha256': sha(prefix),
        'audit_source_sha256': sha(BASE / 'audit.py'),
        'lean_source_sha256': sha(BASE / 'FutilityArithmetic.lean'),
        'lean_toolchain_sha256': sha(BASE / 'lean-toolchain'),
        'freeze_source_sha256': sha(Path(__file__)),
    }
    with (BASE / 'protocol.json').open('x') as stream:
        json.dump(record, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print('FROZEN_PROSPECTIVE_ATTEMPTS_8_TO_30', record['frozen_utc'])


if __name__ == '__main__':
    main()
