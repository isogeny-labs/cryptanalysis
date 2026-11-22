"""CT203: prospective distinct-target, per-block complete cold ECDLP scorer.

Source-only evidence consistency. Cannot attest chronological execution, hidden
target-log leakage, native times, binary bytes, raw input custody, or PCC.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path

from ct201_complete_solve_gate import (
    HEX64, PHASES, add, affine, digest_input, integer, mul, must, prime64,
    quantile,
)
from ct202_balanced_order_gate import ROSTER

SCHEMA = 'ct203/fresh-target-complete-cold/v1'
EXPECTED_ROW = {
    'block', 'arm', 'solution', 'input_sha256', 'stdout_sha256',
    'binary_sha256', 'host_id', 'cold_process', 'external_wall_ns',
    'peak_rss_kib', 'phases_ns',
}
INT64MAX = 2**63 - 1


def canonical_sha(obj):
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(',', ':'),
                   ensure_ascii=True).encode('utf-8')
    ).hexdigest()


def audit(doc):
    """Recompute each different target's scalar and compare five full cold arms."""
    must(type(doc) is dict and set(doc) == {
        'schema', 'curve', 'memory_cap_kib', 'target_roster',
        'target_roster_sha256', 'runs',
    }, 'CT203: top-level schema mismatch')
    must(doc['schema'] == SCHEMA, 'CT203: unsupported schema')
    c = doc['curve']
    must(type(c) is dict and set(c) == {'p', 'a', 'b', 'r', 'G'},
         'CT203: base curve schema mismatch')
    p = integer(c['p'], 'p', 5)
    a = integer(c['a'], 'a')
    b = integer(c['b'], 'b')
    r = integer(c['r'], 'r', 23)
    must(prime64(p) and prime64(r),
         'CT203: p and r must be prime in the <2^64 domain')
    must(a < p and b < p and (4*a*a*a + 27*b*b) % p != 0,
         'CT203: singular or noncanonical source curve')
    G = affine(c['G'], 'G', p, a, b)
    must(mul(G, r, p, a) is None,
         'CT203: base point not of declared prime order')
    cap = integer(doc['memory_cap_kib'], 'memory_cap_kib', 1)
    must(cap <= INT64MAX, 'CT203: memory cap exceeds int64')

    targets = doc['target_roster']
    must(type(targets) is list and len(targets) >= 10
         and len(targets) % 10 == 0,
         'CT203: only complete 10-block target cycles accepted')
    claimed_digest = doc['target_roster_sha256']
    must(type(claimed_digest) is str and HEX64.fullmatch(claimed_digest),
         'CT203: invalid target roster SHA256')
    must(canonical_sha(targets) == claimed_digest,
         'CT203: target roster digest mismatch')

    # On a nonsingular odd-characteristic short Weierstrass curve, equal x
    # means equal points or additive inverses. Treat both as a repeat.
    seen_x = set()
    target_points = []
    input_hashes = []
    for j, entry in enumerate(targets):
        must(type(entry) is dict and set(entry) == {'block', 'Q'}
             and type(entry['block']) is int and entry['block'] == j,
             f'CT203: malformed target roster block {j}')
        Q = affine(entry['Q'], f'target[{j}].Q', p, a, b)
        must(Q[0] not in seen_x,
             f'CT203: repeated target up to inverse at block {j}')
        seen_x.add(Q[0])
        must(mul(Q, r, p, a) is None,
             f'CT203: target {j} not in source subgroup')
        target_points.append(Q)
        input_hashes.append(digest_input({**c, 'Q': entry['Q']}))

    rows = doc['runs']
    must(type(rows) is list and len(rows) == 5 * len(targets),
         'CT203: must supply exactly five chronological arms per target')
    binaries = {}
    hosts = set()
    blocks = []
    for j, Q in enumerate(target_points):
        block = {}
        for pos, row in enumerate(rows[5*j:5*j+5]):
            idx = 5*j + pos
            must(type(row) is dict and set(row) == EXPECTED_ROW,
                 f'CT203: run {idx} schema mismatch')
            arm = ROSTER[j % 10][pos]
            must(type(row['block']) is int and row['block'] == j
                 and row['arm'] == arm,
                 f'CT203: chronological Williams roster mismatch at {idx}')
            sol = integer(row['solution'], f'CT203 run {idx} scalar')
            must(sol < r and mul(G, sol, p, a) == Q,
                 f'CT203: wrong public-target logarithm in run {idx}')
            for key in ('input_sha256', 'stdout_sha256', 'binary_sha256'):
                value = row[key]
                must(type(value) is str and HEX64.fullmatch(value),
                     f'CT203: bad {key} in run {idx}')
            must(row['input_sha256'] == input_hashes[j],
                 f'CT203: wrong per-target input digest in run {idx}')
            sha = row['binary_sha256']
            old = binaries.setdefault(arm, sha)
            must(old == sha, f'CT203: executable drift for {arm}')
            must(type(row['host_id']) is str and bool(row['host_id'].strip()),
                 f'CT203: empty host id in run {idx}')
            hosts.add(row['host_id'])
            must(row['cold_process'] is True,
                 f'CT203: warm/non-cold declared process in run {idx}')
            wall = integer(row['external_wall_ns'], f'CT203 run {idx} wall', 1)
            rss = integer(row['peak_rss_kib'], f'CT203 run {idx} RSS', 1)
            must(wall <= INT64MAX and rss <= cap,
                 f'CT203: wall overflow or memory cap breach in run {idx}')
            phases = row['phases_ns']
            must(type(phases) is dict and set(phases) == PHASES,
                 f'CT203: absent or extra phase in run {idx}')
            accounted = 0
            for key, duration in phases.items():
                integer(duration, f'CT203 run {idx}.{key}')
                must(duration <= INT64MAX,
                     f'CT203: phase int64 overflow in run {idx}')
                accounted += duration
            must(accounted <= wall,
                 f'CT203: phase sum exceeds process wall in run {idx}')
            block[arm] = (wall, rss, wall-accounted)
        blocks.append(block)
    must(len(hosts) == 1, 'CT203: matched single host required')
    must(binaries['rho'] == binaries['rho_sham'],
         'CT203: rho/rho_sham must declare identical executable bytes')

    diffs, shams, memory, unattributed = [], [], [], []
    for j, block in enumerate(blocks):
        fast = min(('rho', 'bsgs', 'ic'), key=lambda arm: (block[arm][0], arm))
        diffs.append(math.log(block[fast][0] / block['transfer'][0]))
        shams.append(math.log(block['rho'][0] / block['rho_sham'][0]))
        memory.append({'block': j,
                       'candidate_kib': block['transfer'][1],
                       'fastest_baseline_kib': block[fast][1],
                       'fastest_baseline_arm': fast})
        unattributed.append({'block': j,
                             'candidate_ns': block['transfer'][2],
                             'fastest_baseline_ns': block[fast][2]})
    n = len(diffs)
    rng = random.Random(0xC7203)
    means = [sum(diffs[rng.randrange(n)] for _ in range(n)) / n
             for _ in range(4096)]
    lo, hi = quantile(means, .025), quantile(means, .975)
    aa_ratio = math.exp(sum(shams)/n)
    aa_ok = abs(math.log(aa_ratio)) <= math.log(1.10)
    eligible = lo > 0 and aa_ok
    return {
        'schema': 'ct203/candidate-diagnostic/v1',
        'standing': '[pcc:unverified]',
        'outcome': ('candidate_needs_external_signed_verifier'
                    if eligible else 'no_qualified_advantage'),
        'distinct_target_classes': len(targets),
        'complete_williams_cycles': len(targets)//10,
        'target_roster_sha256_unattested': claimed_digest,
        'reported_input_sha256_recomputed_per_target': True,
        'reported_logarithms_recomputed_per_target': True,
        'reported_binary_stability_unattested': True,
        'cold_executions_and_blind_challenge_generation_unattested': True,
        'host_id_unverified': next(iter(hosts)),
        'candidate_ratio_geomean': math.exp(sum(diffs)/n),
        'bootstrap_ratio_lower_95': math.exp(lo),
        'bootstrap_ratio_upper_95': math.exp(hi),
        'aa_rho_over_sham_geomean': aa_ratio,
        'aa_within_preregistered_10pct': aa_ok,
        'memory_cap_kib': cap,
        'per_block_memory': memory,
        'per_block_unattributed_wall_ns': unattributed,
        'note': 'Synthetic/source validation only; not genuine native timing, blind target custody, independent execution proof, or PCC.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path)
    args = parser.parse_args()
    try:
        result = audit(json.loads(args.file.read_text(encoding='utf-8')))
        print(json.dumps(result, sort_keys=True, indent=2))
    except (ValueError, KeyError, TypeError, OverflowError, ZeroDivisionError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
