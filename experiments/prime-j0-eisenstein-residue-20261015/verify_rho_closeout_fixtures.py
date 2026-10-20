#!/usr/bin/env python3
"""Independently replay frozen Q and aG+bQ fixtures with affine arithmetic."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from check_secp256k1_tau_generator import G, N, add, mul

HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = HERE / 'rho-closeout-fixtures'


def encoded(point: tuple[int, int]) -> str:
    return ':'.join(f'{coordinate:064x}' for coordinate in point)


def verify(root: Path, sample: bool) -> dict:
    manifest_bytes = (root / 'manifest.json').read_bytes()
    manifest = json.loads(manifest_bytes)
    assert manifest['schema'] == 'rho-closeout-fixtures-v1'
    assert manifest['curve'] == 'secp256k1'
    assert manifest['counts'] == [1, 8, 32, 128]
    assert len(manifest['fixtures']) == 32
    checked = 0
    for entry in manifest['fixtures']:
        raw = (root / entry['path']).read_bytes()
        assert sha256(raw).hexdigest() == entry['sha256']
        fixture = json.loads(raw)
        q = tuple(int(word, 16) for word in fixture['q_hex'].split(':'))
        assert encoded(mul(int(entry['q_scalar_hex'], 16), G)) == fixture['q_hex']
        assert entry['q_hex'] == fixture['q_hex']
        assert len(fixture['cases']) == 128
        indices = (0, 7, 31, 127) if sample else range(128)
        for index in indices:
            row = fixture['cases'][index]
            assert len(row['a_hex']) == len(row['b_hex']) == 64
            point = add(mul(int(row['a_hex'], 16) % N, G),
                        mul(int(row['b_hex'], 16) % N, q))
            assert point is not None
            assert encoded(point) == row['point_hex']
            checked += 1
        assert entry['first_point_hex'] == fixture['cases'][0]['point_hex']
        assert entry['last_point_hex'] == fixture['cases'][-1]['point_hex']
    return {'schema': 'rho-closeout-fixture-verification-v1',
            'manifest_sha256': sha256(manifest_bytes).hexdigest(),
            'q_points_verified': 32, 'rows_verified': checked,
            'total_rows': 32 * 128, 'scope': 'selected_rows' if sample else 'all_rows',
            'status': 'pass'}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    parser.add_argument('--sample', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = verify(args.root, args.sample)
    rendered = json.dumps(result, sort_keys=True, indent=2) + '\n'
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end='')


if __name__ == '__main__':
    main()
