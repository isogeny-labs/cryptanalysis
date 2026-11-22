"""Independent polynomial-field Sage replay of every adjacent image representative."""

import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, Matrix, PolynomialRing

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / 'audit_protocol.json').read_text())
    census = json.loads((HERE / 'census_result.json').read_text())
    source = Path(protocol['source_receipt'])
    assert sha(source) == protocol['source_receipt_sha256']
    assert sha(HERE / 'census_result.json') == protocol['census_result_sha256']
    assert sha(__file__) == protocol['auditor_source_sha256']
    receipt = json.loads(source.read_text())
    started = time.monotonic()
    n = 131
    bitpoly = (1 << 131) | (1 << 13) | (1 << 2) | (1 << 1) | 1
    ring = PolynomialRing(GF(2), 'z')
    modulus = ring([bitpoly >> i & 1 for i in range(n + 1)])
    field = GF(2**n, name='z', modulus=modulus)
    zeta = field.multiplicative_generator() ** ((2**n - 1) // 263)
    assert zeta != 1 and zeta**263 == 1
    basis = [zeta**i + zeta**(263-i) for i in range(1, n+1)]
    assert sum(basis, field(0)) == 1
    inverse = Matrix(GF(2), [b.list() for b in basis]).transpose().inverse()
    dual = [sum(int(bit) << j for j, bit in enumerate(row))
            for row in inverse.rows()]

    def decode(mask):
        result = field(0)
        value = int(mask)
        while value:
            low = value & -value
            result += basis[low.bit_length()-1]
            value ^= low
        return result

    def encode(value):
        polybits = sum(int(bit) << i for i, bit in enumerate(value.list()))
        return sum(((polybits & row).bit_count() & 1) << i
                   for i, row in enumerate(dual))

    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    order = int(protocol['subgroup_order'])
    coefficient = (1 + int(protocol['frobenius_eigenvalue'])) % order
    images = []
    scalar_checks = 0
    for index, (cx, cy) in enumerate(receipt['representatives']):
        point = curve(decode(cx), decode(cy))
        frob = curve(point[0]**2, point[1]**2)
        image = point + frob
        assert image != curve(0)
        assert image[0] == point[0] + 1/point[0]
        images.append(encode(image[0]))
        if index in (0, 1, 9, 64, 131, 1023, 2048, 4133):
            assert order*point == curve(0)
            assert image == coefficient*point
            scalar_checks += 1
        if (index & 63) == 0:
            assert time.monotonic() - started < protocol['wall_cap_seconds']
            assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < protocol['rss_cap_bytes']
    digest = hashlib.sha256(b''.join(
        x.to_bytes(17, 'little') for x in images)).hexdigest()
    assert digest == census['representative_image_x_sha256']
    print(json.dumps({
        'kind': 'n131_d13_adjacent_image_independent_sage_audit',
        'status': 'PASS_ALL_REPRESENTATIVES',
        'protocol_sha256': sha(HERE / 'audit_protocol.json'),
        'representatives_checked': len(images),
        'subgroup_scalar_checks': scalar_checks,
        'image_x_digest': digest,
        'wall_seconds': time.monotonic() - started,
        'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }, sort_keys=True))


if __name__ == '__main__':
    main()
