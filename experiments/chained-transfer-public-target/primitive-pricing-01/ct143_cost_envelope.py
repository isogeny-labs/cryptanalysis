#!/usr/bin/env python3
"""CT143 exact selected-call reuse cost envelope; not a cold ECDLP benchmark.

Never interpret the optimized-route gap C169-C13a-C13b as a reuse saving.
[pcc:unverified]
"""
from __future__ import annotations
import argparse
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

ARMS = ('original-1', 'reuse-1', 'reuse-2', 'original-2')
OPS = ('C169', 'C13_first', 'C13_second', 'D')


def require(ok, why):
    if not ok:
        raise ValueError('CT143 REJECTED: ' + why)


def rational(v, name, *, allow_zero=False):
    require(type(v) in (int, Fraction), name + ' must be exact integer/rational')
    x = Fraction(v)
    require(x >= 0 if allow_zero else x > 0, name + ' must be nonnegative' if allow_zero else name + ' must be positive')
    return x


def envelope(a, b, c, d, extra=None):
    a, b, c, d = (rational(x, n) for x, n in zip((a, b, c, d), OPS))
    if extra is not None:
        extra = rational(extra, 'extra-cold-ns', allow_zero=True)
    two = b + c
    original_direct = 2*a
    original_twohop = 2*two
    reuse_direct = a + d
    reuse_literal = two + 2*d
    reuse_retained = two + d
    best_source = min(original_direct, original_twohop)
    best_reuse = min(reuse_direct, reuse_literal, reuse_retained)
    gross = best_source - best_reuse
    require(gross == min(a, two) - d, 'cost model exact identity')
    require(reuse_literal >= reuse_retained, 'literal dominance')
    require(reuse_direct - reuse_retained == a - two, 'route ranking independent of D')
    x = {
        'original_direct_ns': original_direct,
        'original_twohop_ns': original_twohop,
        'reuse_direct_ns': reuse_direct,
        'reuse_literal_ns': reuse_literal,
        'reuse_retained_ns': reuse_retained,
        'best_original_optimistic_ns': best_source,
        'best_reuse_optimistic_ns': best_reuse,
        'saving_direct_ns': a-d,
        'saving_literal_ns': two-2*d,
        'saving_retained_ns': two-d,
        'route_ranking_ns': a-two,
        'gross_headroom_ns': gross,
        'gross_positive': gross > 0,
        'additional_cold_overhead_known': extra is not None,
    }
    if extra is not None:
        x.update({'assumed_extra_cold_ns': extra,
                  'net_headroom_ns': gross-extra,
                  'net_positive_under_assumption': gross > extra})
    return x


def encode(x):
    if isinstance(x, Fraction):
        return str(x)
    if isinstance(x, dict):
        return {k: encode(v) for k, v in x.items()}
    if isinstance(x, list):
        return [encode(v) for v in x]
    return x


def selftest():
    a = envelope(200,30,40,80)
    require(a['route_ranking_ns'] > 0 and a['gross_headroom_ns'] < 0,
            'positive optimized route gap must not imply reuse gain')
    b = envelope(20,30,40,5)
    require(b['saving_direct_ns'] == 15 and b['gross_headroom_ns'] == 15,
            'direct saving and best route')
    c = envelope(100,20,30,5)
    require(c['saving_retained_ns'] == 45 and c['gross_headroom_ns'] == 45,
            'retained saving and best route')
    require(envelope(80,20,30,50)['gross_headroom_ns'] == 0,
            'exact break even has no strict advantage')
    require(envelope(100,20,30,5,44)['net_positive_under_assumption'],
            'positive extra overhead below margin')
    require(not envelope(100,20,30,5,45)['net_positive_under_assumption'],
            'equality must fail strict bound')
    require(not envelope(100,20,30,5,46)['net_positive_under_assumption'],
            'above margin must fail')
    # Separate source/candidate environments cannot be inferred from one arm.
    require(envelope(100,20,30,5)['best_original_optimistic_ns'] -
            envelope(100,20,30,50)['best_reuse_optimistic_ns'] == 0,
            'cross-arm cost differs when reuse doubling is slower')
    require(envelope(100,20,30,5)['best_original_optimistic_ns'] -
            envelope(100,20,30,5)['best_reuse_optimistic_ns'] == 45,
            'cross-arm same-cost reference')
    q = envelope(Fraction(3,2),Fraction(4,3),Fraction(1,6),Fraction(1,4))
    require(q['gross_headroom_ns'] == Fraction(5,4), 'exact fractions')
    require(not q['additional_cold_overhead_known'], 'unknown cold overhead stays unknown')
    for d in (1, 50, 700):
        require(envelope(100,20,30,d)['route_ranking_ns'] == 50,
                'route gap independent of doubling')
    scale = 13
    for key in ('gross_headroom_ns', 'saving_direct_ns', 'saving_literal_ns', 'saving_retained_ns'):
        require(envelope(50*scale,25*scale,10*scale,7*scale)[key] == scale*envelope(50,25,10,7)[key],
                'common scaling for ' + key)
    for bad in ((0,1,1,1,None),(-1,1,1,1,None),(1,1,1,0,None),
                (1,1,1,1,-1),(1,1,1,1,0.0),(1,1,1,'1',None)):
        try:
            envelope(*bad[:4],extra=bad[4])
        except ValueError:
            continue
        raise ValueError('CT143 SELFTEST: bad cost accepted: ' + repr(bad))
    return {'positive': 'passed', 'checks': 18, 'invalid_inputs_rejected': 6,
            'standing': '[pcc:unverified]'}


