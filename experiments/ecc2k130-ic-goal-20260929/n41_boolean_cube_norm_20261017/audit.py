"""Independent integer-field replay of Boolean-cube norm and ANF density."""
import hashlib
import itertools
import json
import resource
import signal
import struct
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
FLATS = ROOT / 'n41_valid_affine_flat_target_20261017'
POLY = (1 << 41) | (1 << 3) | 1
MASK = (1 << 41) - 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (BASE / name).open('x') as out:
        json.dump(value, out, sort_keys=True, indent=2)
        out.write('\n')


def sources():
    return {'script': sha(Path(__file__)), 'producer_result': sha(BASE / 'result.json'),
            'producer_protocol': sha(BASE / 'protocol.json'),
            'flats': sha(FLATS / 'result.json'),
            'witness_grid': sha(FLATS / 'grid_witness.bin'),
            'negative_grid': sha(FLATS / 'grid_negative.bin')}


def freeze():
    result = json.loads((BASE / 'result.json').read_text())
    assert result['status'] == 'PASS_N41_BOOLEAN_CUBE_NORM_SCREEN'
    save('audit_protocol.json', {'status': 'FROZEN_INDEPENDENT_BOOLEAN_NORM_REPLAY',
         'worker_count': 1, 'alarm_seconds': 120,
         'source_sha256': sources()})


def mul(a, b):
    result = 0
    while b:
        if b & 1:
            result ^= a
        b >>= 1
        a <<= 1
        if a & (1 << 41):
            a ^= POLY
    return result & MASK


def cube_codes(anchor, directions):
    return [anchor ^ (directions[0] if i & 1 else 0)
            ^ (directions[1] if i & 2 else 0)
            ^ (directions[2] if i & 4 else 0) for i in range(8)]


def main():
    signal.alarm(120)
    start = time.monotonic_ns()
    protocol = json.loads((BASE / 'audit_protocol.json').read_text())
    assert protocol['status'] == 'FROZEN_INDEPENDENT_BOOLEAN_NORM_REPLAY'
    assert protocol['source_sha256'] == sources()
    original = json.loads((BASE / 'result.json').read_text())
    flats = json.loads((FLATS / 'result.json').read_text())
    allowed = flats['covered_masks']
    # The grid uses the 40-mask order from the source geometry, not covered_masks.
    geometry = json.loads((ROOT / 'n41_w8_fixed_sum_table_20261009/geometry.json').read_text())
    all_masks = sorted(geometry['permitted_canonical_a'])
    assert len(all_masks) == 40 and set(allowed) <= set(all_masks)
    index = {code: i for i, code in enumerate(all_masks)}
    rows = []
    for row in original['panels']:
        name = row['panel']
        cube = [cube_codes(*flats['canonical_bases'][i])
                for i in row['flat_indices']]
        assert cube == row['source_codes']
        grid = (FLATS / f'grid_{name}.bin').read_bytes()
        direct = [struct.unpack_from('<Q', grid, 8*(index[cube[0][i]]*1600 +
                  index[cube[1][j]]*40 + index[cube[2][k]]))[0]
                  for i, j, k in itertools.product(range(8), repeat=3)]
        assert hashlib.sha256(b''.join(v.to_bytes(8, 'little') for v in direct)).hexdigest() == \
            row['direct_values_sha256']
        anf = [0] * 512
        for (i, j, k), value in zip(itertools.product(range(8), repeat=3), direct):
            anf[i | j << 3 | k << 6] = value
        for bit in range(9):
            for index_value in range(512):
                if index_value >> bit & 1:
                    anf[index_value] ^= anf[index_value ^ (1 << bit)]
        polynomial = {i: value for i, value in enumerate(anf) if value}
        assert len(polynomial) == row['initial_anf_terms']
        stages = []
        for bit in range(8, -1, -1):
            lower = {m: v for m, v in polynomial.items() if not (m >> bit & 1)}
            upper = {m ^ (1 << bit): v for m, v in polynomial.items() if m >> bit & 1}
            next_polynomial = {}
            for mask, value in lower.items():
                next_polynomial[mask] = mul(value, value)
            operations = 0
            for m0, v0 in lower.items():
                for m1, v1 in upper.items():
                    key = m0 | m1
                    next_polynomial[key] = next_polynomial.get(key, 0) ^ mul(v0, v1)
                    operations += 1
            polynomial = {mask: value for mask, value in next_polynomial.items() if value}
            stages.append({'eliminated_bit': bit, 'input_terms': len(lower)+len(upper),
                           'lower_terms': len(lower), 'upper_terms': len(upper),
                           'output_terms': len(polynomial),
                           'field_multiplications': operations,
                           'field_squarings': len(lower)})
        assert set(polynomial) <= {0}
        norm = polynomial.get(0, 0)
        direct_product = 1
        for value in direct:
            direct_product = mul(direct_product, value)
        assert norm == direct_product == row['norm_value']
        zeros = [i for i, value in enumerate(direct) if value == 0]
        assert zeros == row['zero_positions']
        for expected, actual in zip(row['norm_stages'], stages):
            for key, value in actual.items():
                assert expected[key] == value, (name, row['flat_indices'], key)
        rows.append({'panel': name, 'flat_indices': row['flat_indices'],
                     'initial_anf_terms': len(anf)-anf.count(0),
                     'zero_positions': zeros, 'norm_value': norm,
                     'norm_stages': stages})
    result = {'status': 'PASS_INDEPENDENT_BOOLEAN_CUBE_NORM_REPLAY',
              'panels': rows, 'elapsed_ns': time.monotonic_ns()-start,
              'peak_self_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'protocol_sha256': sha(BASE / 'audit_protocol.json'),
              'source_sha256': protocol['source_sha256']}
    save('audit_result.json', result)
    signal.alarm(0)
    print(result['status'], [(r['panel'], r['flat_indices'], len(r['zero_positions']))
                             for r in rows], flush=True)


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'run')
    {'freeze': freeze, 'run': main}[sys.argv[1]]()
