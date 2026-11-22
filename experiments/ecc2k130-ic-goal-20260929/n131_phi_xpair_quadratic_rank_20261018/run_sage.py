"""Rank of Boolean quadratic features on exact Q1358 pair-sum x coordinates."""
import hashlib
import importlib.util
import json
import random
import resource
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def feature_row(x):
    """Constant, x_i, x_i*x_j (i<j), bit 0 is lowest-order coordinate."""
    active = [i for i in range(131) if x >> i & 1]
    row = 1
    for i in active:
        row |= 1 << (1 + i)
    for ai, i in enumerate(active):
        start = 132 + i * (2 * 131 - i - 1) // 2
        for j in active[ai + 1:]:
            row |= 1 << (start + j - i - 1)
    return row


def main():
    cfg = json.loads((HERE / 'protocol.json').read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_RUN'
    for name, source in cfg['sources'].items():
        assert sha(source['path']) == source['sha256'], name
    pair = load_module('frozen_pair_lookup', cfg['sources']['pair_lookup']['path'])
    sys.path.insert(0, str(ROOT / 'ecc2k130/codegen'))
    import field
    import curves
    onb = field.Onb(131)
    curve = curves.Curve(onb)
    geometry = json.loads(Path(cfg['sources']['geometry']['path']).read_text())
    basis = [int(v, 16) for v in geometry['domain']['basis_coordinate_masks_hex']]
    base = pair.build_base(onb, curve, basis)
    slot1 = [curve.frob(p, 1) for _, p in base]
    assert len(base) == 532 and len(slot1) == 532
    rng = random.Random(cfg['seed'])
    pivots = {}
    seen = set()
    witness = []
    attempted = 0
    duplicated = 0
    start = time.monotonic()
    status = 'ROW_CAP'
    for _ in range(cfg['max_attempts']):
        if time.monotonic() - start >= cfg['wall_cap_seconds']:
            status = 'WALL_CAP'
            break
        attempted += 1
        i = rng.randrange(532)
        j = rng.randrange(532)
        s = rng.randrange(2)
        p = base[i][1]
        if s:
            p = curve.neg(p)
        summed = curve.add(p, slot1[j])
        assert summed is not None and curve.onCurve(summed)
        x = onb.toCoords(summed[0])
        if x in seen:
            duplicated += 1
            continue
        seen.add(x)
        row = feature_row(x)
        while row:
            bit = row.bit_length() - 1
            old = pivots.get(bit)
            if old is None:
                pivots[bit] = row
                witness.append([base[i][0], s, base[j][0], format(x, '034x')])
                break
            row ^= old
        if len(pivots) == 8647:
            status = 'FULL_RANK'
            break
    result = {
        'status': status, 'candidate_id': None, 'curve_id': cfg['curve_id'],
        'feature_dimension': 8647, 'rank': len(pivots),
        'attempts': attempted, 'unique_x_sampled': len(seen),
        'duplicate_x': duplicated, 'independent_witnesses': len(witness),
        'wall_seconds': time.monotonic() - start,
        'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'seed': cfg['seed'],
        'witness_sha256': hashlib.sha256(json.dumps(witness, separators=(',', ':')).encode()).hexdigest(),
    }
    (HERE / 'witness.json').write_text(json.dumps(witness, separators=(',', ':')) + '\n')
    (HERE / 'result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