def inspect(out: Path, extra: int | None):
    import ct142_receipt_gate as ct142
    custody = ct142.inspect(out)
    require(custody['schema'] == 'ct142-receipts-and-paired-deltas/v1', 'receipt gate missing')
    rows = []
    signs = Counter()
    blocks = {}
    output_hashes = custody['output_hashes']
    for arm in ARMS:
        path = out / (arm + '.json')
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == output_hashes[path.name],
                arm + ' TOCTOU hash mismatch')
        record = json.loads(raw)
        values = {op: ct142.per_call(record, op) for op in OPS}
        require(all(len(values[op]) == 12 for op in OPS), 'wrong block count')
        for block in range(12):
            v = envelope(*(values[op][block] for op in OPS), extra=extra)
            rows.append({'arm': arm, 'block': block, **v})
            blocks[(arm, block)] = v
            signs['positive' if v['gross_positive'] else
                  'zero' if v['gross_headroom_ns'] == 0 else 'negative'] += 1
    require(len(rows) == 48, 'must report all 48 blocks')
    cross_pairs = []
    cross_signs = Counter()
    for source_arm, reuse_arm in (('original-1', 'reuse-1'),
                                  ('original-2', 'reuse-2')):
        for block in range(12):
            source_best = blocks[(source_arm, block)]['best_original_optimistic_ns']
            reuse_best = blocks[(reuse_arm, block)]['best_reuse_optimistic_ns']
            cross_gap = source_best - reuse_best
            pair = {'original_arm': source_arm, 'reuse_arm': reuse_arm,
                    'block': block, 'original_best_optimistic_ns': source_best,
                    'reuse_best_optimistic_ns': reuse_best,
                    'gross_cross_arm_gap_ns': cross_gap,
                    'gross_cross_arm_positive': cross_gap > 0}
            if extra is not None:
                pair['net_cross_arm_gap_ns'] = cross_gap-extra
                pair['net_cross_arm_positive_under_assumption'] = cross_gap > extra
            cross_pairs.append(pair)
            cross_signs['positive' if cross_gap > 0 else
                        'zero' if cross_gap == 0 else 'negative'] += 1
    require(len(cross_pairs) == 24, 'must report 24 ABBA cross-arm positions')
    return encode({
        'schema': 'ct143-selected-call-cost-envelope/v1',
        'standing': '[pcc:unverified]',
        'scope': 'optimistic primitive-count-only gross headroom, not actual original-prime cold ECDLP time',
        'selection_caveat': 'per-block route oracle is an optimistic envelope, NOT a fixed whole-cohort solver',
        'gross_formula': 'min(C169,C13_first+C13_second)-D',
        'extra_cold_overhead': 'unknown' if extra is None else str(extra),
        'block_count': len(rows),
        'gross_signs': dict(sorted(signs.items())),
        'cross_arm_scope': '24 ABBA-position-matched same-block cost diagnostics, NOT synchronized process timings',
        'cross_arm_count': len(cross_pairs),
        'cross_arm_signs': dict(sorted(cross_signs.items())),
        'cross_arm_records': cross_pairs,
        'source_sha256_roster': custody['source_hashes'],
        'binary_sha256_roster': custody['binary_hashes'],
        'records': rows,
    })


def main():
    p = argparse.ArgumentParser()
    p.add_argument('directory', type=Path, nargs='?')
    p.add_argument('--extra-cold-ns', type=int)
    p.add_argument('--out', type=Path)
    p.add_argument('--self-test', action='store_true')
    args = p.parse_args()
    if args.self_test:
        print(json.dumps(selftest(), sort_keys=True))
        return
    require(args.directory is not None, 'input directory required')
    if args.extra_cold_ns is not None:
        rational(args.extra_cold_ns, 'extra-cold-ns', allow_zero=True)
    report = inspect(args.directory, args.extra_cold_ns)
    payload = json.dumps(report, sort_keys=True, indent=2) + '\n'
    if args.out:
        require(not args.out.exists(), 'refuse to overwrite existing evidence')
        args.out.write_text(payload)
    print(json.dumps({'schema': report['schema'], 'block_count': report['block_count'],
                      'gross_signs': report['gross_signs'], 'cross_arm_count': report['cross_arm_count'],
                      'cross_arm_signs': report['cross_arm_signs'],
                      'standing': report['standing']}, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, ZeroDivisionError) as exc:
        raise SystemExit(str(exc))
