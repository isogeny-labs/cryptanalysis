"""Prepare the second trace-compatible raw lift of each frozen public point."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
N41 = ROOT / 'n41_n131_fivepair_w9_w29_20261017'
N131_PUBLIC = ROOT / 'n131_w23_sixpair_public_sat_20261017/protocol.json'
N41_FIXTURE = ROOT / 'n41_w9_lazy_source_20261017/fixture.json'
PRIOR_LIFTS = ROOT / 'rotated_fouratom_public_lift_correction_20261010/result.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def field(n, taps):
    R = PolynomialRing(GF(2), 'u')
    u = R.gen()
    F = GF(2**n, name='u', modulus=u**n + sum(u**i for i in taps))
    def dec(word):
        return F(R([(int(word) >> bit) & 1 for bit in range(n)]))
    def enc(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))
    return F, dec, enc


public = json.loads(N131_PUBLIC.read_text())
fixture = json.loads(N41_FIXTURE.read_text())
prior = json.loads(PRIOR_LIFTS.read_text())
cases = [('n41', 41, [0, 3], fixture['curve_id'], fixture['original_raw_point'],
          fixture['original_subgroup_point']),
         ('n131', 131, [0, 1, 2, 13], public['curve_id'], public['raw_point'],
          public['public_target'])]
rows = []
for name, n, taps, curve_id, raw_xy, subgroup_xy in cases:
    F, dec, enc = field(n, taps)
    E = EllipticCurve(F, [1, 0, 0, 0, 1])
    T = E(F.zero(), F.one())
    R0 = E(*map(dec, raw_xy))
    Q = E(*map(dec, subgroup_xy))
    assert 2*T == E(0) and 4*R0 == Q
    R1 = R0 + T
    assert R1 != R0 and 4*R1 == Q and R1[0] and R0[0]
    assert int((1/R0[0]).trace()) == int((1/R1[0]).trace()) == 0
    if name == 'n131':
        expected = prior['n131']['preimages'][1]['point']
        assert [enc(R1[0]), enc(R1[1])] == expected
    rows.append({'field': name, 'degree': n, 'modulus_taps': taps,
                 'curve_id': curve_id,
                 'raw0': list(raw_xy), 'raw1': [enc(R1[0]), enc(R1[1])],
                 'subgroup_point': list(subgroup_xy),
                 'raw0_reciprocal_x': enc(1/R0[0]),
                 'raw1_reciprocal_x': enc(1/R1[0]),
                 'trace_reciprocal_x': 0,
                 'fourfold_projection_equal': True})

source_lines = (N41 / 'join_input.tsv').read_text().splitlines()
assert source_lines[0] == ('ECC2K41 5 284 ' + ' '.join(map(str, rows[0]['raw0'])))
source_lines[0] = 'ECC2K41 5 284 ' + ' '.join(map(str, rows[0]['raw1']))
input_path = HERE / 'n41_raw1_join_input.tsv'
with input_path.open('x') as out:
    out.write('\n'.join(source_lines) + '\n')
result = {'status': 'PASS_TWO_TRACE_COMPATIBLE_RAW_LIFTS',
          'rows': rows, 'n41_raw1_join_input_sha256': sha(input_path),
          'source_sha256': {name: sha(path) for name, path in
                            {'script': Path(__file__), 'n41_fixture': N41_FIXTURE,
                             'n41_join_input': N41 / 'join_input.tsv',
                             'n131_public': N131_PUBLIC,
                             'prior_lifts': PRIOR_LIFTS,
                             'runtime': HERE / 'sage_runtime_info.json'}.items()}}
with (HERE / 'lift_targets.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': result['status'], 'rows': rows}))
