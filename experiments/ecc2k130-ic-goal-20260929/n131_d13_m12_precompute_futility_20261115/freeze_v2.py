"""Amend the prospective gate to require independently audited timeout rows."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    original = BASE / 'protocol.json'
    first = json.loads(original.read_text())
    run = Path(first['run_dir'])
    rows = (run / 'precomputation_attempts.jsonl').read_bytes().splitlines()
    assert len(rows) == 7
    assert first['prospective_attempt_indices'] == [8, 30]
    amendment = {
        'kind': 'n131_d13_m12_prospective_precompute_futility_protocol_v2',
        'status': 'FROZEN_BEFORE_ATTEMPT_EIGHT_COMPLETED',
        'frozen_utc': datetime.now(timezone.utc).isoformat(),
        'amends_protocol_sha256': sha(original),
        'reason_for_amendment': 'Require every zero-yield prospective row to be an independently audited ordinary timeout; infrastructure and producer failures cannot count as low relation yield.',
        'run_dir': first['run_dir'],
        'curve_id': first['curve_id'],
        'candidate_id': first['candidate_id'],
        'workload_id': first['workload_id'],
        'run_id': first['run_id'],
        'observed_prefix_attempt_count': 7,
        'prospective_attempt_indices': [8, 30],
        'prospective_sample_size': 23,
        'productive_definition': first['productive_definition'],
        'stop_recommendation_condition': 'all 23 future attempts complete as independently audited timeout rows with zero verified relations',
        'continue_condition': 'at least one future attempt contains a verified relation',
        'ineligible_condition': 'any zero-relation future attempt is not an audited ordinary timeout, including OOM or producer/infrastructure failure',
        'statistical_model': first['statistical_model'],
        'null_productive_probability_lower_bound': first['null_productive_probability_lower_bound'],
        'zero_in_next_23_null_tail_upper_bound': first['zero_in_next_23_null_tail_upper_bound'],
        'claim_boundary': first['claim_boundary'],
        'source_sha256': {'auditor': sha(BASE / 'audit_v2.py'),
                          'first_seven': sha(BASE / 'first_seven.jsonl'),
                          'lean_arithmetic': sha(BASE / 'FutilityArithmetic.lean'),
                          'freeze_v2': sha(Path(__file__))},
    }
    with (BASE / 'protocol_v2.json').open('x') as stream:
        json.dump(amendment, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print('FROZEN_V2_BEFORE_ATTEMPT_EIGHT_COMPLETED', amendment['frozen_utc'])


if __name__ == '__main__':
    main()
