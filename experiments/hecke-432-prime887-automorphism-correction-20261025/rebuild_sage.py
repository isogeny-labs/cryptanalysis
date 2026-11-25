"""Quotient special source chains by automorphisms and rebuild the p887 image."""
import importlib.util
import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'
from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
P = 887


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def record_key(row):
    return (tuple(row['source_ainvs']), row['source_label'], tuple(row['pair']))


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_P887_AUTOMORPHISM_CORRECTION'
    inputs = {}
    for name, record in protocol['inputs'].items():
        path = Path(record['path'])
        assert sha256(path.read_bytes()).hexdigest() == record['sha256']
        inputs[name] = path
    census = json.loads(inputs['census'].read_text())
    previous = json.loads(inputs['previous_image'].read_text())
    coordinate_map = json.loads(inputs['coordinate_map'].read_text())
    intermediate_j = json.loads(inputs['intermediate_j'].read_text())
    assert census['raw_chain_pairs'] == 888
    assert census['X0_point_count_from_Hecke'] == 880
    assert previous['row_count'] == 872
    models = {row['label']: row for row in census['rows'] if row['label'] != 'generic'}
    assert set(models) == {'j0_base', 'j0_twist', 'j1728_base', 'j1728_twist'}
    kernel = load('kernel887_correction', inputs['kernel_transport'])
    forward = load('forward887_correction', inputs['forward_evaluator'])
    F = GF(P)
    K = GF(P**2, 'u')
    R = PolynomialRing(K, 'x')
    x = R.gen()
    zeta = K.multiplicative_generator()**((P**2 - 1)//3)
    assert zeta != 1 and zeta**3 == 1
    t0 = F(5)**pow(3, -1, P-1)
    assert t0**3 == 5
    t1728 = K(5).sqrt()
    assert t1728**2 == 5

    polynomials = {}
    for label, model in models.items():
        curve = EllipticCurve(F, model['curve_ainvs'])
        records = []
        for i, path2 in enumerate(model['two_paths']):
            poly2 = R(kernel.chain(curve, path2)[0].kernel_polynomial().monic())
            for j, path3 in enumerate(model['three_paths']):
                poly3 = R(kernel.chain(curve, path3)[0].kernel_polynomial().monic())
                assert poly2.degree() == 8 and poly3.degree() == 13
                records.append({'pair': (i, j), 'two': poly2, 'three': poly3})
        assert len(records) == 8
        polynomials[label] = records

    def equivalent(a, b, scalars):
        return any(b['two'] == a['two'](x / t).monic() and
                   b['three'] == a['three'](x / t).monic() for t in scalars)

    def orbits(label, scalars):
        entries = polynomials[label]
        unseen = set(range(len(entries)))
        result = []
        while unseen:
            representative = min(unseen)
            orbit = [k for k in range(len(entries))
                     if equivalent(entries[representative], entries[k], scalars)]
            assert set(orbit) <= unseen
            unseen.difference_update(orbit)
            result.append([list(entries[k]['pair']) for k in orbit])
        return result

    j0_base_orbits = orbits('j0_base', [zeta**k for k in range(3)])
    j0_twist_orbits = orbits('j0_twist', [zeta**k for k in range(3)])
    j1728_base_orbits = orbits('j1728_base', [K(1), -K(1)])
    j1728_twist_orbits = orbits('j1728_twist', [K(1), -K(1)])
    assert len(j0_base_orbits) == len(j0_twist_orbits) == 8
    assert len(j1728_base_orbits) == len(j1728_twist_orbits) == 4
    j0_cross = [(list(a['pair']), list(b['pair']))
                for a in polynomials['j0_base']
                for b in polynomials['j0_twist']
                if equivalent(a, b, [K(t0)*zeta**k for k in range(3)])]
    j1728_cross = [(list(a['pair']), list(b['pair']))
                   for a in polynomials['j1728_base']
                   for b in polynomials['j1728_twist']
                   if equivalent(a, b, [t1728, -t1728])]
    assert len(j0_cross) == 8
    assert len({tuple(a) for a, _ in j0_cross}) == 8
    assert len({tuple(b) for _, b in j0_cross}) == 8
    assert j1728_cross == []

    base_keep = {tuple(min(orbit)) for orbit in j1728_base_orbits}
    twist_keep = {tuple(min(orbit)) for orbit in j1728_twist_orbits}
    assert len(base_keep) == len(twist_keep) == 4
    rows = []
    removed = []
    for old_index, row in enumerate(previous['rows']):
        key = record_key(row)
        if row['source_label'] == 'j1728_base' and tuple(row['pair']) not in base_keep:
            removed.append({'previous_row': old_index, 'pair': row['pair'],
                            'B_point': row['B_candidates'][0]})
            continue
        assert len(row['B_candidates']) == 1 and row['B_candidates'][0] is not None
        rows.append({'source_ainvs': row['source_ainvs'],
                     'source_label': row['source_label'], 'pair': row['pair'],
                     'B_point': row['B_candidates'][0],
                     'previous_row': old_index})
    assert len(rows) == 868 and len(removed) == 4
    twist = models['j1728_twist']
    added = []
    for i, j in sorted(twist_keep):
        value = forward.one(P, twist['curve_ainvs'], twist['two_paths'][i],
                            twist['three_paths'][j], coordinate_map, intermediate_j)
        assert len(value['B_candidates']) == 1 and value['B_candidates'][0] is not None
        point = value['B_candidates'][0]
        new_row = {'source_ainvs': twist['curve_ainvs'], 'source_label': 'j1728_twist',
                   'pair': [i, j], 'B_point': point, 'previous_row': None}
        rows.append(new_row)
        added.append({'pair': [i, j], 'B_point': point,
                      'coordinate_counts': value['coordinate_counts'],
                      'frobenius_pair_count': value['frobenius_pair_count']})
    assert len(rows) == 872
    assert len({record_key(row) for row in rows}) == 872
    rows.sort(key=lambda row: (tuple(row['source_ainvs']), row['source_label'],
                               tuple(row['pair'])))
    shards = []
    for offset in range(0, len(rows), 250):
        path = HERE / f'corrected-{offset//250:02d}.json'
        block = rows[offset:offset+250]
        path.write_text(json.dumps(block, sort_keys=True, separators=(',', ':')) + '\n')
        shards.append({'file': path.name, 'rows': len(block),
                       'sha256': sha256(path.read_bytes()).hexdigest()})
    old_fibers = Counter(tuple(row['B_candidates'][0]) for row in previous['rows'])
    new_fibers = Counter(tuple(row['B_point']) for row in rows)
    assert len(old_fibers) == len(new_fibers) == 109
    old_hist = dict(sorted(Counter(old_fibers.values()).items()))
    new_hist = dict(sorted(Counter(new_fibers.values()).items()))
    assert old_hist == {6: 1, 7: 2, 8: 102, 9: 4}
    assert new_hist == {8: 109}
    result = {'status': 'COMPLETE_P887_AUTOMORPHISM_CORRECTION',
              'prime': P, 'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
              'source_code_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
              'raw_chain_pairs': census['raw_chain_pairs'],
              'Hecke_rational_points': census['X0_point_count_from_Hecke'],
              'rational_cusps': 8, 'corrected_noncuspidal_source_points': len(rows),
              'j0_base_orbits': j0_base_orbits, 'j0_twist_orbits': j0_twist_orbits,
              'j0_cross_matches': j0_cross,
              'j1728_base_orbits': j1728_base_orbits,
              'j1728_twist_orbits': j1728_twist_orbits,
              'j1728_cross_matches': j1728_cross,
              'removed_duplicate_base_rows': removed,
              'added_twist_orbits': added, 'corrected_shards': shards,
              'old_affine_B_image': len(old_fibers),
              'corrected_affine_B_image': len(new_fibers),
              'old_B_fiber_histogram': old_hist, 'corrected_B_fiber_histogram': new_hist,
              'corrected_full_B_image_with_cusp_identity': len(new_fibers) + 1}
    (HERE / 'result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in
                      ('status', 'corrected_noncuspidal_source_points',
                       'corrected_affine_B_image', 'corrected_B_fiber_histogram')},
                     sort_keys=True))


if __name__ == '__main__':
    main()
