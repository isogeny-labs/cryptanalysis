"""Extend the four translated rank samples until each certificate is full."""
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


def main():
    cfg = json.loads((HERE / 'translated_extend_protocol.json').read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_EXTENSION'
    for name, entry in cfg['sources'].items():
        assert sha(entry['path']) == entry['sha256'], name
    pair = load_module('frozen_pair_lookup_ext', cfg['sources']['pair_lookup']['path'])
    quad = load_module('frozen_quadratic_features_ext', cfg['sources']['run_sage']['path'])
    sys.path.insert(0, str(ROOT / 'ecc2k130/codegen'))
    import curves
    import field
    onb = field.Onb(131)
    curve = curves.Curve(onb)
    geo = json.loads(Path(cfg['sources']['geometry']['path']).read_text())
    basis = [int(v, 16) for v in geo['domain']['basis_coordinate_masks_hex']]
    base = pair.build_base(onb, curve, basis)
    by_code = dict(base)
    slot1 = [curve.frob(p, 1) for _, p in base]
    endpoints = [tuple(onb.fromCoords(int(v)) for v in record['target_coordinates'])
                 for record in geo['official_single_target_cofactor_fiber']['four_verified_lifts']]
    assert len(endpoints) == 4
    witness = json.loads(Path(cfg['sources']['witness']['path']).read_text())
    old_result = json.loads(Path(cfg['sources']['translated_result']['path']).read_text())
    assert old_result['rank_by_lift'] == [8646, 8645, 8646, 8647]
    pivots = [{} for _ in endpoints]
    independent_indices = [[] for _ in endpoints]
    start = time.monotonic()

    def ingest(k, code0, sign0, code1, xhex=None):
        p0 = by_code[code0]
        if sign0:
            p0 = curve.neg(p0)
        summed = curve.add(p0, curve.frob(by_code[code1], 1))
        assert summed is not None and curve.onCurve(summed)
        x = onb.toCoords(summed[0])
        if xhex is not None:
            assert x == int(xhex, 16)
        for endpoint_index, endpoint in enumerate(endpoints):
            residual = curve.add(endpoint, curve.neg(summed))
            assert residual is not None and curve.onCurve(residual)
            row = quad.feature_row(onb.toCoords(residual[0]))
            while row:
                bit = row.bit_length() - 1
                old = pivots[endpoint_index].get(bit)
                if old is None:
                    pivots[endpoint_index][bit] = row
                    independent_indices[endpoint_index].append(k)
                    break
                row ^= old
        return format(x, '034x')

    for k, (code0, sign0, code1, xhex) in enumerate(witness):
        ingest(k, code0, sign0, code1, xhex)
    assert [len(p) for p in pivots] == old_result['rank_by_lift']
    rng = random.Random(cfg['extension_seed'])
    extra = []
    status = 'EXTRA_DRAW_CAP'
    for draw in range(cfg['max_extra_draws']):
        if time.monotonic() - start >= cfg['wall_cap_seconds']:
            status = 'WALL_CAP'
            break
        i = rng.randrange(532)
        j = rng.randrange(532)
        sign0 = rng.randrange(2)
        code0, code1 = base[i][0], base[j][0]
        xhex = ingest(len(witness) + draw, code0, sign0, code1)
        extra.append([code0, sign0, code1, xhex])
        if all(len(p) == 8647 for p in pivots):
            status = 'ALL_FOUR_FULL_RANK'
            break
    result = {'status': status, 'candidate_id': None, 'curve_id': cfg['curve_id'],
              'rank_by_lift': [len(p) for p in pivots], 'feature_dimension': 8647,
              'initial_witnesses': len(witness), 'extra_draws': len(extra),
              'wall_seconds': time.monotonic() - start,
              'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (HERE / 'translated_extra_witness.json').write_text(json.dumps(extra, separators=(',', ':')) + '\n')
    (HERE / 'translated_extended_indices.json').write_text(json.dumps(independent_indices, separators=(',', ':')) + '\n')
    (HERE / 'translated_extended_result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
