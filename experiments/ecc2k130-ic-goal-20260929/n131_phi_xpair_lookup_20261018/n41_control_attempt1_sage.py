"""Positive public-point control for the x-keyed pair lookup on archived W9."""
import hashlib
import json
import random
import resource
import time
from collections import defaultdict
from pathlib import Path

from sage.all import GF, PolynomialRing, EllipticCurve

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    cfg_path = HERE / 'protocol.json'
    cfg = json.loads(cfg_path.read_text())
    for name, item in cfg['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    path = Path(cfg['sources']['n41_join_input']['path'])
    start = time.monotonic()
    ring = PolynomialRing(GF(2), 'u')
    u = ring.gen()
    field = GF(2**41, 'a', modulus=u**41 + u**3 + 1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    with path.open() as src:
        header = src.readline().split()
        assert header[:3] == ['ECC2K41', '5', '284']
        target = curve(field.fetch_int(int(header[3])),
                       field.fetch_int(int(header[4])))
        slots = [dict() for _ in range(5)]
        for line in src:
            parts = line.split()
            assert parts[0] == 'S' and len(parts) == 11
            slot, state = int(parts[1]), int(parts[2])
            point = curve(field.fetch_int(int(parts[9])),
                          field.fetch_int(int(parts[10])))
            assert state not in slots[slot]
            slots[slot][state] = point
    assert all(len(s) == 284 for s in slots)
    index = defaultdict(list)
    for i in range(284):
        for j in range(284):
            pair = slots[0][i] + slots[1][j]
            assert not pair.is_zero()
            index[pair[0]].append((pair, i, j))
    target_rot = curve(target[0] ** 8, target[1] ** 8)
    right = slots[3][283] + slots[4][152]
    need = target_rot - slots[2][233] - right
    candidates = index.get(need[0], [])
    hits = [(i, j) for pair, i, j in candidates if pair == need]
    assert (0, 130) in hits
    assert slots[0][0] + slots[1][130] + slots[2][233] + right == target_rot
    rng = random.Random(cfg['n41_control_seed'])
    x_rejects = exact_hits = 0
    for _ in range(cfg['n41_family_queries']):
        c, a, b = (rng.randrange(284) for _ in range(3))
        residual = target_rot - slots[2][c] - slots[3][a] - slots[4][b]
        bucket = index.get(residual[0])
        if bucket is None:
            x_rejects += 1
        elif any(pair == residual for pair, _, _ in bucket):
            exact_hits += 1
    result = {'status': 'PASS_N41_PUBLIC_TARGET_XPAIR_HIT',
              'public_target_orientation': 3,
              'expected_left_state_ids': [0, 130],
              'matching_left_state_ids': [list(item) for item in hits],
              'indexed_pair_states': 284 * 284,
              'distinct_x_keys': len(index),
              'target_conditioned_family_queries': cfg['n41_family_queries'],
              'x_rejected_families': x_rejects,
              'exact_hit_families': exact_hits,
              'wall_seconds': time.monotonic() - start,
              'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'protocol_sha256': sha(cfg_path),
              'join_input_sha256': sha(path)}
    with (HERE / 'n41_control_result.json').open('x') as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write('\n')
    print(json.dumps({key: result[key] for key in
                      ('status', 'indexed_pair_states', 'distinct_x_keys',
                       'x_rejected_families', 'exact_hit_families',
                       'wall_seconds', 'peak_rss_bytes')}, sort_keys=True))


if __name__ == '__main__':
    main()
