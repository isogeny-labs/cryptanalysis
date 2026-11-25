"""Replay special-kernel equivalence and missing twist images from raw chains."""
import importlib.util
import json
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'
from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
P = 887


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    files = {name: Path(entry['path']) for name, entry in protocol['inputs'].items()}
    assert all(sha256(files[name].read_bytes()).hexdigest() ==
               entry['sha256'] for name, entry in protocol['inputs'].items())
    result = json.loads((HERE / 'result.json').read_text())
    census = json.loads(files['census'].read_text())
    models = {record['label']: record for record in census['rows']
              if record['label'] != 'generic'}
    kernel = module('independent_kernel887', files['kernel_transport'])
    forward = module('independent_forward887', files['forward_evaluator'])
    F = GF(P)
    K = GF(P**2, 'v')
    ring = PolynomialRing(K, 'X')
    X = ring.gen()
    omega = K.multiplicative_generator()**((P**2 - 1)//3)
    c0 = F(5)**pow(3, -1, P-1)
    c1728 = K(5).sqrt()
    assert omega**3 == 1 and omega != 1
    assert c0**3 == 5 and c1728**2 == 5
    kernels = {}
    for label, record in models.items():
        curve = EllipticCurve(F, record['curve_ainvs'])
        kernels[label] = {}
        for i, two in enumerate(record['two_paths']):
            p2 = ring(kernel.chain(curve, two)[0].kernel_polynomial().monic())
            for j, three in enumerate(record['three_paths']):
                p3 = ring(kernel.chain(curve, three)[0].kernel_polynomial().monic())
                kernels[label][(i, j)] = (p2, p3)
    def maps_to(a, b, scalar):
        return all(target == source(X/scalar).monic()
                   for source, target in zip(a, b))
    def verify_orbits(label, orbits, scalars):
        covered = set()
        for orbit in orbits:
            representative = tuple(orbit[0])
            for entry in orbit:
                pair = tuple(entry)
                assert pair not in covered
                assert any(maps_to(kernels[label][representative],
                                   kernels[label][pair], s) for s in scalars)
                covered.add(pair)
        assert covered == set(kernels[label])
        return len(orbits)
    assert verify_orbits('j0_base', result['j0_base_orbits'],
                         [omega**k for k in range(3)]) == 8
    assert verify_orbits('j0_twist', result['j0_twist_orbits'],
                         [omega**k for k in range(3)]) == 8
    assert verify_orbits('j1728_base', result['j1728_base_orbits'],
                         [K(1), -K(1)]) == 4
    assert verify_orbits('j1728_twist', result['j1728_twist_orbits'],
                         [K(1), -K(1)]) == 4
    j0_matches = []
    for a, pa in kernels['j0_base'].items():
        for b, pb in kernels['j0_twist'].items():
            if any(maps_to(pa, pb, K(c0)*omega**k) for k in range(3)):
                j0_matches.append((a, b))
    assert len(j0_matches) == 8
    assert {a for a, _ in j0_matches} == set(kernels['j0_base'])
    assert {b for _, b in j0_matches} == set(kernels['j0_twist'])
    j1728_matches = [(a, b) for a, pa in kernels['j1728_base'].items()
                     for b, pb in kernels['j1728_twist'].items()
                     if any(maps_to(pa, pb, scalar)
                            for scalar in (c1728, -c1728))]
    assert j1728_matches == []
    coordinate = json.loads(files['coordinate_map'].read_text())
    intermediate = json.loads(files['intermediate_j'].read_text())
    twist = models['j1728_twist']
    outputs = []
    for record in result['added_twist_orbits']:
        i, j = record['pair']
        value = forward.one(P, twist['curve_ainvs'], twist['two_paths'][i],
                            twist['three_paths'][j], coordinate, intermediate)
        assert value['B_candidates'] == [record['B_point']]
        outputs.append(record['B_point'])
    out = {'status': 'PASS_INDEPENDENT_SPECIAL_ORBIT_REPLAY',
           'j0_base_orbits': 8, 'j0_twist_orbits': 8,
           'j0_cross_model_pairs': len(j0_matches),
           'j1728_base_orbits': 4, 'j1728_twist_orbits': 4,
           'j1728_cross_model_pairs': len(j1728_matches),
           'twist_map_outputs_replayed': len(outputs),
           'twist_B_points': outputs}
    (HERE / 'orbit_audit.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
