"""CT202 source-only balanced-order and same-binary control for CT201 evidence.

This does NOT attest execution, timings, RNG seeds, command arguments, coldness,
binary contents, or host/PCC standing. The claimed chronology is untrusted data.
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

from ct201_complete_solve_gate import evaluate, must, HEX64

ARMS = ('transfer', 'rho', 'rho_sham', 'bsgs', 'ic')
BASE = (0, 1, 4, 2, 3)


def roster():
    """Ten-position-balanced five-arm Williams schedule, fixed before timing."""
    first = tuple(
        tuple(ARMS[(k + j) % 5] for k in BASE)
        for j in range(5)
    )
    return first + tuple(tuple(reversed(row)) for row in first)


ROSTER = roster()


def audit(doc):
    """Reject post hoc ordering and executable substitution before CT201 scoring."""
    must(type(doc) is dict, 'CT202: document must be object')
    rows = doc.get('runs')
    must(type(rows) is list and len(rows) >= 50 and len(rows) % 50 == 0,
         'CT202: at least one complete 10-block/50-run balanced cycle required')
    binary_for_arm = {}
    for idx, row in enumerate(rows):
        must(type(row) is dict, f'CT202: row {idx} must be object')
        block, pos = divmod(idx, 5)
        want = ROSTER[block % 10][pos]
        must(type(row.get('block')) is int and row['block'] == block
             and row.get('arm') == want,
             f'CT202: chronological roster mismatch at row {idx}, block {block}, position {pos}')
        sha = row.get('binary_sha256')
        must(type(sha) is str and HEX64.fullmatch(sha),
             f'CT202: invalid executable hash at row {idx}')
        previous = binary_for_arm.setdefault(want, sha)
        must(previous == sha, f'CT202: executable changed within arm {want}')
    must(binary_for_arm['rho'] == binary_for_arm['rho_sham'],
         'CT202: rho/rho_sham A/A must bind identical executable SHA-256')
    result = evaluate(doc)
    result['ct202_order_and_binary_binding'] = {
        'status': 'source_protocol_only_untrusted_chronology',
        'complete_williams_cycles': len(rows) // 50,
        'recorded_order_matches_frozen_roster': True,
        'binary_hash_stable_per_arm': True,
        'rho_sham_binary_equal': True,
        'no_signed_execution_or_custody_attestation': True,
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path, help='CT201 v1 full-cold evidence JSON')
    args = parser.parse_args()
    try:
        result = audit(json.loads(args.file.read_text(encoding='utf8')))
        print(json.dumps(result, sort_keys=True, indent=2))
    except (ValueError, KeyError, TypeError, OverflowError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
