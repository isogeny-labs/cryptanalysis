#!/usr/bin/env sage -python
"""Complete adjacent-Frobenius reciprocal maps on W18 raw pair roots."""
import hashlib
import json
import resource
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n131_projected_root_lookup_screen_20261015'
TABLE = SOURCE / 'canonical_table.bin'
RUNTIME = HERE / 'n131_sage_runtime_info.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open('x') as file:
        json.dump(value, file, indent=2, sort_keys=True)
        file.write('\n')


def sources():
    return {'script': Path(__file__), 'raw_root_table': TABLE,
            'raw_root_receipt': SOURCE / 'prepare_result.json',
            'n41_sage_audit': HERE / 'audit_result.json',
            'runtime': RUNTIME}


def freeze():
    source = json.loads((SOURCE / 'prepare_result.json').read_text())
    assert source['status'] == 'PASS_N131_CANONICAL_PROJECTED_ROOT_TABLE'
    assert source['raw_root_values'] == 66382
    assert source['table_sha256'] == sha(TABLE)
    save('n131_protocol.json', {'status': 'FROZEN_ADJACENT_W18_ROOT_SOURCE',
         'candidate_id': None, 'curve_id': 'EC1N131Ckb1heb5f1998f20b',
         'field': 'GF(2)[t]/(t^131+t^13+t^2+t+1)',
         'source_codes': 33191, 'roots_per_code': 2,
         'sample_rule': '64 equally spaced ordinal code indices including endpoints; both roots and both point signs',
         'worker_count': 1, 'alarm_seconds': 180,
         'rss_observational_cap_bytes': 4*1024**3,
         'source_sha256': {name: sha(path) for name, path in sources().items()}})


def batch_inverse(values, one):
    assert values and all(values)
    prefix = [one]
    for value in values:
        prefix.append(prefix[-1]*value)
    inverse = ~prefix[-1]
    output = [None]*len(values)
    for index in range(len(values)-1, -1, -1):
        output[index] = inverse*prefix[index]
        inverse *= values[index]
    assert inverse == one
    return output


def run():
    from sage.all import EllipticCurve, GF, PolynomialRing
    protocol = json.loads((HERE / 'n131_protocol.json').read_text())
    assert protocol['source_sha256'] == {name: sha(path) for name, path in sources().items()}
    start = time.monotonic_ns()
    raw = TABLE.read_bytes()
    assert len(raw) == (1 << 17)*4*17
    code_and_root = []
    for code in range(1 << 17):
        offset = code*68
        a = [int.from_bytes(raw[offset+17*j:offset+17*(j+1)], 'little') for j in range(2)]
        if a[0] or a[1]:
            assert all(value not in (0, 1) for value in a)
            code_and_root.extend((code, branch, value) for branch, value in enumerate(a))
    assert len(code_and_root) == 66382
    parsed = time.monotonic_ns()
    ring = PolynomialRing(GF(2), 't')
    t = ring.gen()
    field = GF(2**131, name='t', modulus=t**131+t**13+t**2+t+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    one = field.one()
    def dec(value):
        return field(ring([(int(value) >> i) & 1 for i in range(131)]))
    def enc(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))
    a_values = [dec(value) for _, _, value in code_and_root]
    denominators = [one+a*a for a in a_values]
    assert all(denominators)
    inverses = batch_inverse(denominators, one)
    plus = [a*inverse for a, inverse in zip(a_values, inverses)]
    assert all(value not in (0, one) for value in plus)
    second_denominators = [one+b*b for b in plus]
    assert all(second_denominators)
    second_inverses = batch_inverse(second_denominators, one)
    minus = [b*inverse for b, inverse in zip(plus, second_inverses)]
    assert all(minus)
    mapped = time.monotonic_ns()
    output = bytearray()
    for b,c in zip(plus, minus):
        output += enc(b).to_bytes(17, 'little')
        output += enc(c).to_bytes(17, 'little')
    with (HERE / 'adjacent_roots.bin').open('xb') as file:
        file.write(output)
    saved = time.monotonic_ns()
    sample_ordinals = sorted({i*33190//63 for i in range(64)})
    assert len(sample_ordinals) == 64
    checked = 0
    for ordinal in sample_ordinals:
        for branch in range(2):
            index = ordinal*2+branch
            a = a_values[index]
            x = ~a
            for point in curve.lift_x(x, all=True):
                tau = curve(point[0]**2, point[1]**2)
                actual_plus = point+tau
                actual_minus = point-tau
                assert actual_plus != curve(0) and actual_minus != curve(0)
                assert plus[index] == 1/actual_plus[0]
                assert minus[index] == 1/actual_minus[0]
                checked += 2
    audited = time.monotonic_ns()
    assert checked == 64*2*2*2
    save('n131_result.json', {'status': 'PASS_N131_ADJACENT_ROOT_MAP',
         'candidate_id': None, 'codes': 33191, 'raw_roots': len(code_and_root),
         'mapped_reciprocals_per_root': 2,
         'exceptional_denominators': 0, 'sample_code_ordinals': sample_ordinals,
         'independent_group_checks': checked,
         'output_bytes': len(output), 'output_sha256': sha(HERE / 'adjacent_roots.bin'),
         'phase_ns': {'source_parse': parsed-start, 'two_batch_maps': mapped-parsed,
                      'serialization': saved-mapped, 'sage_group_sample': audited-saved},
         'total_ns': audited-start,
         'peak_self_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         'protocol_sha256': sha(HERE / 'n131_protocol.json'),
         'source_sha256': protocol['source_sha256']})
    print('PASS_N131_ADJACENT_ROOT_MAP', len(code_and_root), checked)


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'run')
    {'freeze': freeze, 'run': run}[sys.argv[1]]()
