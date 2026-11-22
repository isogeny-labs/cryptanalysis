"""CT201 independent *mathematical* verifier and conservative full-cold scorer.

This is NOT an independent execution/PCC verifier: raw producer timings, host
identity, logs, input digests, and receipt provenance require a signed external
verifier. Never classify this reader's output as a demonstrated speedup.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
from pathlib import Path

ARMS = frozenset({'transfer', 'rho', 'rho_sham', 'bsgs', 'ic'})
PHASES = frozenset({'setup', 'transfer', 'relation_collection', 'linear_algebra',
                    'individual_log', 'verification', 'other'})
SCHEMA = 'ct201/full-cold-evidence/v1'
HEX64 = re.compile(r'^[a-f0-9]{64}$')


def must(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, name, low=0):
    must(type(value) is int and value >= low, f'{name}: nonnegative/positive integer required')
    return value


def prime64(n):
    """Deterministic Miller--Rabin for 0 <= n < 2^64 (not larger!)."""
    integer(n, 'prime candidate', 0)
    must(n < 2**64, 'primality proof only valid for <2^64')
    if n < 2:
        return False
    for q in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % q == 0:
            return n == q
    d = n - 1
    s = 0
    while d % 2 == 0:
        s += 1
        d //= 2
    for a in (2, 325, 9375, 28178, 450775, 9780504, 1795265022):
        a %= n
        if not a:
            continue
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def affine(value, name, p, a, b):
    must(type(value) is list and len(value) == 2, f'{name}: affine pair required')
    x = integer(value[0], name + '.x')
    y = integer(value[1], name + '.y')
    must(x < p and y < p and (y*y - x*x*x - a*x - b) % p == 0,
         f'{name}: noncanonical or off curve')
    return (x, y)


def add(P, Q, p, a):
    if P is None:
        return Q
    if Q is None:
        return P
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2 and (y1 + y2) % p == 0:
        return None
    if P == Q:
        slope = ((3*x1*x1 + a) * pow(2*y1, -1, p)) % p
    else:
        slope = ((y2 - y1) * pow((x2 - x1) % p, -1, p)) % p
    x3 = (slope*slope - x1 - x2) % p
    return (x3, (slope*(x1-x3) - y1) % p)


def mul(P, k, p, a):
    R = None
    while k:
        if k & 1:
            R = add(R, P, p, a)
        P = add(P, P, p, a)
        k >>= 1
    return R


def digest_input(curve):
    return hashlib.sha256(json.dumps(curve, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def quantile(vals, q):
    vals = sorted(vals)
    i = q * (len(vals)-1)
    k = int(i)
    return vals[k] if k+1 == len(vals) else vals[k]*(1-(i-k)) + vals[k+1]*(i-k)


def evaluate(doc):
    must(type(doc) is dict and set(doc) == {'schema', 'curve', 'memory_cap_kib', 'runs'},
         'top-level schema mismatch')
    must(doc['schema'] == SCHEMA, 'unknown protocol schema')
    c = doc['curve']
    must(type(c) is dict and set(c) == {'p', 'a', 'b', 'r', 'G', 'Q'}, 'curve schema mismatch')
    p = integer(c['p'], 'p', 5)
    a = integer(c['a'], 'a')
    b = integer(c['b'], 'b')
    r = integer(c['r'], 'r', 5)
    must(prime64(p) and prime64(r), 'p and prime subgroup order r required, both <2^64')
    must(a < p and b < p and (4*a*a*a + 27*b*b) % p != 0, 'singular/noncanonical curve')
    G = affine(c['G'], 'G', p, a, b)
    Q = affine(c['Q'], 'Q', p, a, b)
    must(mul(G, r, p, a) is None, 'G not in declared prime-order subgroup')
    must(mul(Q, r, p, a) is None, 'Q not in declared subgroup')
    target_digest = digest_input(c)
    cap = integer(doc['memory_cap_kib'], 'memory cap', 1)
    runs = doc['runs']
    must(type(runs) is list, 'runs must be list')
    blocks = {}
    hosts = set()
    for i, row in enumerate(runs):
        pre = f'run {i}'
        expected = {'block', 'arm', 'solution', 'input_sha256', 'stdout_sha256',
                    'binary_sha256', 'host_id', 'cold_process', 'external_wall_ns',
                    'peak_rss_kib', 'phases_ns'}
        must(type(row) is dict and set(row) == expected, f'{pre}: schema mismatch')
        k = integer(row['block'], pre+'.block')
        arm = row['arm']
        must(type(arm) is str and arm in ARMS, f'{pre}: invalid arm')
        sol = integer(row['solution'], pre+'.solution')
        must(sol < r and mul(G, sol, p, a) == Q,
             f'{pre}: wrong public-target discrete logarithm')
        for name in ('input_sha256', 'stdout_sha256', 'binary_sha256'):
            must(type(row[name]) is str and HEX64.fullmatch(row[name]), f'{pre}: invalid {name}')
        must(row['input_sha256'] == target_digest, f'{pre}: wrong public input digest')
        must(type(row['host_id']) is str and bool(row['host_id'].strip()), f'{pre}: empty host')
        hosts.add(row['host_id'])
        must(row['cold_process'] is True, f'{pre}: not a declared fresh process')
        wall = integer(row['external_wall_ns'], pre+'.external_wall_ns', 1)
        rss = integer(row['peak_rss_kib'], pre+'.peak_rss_kib', 1)
        must(rss <= cap, f'{pre}: exceeded predeclared memory cap')
        phases = row['phases_ns']
        must(type(phases) is dict and set(phases) == PHASES, f'{pre}: missing phase')
        accounted = sum(integer(t, pre+'.phase.'+name) for name, t in phases.items())
        must(accounted <= wall, f'{pre}: phase sum exceeds process wall')
        this = blocks.setdefault(k, {})
        must(arm not in this, f'{pre}: duplicate arm per block')
        this[arm] = (wall, rss, wall-accounted)
    must(len(hosts) == 1, 'matched single host required')
    must(len(blocks) >= 8 and sorted(blocks) == list(range(len(blocks))),
         'at least eight contiguous paired blocks required')
    must(all(set(v) == ARMS for v in blocks.values()), 'missing matched solver or A/A arm')
    diffs = []
    shams = []
    memories = []
    unallocated = []
    for bno in sorted(blocks):
        b = blocks[bno]
        fastest = min((b[arm][0], arm) for arm in ('rho', 'bsgs', 'ic'))
        diffs.append(math.log(fastest[0] / b['transfer'][0]))
        shams.append(math.log(b['rho'][0] / b['rho_sham'][0]))
        memories.append({'block': bno, 'candidate_kib': b['transfer'][1],
                         'fastest_baseline_kib': b[fastest[1]][1],
                         'fastest_baseline_arm': fastest[1]})
        unallocated.append({'block': bno,
                            'candidate_ns': b['transfer'][2],
                            'fastest_baseline_ns': b[fastest[1]][2]})
    n = len(diffs)
    # Purely diagnostic percentile bootstrap; no claim of independent CI/PCC.
    rng = random.Random(0xC7201)
    means = [sum(diffs[rng.randrange(n)] for _ in range(n))/n for _ in range(4096)]
    lo, hi = quantile(means, .025), quantile(means, .975)
    a_a_ratio = math.exp(sum(shams)/n)
    aa_ok = abs(math.log(a_a_ratio)) <= math.log(1.10)
    eligible = lo > 0 and aa_ok
    return {'schema': 'ct201/candidate-diagnostic/v1',
            'standing': '[pcc:unverified]',
            'outcome': 'candidate_needs_external_signed_verifier' if eligible else 'no_qualified_advantage',
            'untrusted_execution_receipts': True,
            'complete_pair_count': n,
            'host_id_unverified': next(iter(hosts)),
            'candidate_ratio_geomean': math.exp(sum(diffs)/n),
            'bootstrap_ratio_lower_95': math.exp(lo),
            'bootstrap_ratio_upper_95': math.exp(hi),
            'aa_rho_over_sham_geomean': a_a_ratio,
            'aa_within_preregistered_10pct': aa_ok,
            'memory_cap_kib': cap,
            'per_block_memory': memories,
            'per_block_unattributed_wall_ns': unallocated,
            'note': 'Times, host, stdout and binary hashes are producer-supplied; this is not a PCC verifier, native experiment or ECDLP result.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path)
    args = parser.parse_args()
    try:
        obj = json.loads(args.file.read_text())
        print(json.dumps(evaluate(obj), sort_keys=True, indent=2))
    except (ValueError, KeyError, TypeError, ZeroDivisionError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
