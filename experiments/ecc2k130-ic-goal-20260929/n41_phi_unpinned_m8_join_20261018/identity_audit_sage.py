"""Append-only correction of the curve identity in the first-run receipts."""
import hashlib
import json
import sys
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'n41_phi_second_link_control_20261009/protocol.json'
sys.path.insert(0, str(HERE.parents[2] / 'ecc2k130/codegen'))
import curves
import field


def digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'),
                     ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = json.loads(SOURCE.read_text())
    old = json.loads((HERE / 'export_result.json').read_text())
    assert source['curve_id'] is None
    assert old['curve_id'] == 'EC1N41Ckb1h7d5e80d3c4d0'
    onb = field.Onb(41)
    source_curve = curves.Curve(onb)
    ring = PolynomialRing(GF(2), 'u')
    u = ring.gen()
    K = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
    E = EllipticCurve(K, [1, 0, 0, 0, 1])
    vring = PolynomialRing(K, 'v')
    v = vring.gen()
    c_min = onb.minPolyOfC()
    poly = sum((K.one() * v**i for i in range(42) if c_min >> i & 1), vring.zero())
    alpha = min((root for root, _ in poly.roots()), key=encode)
    assert encode(alpha) == old['isomorphism_gamma1']
    gamma = [K.zero(), alpha]
    for i in range(1, 41):
        gamma.append(alpha * gamma[i] + gamma[i - 1])

    def image(value):
        bits = onb.toCoords(value)
        out = K.zero()
        while bits:
            bit = bits & -bits
            out += gamma[bit.bit_length()]
            bits ^= bit
        return out

    def point(values):
        return tuple(onb.fromCoords(int(value)) for value in values)

    def mapped(values):
        return E(image(values[0]), image(values[1]))

    generator = point(source['generator_coordinates'])
    subgroup_target = point(source['target_coordinates'])
    raw_endpoint = point(source['endpoint_coordinates'])
    r = source['subgroup_order']
    assert source_curve.mul(generator, r) is None
    assert source_curve.mul(subgroup_target, r) is None
    assert source_curve.mul(raw_endpoint, 4) == subgroup_target
    g = mapped(generator)
    q = mapped(subgroup_target)
    endpoint = mapped(raw_endpoint)
    assert r * g == r * q == E(0) and 4 * endpoint == q
    assert [encode(v) for v in q[:2]] == old['public_subgroup_target']
    assert [encode(v) for v in endpoint[:2]] == old['public_endpoint']
    field_record = {
        'p': 2, 'n': 41, 'basis': 'polynomial',
        'defining_polynomial_int': (1 << 41) | (1 << 3) | 1,
        'element_encoding': 'nonnegative little-endian polynomial coefficient bit mask'}
    curve_record = {
        'model': 'y^2+x*y=x^3+1',
        'coefficients': {'a1': 1, 'a2': 0, 'a3': 0, 'a4': 0, 'a6': 1},
        'curve_order': 4 * r, 'trace': (1 << 41) + 1 - 4 * r,
        'r': r, 'cofactor': 4, 'G': [encode(v) for v in g[:2]],
        'target_group': 'prime_order_r_subgroup'}
    curve_id = 'EC1N41Ckb1h' + digest({'field': field_record, 'curve': curve_record})[:12]
    assert curve_id != old['curve_id']
    result = {
        'status': 'PASS_CURVE_IDENTITY_CORRECTION',
        'original_curve_id': old['curve_id'], 'corrected_curve_id': curve_id,
        'source_curve_id': source['curve_id'],
        'field': field_record, 'curve': curve_record,
        'source_generator_onb_coordinates': source['generator_coordinates'],
        'source_target_onb_coordinates': source['target_coordinates'],
        'source_protocol_sha256': sha(SOURCE),
        'export_result_sha256': sha(HERE / 'export_result.json'),
        'public_input_sha256': sha(HERE / 'public_input.tsv'),
        'public_receipt_sha256': sha(HERE / 'public_receipt.json'),
        'public_audit_sha256': sha(HERE / 'public_audit.json'),
        'row_result_sha256': sha(HERE / 'row_result.json')}
    output = HERE / 'identity_correction.json'
    with output.open('x') as handle:
        json.dump(result, handle, sort_keys=True, indent=2)
        handle.write('\n')
    print(json.dumps({'status': result['status'], 'corrected_curve_id': curve_id,
                      'generator': curve_record['G']}, sort_keys=True))


if __name__ == '__main__':
    main()
