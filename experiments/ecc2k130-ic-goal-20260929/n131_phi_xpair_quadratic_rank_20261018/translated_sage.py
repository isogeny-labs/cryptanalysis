"""Quadratic feature rank of T-S x coordinates for all public target lifts."""
import hashlib
import importlib.util
import json
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
    cfg = json.loads((HERE / 'translated_protocol.json').read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_TRANSLATION'
    for name, entry in cfg['sources'].items():
        assert sha(entry['path']) == entry['sha256'], name
    pair = load_module('frozen_pair_lookup2', cfg['sources']['pair_lookup']['path'])
    quad = load_module('frozen_quadratic_features', cfg['sources']['run_sage']['path'])
    sys.path.insert(0, str(ROOT / 'ecc2k130/codegen'))
    import curves
    import field
    onb = field.Onb(131)
    curve = curves.Curve(onb)
    geo = json.loads(Path(cfg['sources']['geometry']['path']).read_text())
    basis = [int(v, 16) for v in geo['domain']['basis_coordinate_masks_hex']]
    base = dict(pair.build_base(onb, curve, basis))
    endpoints = [tuple(onb.fromCoords(int(v)) for v in record['target_coordinates'])
                 for record in geo['official_single_target_cofactor_fiber']['four_verified_lifts']]
    assert len(endpoints) == 4
    witness = json.loads(Path(cfg['sources']['witness']['path']).read_text())
    pivots = [{} for _ in endpoints]
    independent_indices = [[] for _ in endpoints]
    elapsed = time.monotonic()
    status = 'ALL_FOUR_FULL_RANK'
    for k, (code0, sign0, code1, xhex) in enumerate(witness):
        p0 = base[code0]
        if sign0:
            p0 = curve.neg(p0)
        p1 = curve.frob(base[code1], 1)
        summed = curve.add(p0, p1)
        assert summed is not None and onb.toCoords(summed[0]) == int(xhex, 16)
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
        if time.monotonic() - elapsed >= cfg['wall_cap_seconds']:
            status = 'WALL_CAP'
            break
    result = {'status': status, 'candidate_id': None, 'curve_id': cfg['curve_id'],
              'rank_by_lift': [len(p) for p in pivots], 'feature_dimension': 8647,
              'processed_witnesses': k + 1, 'wall_seconds': time.monotonic() - elapsed,
              'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'independent_indices_sha256': hashlib.sha256(json.dumps(independent_indices, separators=(',', ':')).encode()).hexdigest()}
    (HERE / 'translated_indices.json').write_text(json.dumps(independent_indices, separators=(',', ':')) + '\n')
    (HERE / 'translated_result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
