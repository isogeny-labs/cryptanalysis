#!/usr/bin/env python3
"""Freeze independent secp256k1 Q points and same-point restart fixtures."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import ec

ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
CURVE = ec.SECP256K1()
COUNTS = (1, 8, 32, 128)


def scalar(seed: bytes, label: str) -> int:
    return 1 + int.from_bytes(sha256(seed + label.encode()).digest(), 'big') % (ORDER - 1)


def point(k: int) -> str:
    assert 0 < k < ORDER
    xy = ec.derive_private_key(k, CURVE).public_key().public_numbers()
    return f'{xy.x:064x}:{xy.y:064x}'


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed-hex', required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    seed = bytes.fromhex(args.seed_hex)
    if len(seed) != 32:
        parser.error('--seed-hex must be 32 bytes')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {'schema': 'rho-closeout-fixtures-v1', 'seed_hex': args.seed_hex,
                'curve': 'secp256k1', 'counts': list(COUNTS),
                'input_law': 'SHA-256(seed || ASCII label), reduced to nonzero subgroup scalar',
                'fixtures': []}
    for qi in range(32):
        q_scalar = scalar(seed, f'/q/{qi}')
        q_hex = point(q_scalar)
        cases = []
        for j in range(128):
            a = scalar(seed, f'/a/{qi}/{j}')
            b = scalar(seed, f'/b/{qi}/{j}')
            result = (a + b * q_scalar) % ORDER
            if result == 0:
                raise ValueError(f'identity output at Q {qi}, case {j}')
            cases.append({'a_hex': f'{a:064x}', 'b_hex': f'{b:064x}',
                          'point_hex': point(result)})
        fixture = {'q_hex': q_hex, 'cases': cases}
        path = args.output_dir / f'q{qi:02d}.json'
        content = canonical_bytes(fixture)
        path.write_bytes(content)
        manifest['fixtures'].append({'path': path.name, 'sha256': sha256(content).hexdigest(),
                                     'q_hex': q_hex, 'q_scalar_hex': f'{q_scalar:x}',
                                     'first_point_hex': cases[0]['point_hex'],
                                     'last_point_hex': cases[-1]['point_hex']})
    (args.output_dir / 'manifest.json').write_bytes(canonical_bytes(manifest))
    print(json.dumps({'fixture_count': len(manifest['fixtures']),
                      'manifest_sha256': sha256(canonical_bytes(manifest)).hexdigest()},
                     sort_keys=True))


if __name__ == '__main__':
    main()
