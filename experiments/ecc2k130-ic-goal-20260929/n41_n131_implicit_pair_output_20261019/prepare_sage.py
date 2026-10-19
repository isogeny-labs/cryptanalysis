"""Freeze exact pair-output controls and linearized product bases."""
import hashlib
import json
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def field(n):
    ring = PolynomialRing(GF(2), 'u')
    u = ring.gen()
    modulus = u**41 + u**3 + 1 if n == 41 else u**131 + u**13 + u**2 + u + 1
    return GF(2**n, name='u', modulus=modulus)


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def halftrace(value, n):
    result = value
    power = value
    for _ in range((n - 1) // 2):
        power = power**4
        result += power
    return result if result**2 + result == value else None


def roots(p, c, h, n):
    if p == 0:
        return []
    a = c
    b = p
    d = h
    if a == 0:
        return [d / b]
    h = halftrace(a * d / b**2, n)
    if h is None:
        return []
    scale = b / a
    return [scale * h, scale * (h + 1)]


def prepare_case(n, seed, positions, rotation, fixture_code, fixture_output):
    f = field(n)
    decode = f.from_integer
    s = decode(seed << 1)
    srot = s**(1 << rotation)
    source_half = halftrace(s, n)
    assert source_half is not None
    h0 = source_half**2
    c0 = 1 + h0
    hrot = h0**(1 << rotation)
    crot = c0**(1 << rotation)
    source = [decode(1 << (bit + 1)) for bit in positions]
    basis = [(w**2 + s * w)**(1 << rotation) for w in source]
    assert len(set(map(encode, basis))) == len(basis)

    def value(code):
        w = sum((source[i] for i in range(len(source)) if (code >> i) & 1), f.zero())
        return w, (w**2 + s * w)**(1 << rotation)

    def valid(w):
        other = w + s
        return (w != 0 and other != 0 and w.trace() == 0 and
                other.trace() == 0 and (1 / w).trace() == 0 and
                (1 / other).trace() == 0)

    positives = []
    for code in range(1 << len(positions)):
        w, p = value(code)
        if not valid(w):
            continue
        choices = roots(p, crot, hrot, n)
        assert len(choices) == 2
        c = choices[0]
        assert c != 0 and crot*c**2 + p*c + hrot == 0
        positives.append((encode(c), code))
        if len(positives) == 64:
            break
    assert len(positives) == 64
    w, p = value(fixture_code)
    assert valid(w)
    if fixture_output is None:
        fixture_output = encode(roots(p, crot, hrot, n)[0])
    assert fixture_output in [encode(c) for c in roots(p, crot, hrot, n)]
    if (fixture_output, fixture_code) not in positives:
        positives[0] = (fixture_output, fixture_code)
    assert len(set(positives)) == 64
    path = HERE / f'input_n{n}.txt'
    samples = 100000 if n == 41 else 200000
    with path.open('x') as out:
        out.write(f'PAIR {n} {len(positions)} {encode(crot)} {encode(hrot)} {samples} 898618\n')
        for b in basis:
            out.write(f'{encode(b)}\n')
        out.write(f'POS {len(positives)}\n')
        for c, code in positives:
            out.write(f'{c} {code}\n')
    return {'field_degree': n, 'seed_mask': seed, 'rotation': rotation,
            'quadratic_c': encode(crot), 'quadratic_h': encode(hrot),
            'free_positions': positions, 'positive_controls': len(positives),
            'fixture_code': fixture_code, 'fixture_output': fixture_output,
            'samples': samples, 'path': str(path), 'sha256': sha(path)}


def main():
    cfg = json.loads((HERE / 'prepare_protocol_v2.json').read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_IMPLICIT_PAIR_PREPARATION_V2'
    assert sha(__file__) == cfg['script_sha256']
    for rec in cfg['sources'].values():
        assert sha(rec['path']) == rec['sha256']
    n131_control = json.loads((ROOT / 'n41_n131_fivepair_w9_w29_20261017' /
                               'n131_control_3p2.json').read_text())
    assert n131_control['curve_id'] == 'EC1N131Ckb1heb5f1998f20b'
    pair = n131_control['pairs'][0]
    assert pair['masks'] == [3, 898617] and n131_control['rotations'][0] == 0
    start = time.monotonic()
    cases = [prepare_case(41, 56, [0, 1, 2, 3, 4, 6, 7, 8, 9, 10], 12,
                          253, None)]
    cases.append(prepare_case(131, 898618,
        [i for i in range(29) if i != (898618).bit_length() - 1], 0,
        3, pair['output_reciprocal']))
    result = {'status': 'PASS_IMPLICIT_PAIR_PREPARATION', 'candidate_id': None,
              'cases': cases, 'wall_seconds': time.monotonic() - start,
              'protocol_sha256': sha(HERE / 'prepare_protocol_v2.json'),
              'script_sha256': sha(__file__)}
    (HERE / 'prepare_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
