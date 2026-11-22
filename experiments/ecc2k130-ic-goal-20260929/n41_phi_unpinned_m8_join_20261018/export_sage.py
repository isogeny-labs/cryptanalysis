"""Export eight unpinned N41 phi slots in an independently checked field basis."""
import hashlib
import json
import random
import sys
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'n41_phi_second_link_control_20261009'
sys.path.insert(0, str(HERE.parents[2] / 'ecc2k130/codegen'))
import curves
import field


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def main():
    cfg_path = HERE / 'export_protocol.json'
    cfg = json.loads(cfg_path.read_text())
    for name, item in cfg['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    source = json.loads((BASE / 'protocol.json').read_text())
    table = json.loads((BASE / 'table.json').read_text())
    assert source['domain_dimension'] == 6 and len(table['valid_codes']) == 30
    onb = field.Onb(41)
    curve = curves.Curve(onb)
    poly_ring = PolynomialRing(GF(2), 'u')
    u = poly_ring.gen()
    K = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
    E = EllipticCurve(K, [1, 0, 0, 0, 1])
    c_min = onb.minPolyOfC()
    root_poly = PolynomialRing(K, 'v')
    v = root_poly.gen()
    roots = [r for r, _multiplicity in
             sum((K.one() * v**i for i in range(42) if (c_min >> i) & 1),
                 root_poly.zero()).roots()]
    assert len(roots) == 41
    alpha = min(roots, key=encode)
    gamma = [K.zero(), alpha]
    for i in range(1, 41):
        gamma.append(alpha * gamma[i] + gamma[i-1])

    def image(a):
        bits = onb.toCoords(a)
        value = K.zero()
        while bits:
            bit = bits & -bits
            value += gamma[bit.bit_length()]
            bits ^= bit
        return value

    assert image(onb.one()) == K.one()
    rng = random.Random(41018)
    for _ in range(128):
        a, b = onb.fromCoords(rng.getrandbits(41)), onb.fromCoords(rng.getrandbits(41))
        assert image(onb.add(a, b)) == image(a) + image(b)
        assert image(onb.mul(a, b)) == image(a) * image(b)
        assert image(onb.sqr(a)) == image(a)**2

    basis, codes = table['basis_coordinate_masks'], table['valid_codes']
    def leaf(code, position):
        mask = 0
        for bit, basis_mask in enumerate(basis):
            if code >> bit & 1:
                mask ^= basis_mask
        phi = onb.frob(onb.fromCoords(mask), position)
        point = curve.pointFromX(onb.add(onb.inv(phi), onb.one()))
        assert point is not None
        return point

    def mapped(point):
        return E(image(point[0]), image(point[1]))

    orbit_keys = {}
    for code in codes:
        projected = curve.mul(leaf(code, 0), 4)
        assert projected is not None
        orbit = []
        for k in range(41):
            p = curve.frob(projected, k)
            orbit.extend((p, curve.neg(p)))
        key = min(tuple(onb.toCoords(value) for value in p) for p in orbit)
        orbit_keys[code] = key
    key_to_column = {key: i for i, key in enumerate(sorted(set(orbit_keys.values())))}
    assert len(key_to_column) == 26

    slots = []
    for position in range(8):
        rows = []
        for code in codes:
            p = leaf(code, position)
            for sign, q in enumerate((p, curve.neg(p))):
                epoint = mapped(q)
                assert epoint != E(0)
                rows.append((code, sign, key_to_column[orbit_keys[code]],
                             encode(epoint[0]), encode(epoint[1]), q))
        assert len(rows) == 60
        slots.append(rows)
    for a, b in ((slots[0][0], slots[1][3]), (slots[2][10], slots[3][17])):
        source_sum = curve.add(a[5], b[5])
        assert mapped(source_sum) == mapped(a[5]) + mapped(b[5])

    endpoint = tuple(onb.fromCoords(v) for v in source['endpoint_coordinates'])
    public = tuple(onb.fromCoords(v) for v in source['target_coordinates'])
    assert curve.mul(endpoint, 4) == public
    assert mapped(endpoint) != E(0)
    selected, used = [], set()
    for slot in slots:
        choice = next(i for i, row in enumerate(slot) if row[2] not in used)
        selected.append(choice)
        used.add(slot[choice][2])
    positive = None
    for position, state_id in enumerate(selected):
        positive = curve.add(positive, slots[position][state_id][5])
    assert positive is not None

    def write_input(path, target):
        ex, ey = mapped(target)[:2]
        with path.open('x') as out:
            out.write(f'PHI41 8 60 {encode(ex)} {encode(ey)}\n')
            for position, slot in enumerate(slots):
                for state_id, (code, sign, col, x, y, _q) in enumerate(slot):
                    out.write(f'S {position} {state_id} {code} {sign} {col} {x} {y}\n')

    write_input(HERE / 'positive_input.tsv', positive)
    write_input(HERE / 'public_input.tsv', endpoint)
    result = {'status': 'PASS_N41_PHI_UNPINNED_EIGHT_SLOT_EXPORT',
              'candidate_id': None, 'curve_id': cfg['curve_id'],
              'minpoly_gamma1': c_min, 'isomorphism_gamma1': encode(alpha),
              'codes_per_slot': len(codes), 'signed_states_per_slot': 60,
              'folded_columns': len(key_to_column),
              'positive_state_ids': selected,
              'positive_point': [encode(v) for v in mapped(positive)[:2]],
              'public_endpoint': [encode(v) for v in mapped(endpoint)[:2]],
              'public_subgroup_target': [encode(v) for v in mapped(public)[:2]],
              'positive_input_sha256': sha(HERE / 'positive_input.tsv'),
              'public_input_sha256': sha(HERE / 'public_input.tsv'),
              'export_protocol_sha256': sha(cfg_path)}
    (HERE / 'export_result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
