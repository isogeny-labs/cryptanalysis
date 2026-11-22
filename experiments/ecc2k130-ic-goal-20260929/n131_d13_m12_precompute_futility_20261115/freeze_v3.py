"""Freeze a fully unstarted future panel; preserve earlier panel versions."""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    previous = BASE / 'protocol_v2.json'
    old = json.loads(previous.read_text())
    run = Path(old['run_dir'])
    lines = (run / 'precomputation_attempts.jsonl').read_bytes().splitlines(keepends=True)
    assert len(lines) == 8
    assert lines == (BASE / 'first_eight.jsonl').read_bytes().splitlines(keepends=True)
    assert all(json.loads(line)['status'] == 'timeout' and
               json.loads(line)['verified_relation_count'] == 0 for line in lines)
    progress = json.loads((run / 'precompute_progress.json').read_text())
    assert progress['status'] == 'RUNNING' and progress['attempts_completed'] == 8
    assert progress['verified_relations'] == progress['rank'] == 0
    assert (run / 'precomputation/target_00009/model_01/cryptominisat.stdout.txt').is_file()
    assert not (run / 'precomputation/target_00010').exists()
    assert not (run / 'result.json').exists()
    os.kill(53627, 0)
    record = {
        'kind': 'n131_d13_m12_prospective_precompute_futility_protocol_v3',
        'status': 'FROZEN_BEFORE_QUERY_TEN_STARTED',
        'frozen_utc': datetime.now(timezone.utc).isoformat(),
        'amends_protocol_v2_sha256': sha(previous),
        'reason_for_amendment': 'Query eight was already running when v1/v2 froze; use 23 wholly unstarted future queries for the conditional Bernoulli tail.',
        'curve_id': old['curve_id'], 'candidate_id': old['candidate_id'],
        'workload_id': old['workload_id'], 'run_id': old['run_id'],
        'run_dir': old['run_dir'],
        'observed_prefix_attempt_count': 8,
        'excluded_inflight_query_index': 9,
        'prospective_attempt_indices': [10, 32],
        'prospective_sample_size': 23,
        'productive_definition': old['productive_definition'],
        'stop_recommendation_condition': 'all queries 10-32 complete as independently audited ordinary timeouts with zero verified relations',
        'continue_condition': 'query nine or any query 10-32 returns a verified relation',
        'ineligible_condition': 'an infrastructure or producer failure occurs in the prospective panel',
        'statistical_model': old['statistical_model'],
        'null_productive_probability_lower_bound': old['null_productive_probability_lower_bound'],
        'zero_in_next_23_null_tail_upper_bound': old['zero_in_next_23_null_tail_upper_bound'],
        'claim_boundary': old['claim_boundary'],
        'source_sha256': {'auditor': sha(BASE / 'audit_v3.py'),
                          'first_eight': sha(BASE / 'first_eight.jsonl'),
                          'lean_arithmetic': sha(BASE / 'FutilityArithmetic.lean'),
                          'freeze_v3': sha(Path(__file__))},
    }
    with (BASE / 'protocol_v3.json').open('x') as stream:
        json.dump(record, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print('FROZEN_V3_BEFORE_QUERY_TEN_STARTED', record['frozen_utc'])


if __name__ == '__main__':
    main()
