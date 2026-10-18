"""Independent checked-Sage replay of native N41 phi join hits."""
import hashlib
import json
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


def enc(value):
    return sum(int(v) << i for i, v in enumerate(value.polynomial().list()))


def main(label):
    assert label in ('positive', 'public')
    cfg = json.loads((HERE / 'audit_protocol.json').read_text())
    for name, item in cfg['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    table = json.loads((BASE / 'table.json').read_text())
    source = json.loads((BASE / 'protocol.json').read_text())
    export = json.loads((HERE / 'export_result.json').read_text())
    receipt = json.loads((HERE / f'{label}_receipt.json').read_text())
    lines = (HERE / f'{label}.stdout').read_text().splitlines()
    assert receipt['stdout_sha256'] == sha(HERE / f'{label}.stdout')
    hits = [r.split() for r in lines if r.startswith('HIT ')]
    assert len(hits) == 1 and len(hits[0]) == 13
    ids = list(map(int, hits[0][1:9]))
    assert all(0 <= v < 60 for v in ids)

    onb = field.Onb(41)
    curve = curves.Curve(onb)
    P = PolynomialRing(GF(2), 'u')
    u = P.gen()
    K = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
    E = EllipticCurve(K, [1, 0, 0, 0, 1])
    def dec(value):
        return K(P([(value >> i) & 1 for i in range(41)]))
    alpha = dec(export['isomorphism_gamma1'])
    assert sum((alpha**i for i in range(42) if export['minpoly_gamma1'] >> i & 1), K.zero()) == 0
    gamma = [K.zero(), alpha]
    for i in range(1, 41):
        gamma.append(alpha*gamma[i]+gamma[i-1])
    def image(a):
        bits = onb.toCoords(a)
        out = K.zero()
        while bits:
            bit = bits & -bits
            out += gamma[bit.bit_length()]
            bits ^= bit
        return out
    assert image(onb.one()) == K.one()
    def mapped(point):
        return E(image(point[0]), image(point[1]))

    basis, codes = table['basis_coordinate_masks'], table['valid_codes']
    def leaf(code, position, sign):
        mask = 0
        for i, value in enumerate(basis):
            if code >> i & 1:
                mask ^= value
        phi = onb.frob(onb.fromCoords(mask), position)
        x = onb.add(onb.inv(phi), onb.one())
        point = curve.pointFromX(x)
        assert point is not None
        return curve.neg(point) if sign else point

    orbit_keys = {}
    for code in codes:
        projected = curve.mul(leaf(code, 0, 0), 4)
        orbit = []
        for shift in range(41):
            value = curve.frob(projected, shift)
            orbit.extend((value, curve.neg(value)))
        orbit_keys[code] = min(tuple(onb.toCoords(v) for v in q) for q in orbit)
    col_map = {key: i for i, key in enumerate(sorted(set(orbit_keys.values())))}
    assert len(col_map) == 26

    rows = {}
    for line in (HERE / f'{label}_input.tsv').read_text().splitlines():
        parts = line.split()
        if parts[0] == 'PHI41':
            target_xy = tuple(map(int, parts[3:5]))
            assert parts[1:3] == ['8', '60']
            continue
        assert parts[0] == 'S' and len(parts) == 8
        slot, state_id, code, sign, column, x, y = map(int, parts[1:])
        assert code == codes[state_id//2] and sign == state_id%2
        assert column == col_map[orbit_keys[code]]
        point = leaf(code, slot, sign)
        mapped_point = mapped(point)
        assert (enc(mapped_point[0]), enc(mapped_point[1])) == (x, y)
        rows[(slot, state_id)] = (code, sign, column, point)
    assert len(rows) == 480
    target = E(dec(target_xy[0]), dec(target_xy[1]))
    assert target != E(0)
    selected = [rows[(slot, ids[slot])] for slot in range(8)]
    assert len({row[2] for row in selected}) == 8
    total = None
    for row in selected:
        total = curve.add(total, row[3])
    assert total is not None and mapped(total) == target
    subgroup_target = tuple(onb.fromCoords(v) for v in source['target_coordinates'])
    if label == 'public':
        endpoint = tuple(onb.fromCoords(v) for v in source['endpoint_coordinates'])
        assert total == endpoint and curve.mul(total, 4) == subgroup_target
    else:
        assert target_xy == tuple(export['positive_point'])
    result = {'status': 'PASS_INDEPENDENT_N41_PHI_EIGHT_LEAF_REPLAY',
              'arm': label, 'candidate_id': None, 'curve_id': cfg['curve_id'],
              'state_ids': ids, 'leaf_codes': [r[0] for r in selected],
              'leaf_signs': [r[1] for r in selected],
              'folded_columns': [r[2] for r in selected],
              'sum_point': list(target_xy),
              'subgroup_point': [enc(v) for v in mapped(subgroup_target)[:2]] if label == 'public' else None,
              'input_sha256': sha(HERE / f'{label}_input.tsv'),
              'stdout_sha256': sha(HERE / f'{label}.stdout'),
              'audit_protocol_sha256': sha(HERE / 'audit_protocol.json')}
    (HERE / f'{label}_audit.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == '__main__':
    assert len(sys.argv) == 2
    main(sys.argv[1])
