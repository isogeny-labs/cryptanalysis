#!/usr/bin/env python3
"""Generate the independent same-point secp256k1 replay for mixed-77."""
import hashlib
import json
from pathlib import Path
import sys

from cryptography.hazmat.primitives.asymmetric import ec

ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
CURVE = ec.SECP256K1()


def point(scalar: int) -> str:
    assert 0 < scalar < ORDER
    numbers = ec.derive_private_key(scalar, CURVE).public_key().public_numbers()
    return f'{numbers.x:064x}:{numbers.y:064x}'


def digest_scalar(label: bytes) -> int:
    return int.from_bytes(hashlib.sha256(label).digest(), 'big')


def main(output: Path) -> None:
    q_scalar = digest_scalar(b'mixed77-independent-Q-v1') % (ORDER - 1) + 1
    cases = []
    for index in range(128):
        a = digest_scalar(f'mixed77-a-{index}'.encode()) % ORDER
        b = digest_scalar(f'mixed77-b-{index}'.encode()) % ORDER
        combined = (a + b * q_scalar) % ORDER
        assert combined != 0
        cases.append({'a_hex': f'{a:x}', 'b_hex': f'{b:x}',
                      'point_hex': point(combined)})
    fixture = {'q_hex': point(q_scalar), 'cases': cases}
    output.write_text(json.dumps(fixture, sort_keys=True,
                                 separators=(',', ':')))


if __name__ == '__main__':
    assert len(sys.argv) == 2
    main(Path(sys.argv[1]))
