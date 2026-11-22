"""Independent finite-field replay of native product recovery and membership."""
import hashlib
import json
import sys
from pathlib import Path

from sage.all import GF, PolynomialRing, matrix, vector

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def field(n):
    ring = PolynomialRing(GF(2), 'x')
    x = ring.gen()
    modulus = x**41 + x**3 + 1 if n == 41 else x**131 + x**13 + x**2 + x + 1
    return GF(2**n, name='x', modulus=modulus)


def encoded(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def parse_limb_value(value):
    limbs = json.loads(value)
    assert len(limbs) == 3 and all(0 <= part < 1 << 64 for part in limbs)
    return limbs[0] | (limbs[1] << 64) | (limbs[2] << 128)


def main():
    assert len(sys.argv) == 2 and sys.argv[1] in ('n41', 'n131')
    label = sys.argv[1]
    cfg = json.loads((HERE / f'audit_protocol_{label}_v2.json').read_text())
    assert cfg['status'] == f'FROZEN_BEFORE_IMPLICIT_PAIR_AUDIT_{label.upper()}_V2'
    assert sha(__file__) == cfg['script_sha256']
    for rec in cfg['sources'].values():
        assert sha(rec['path']) == rec['sha256']
    n = 41 if label == 'n41' else 131
    prep = json.loads((HERE / 'prepare_result.json').read_text())
    case = next(item for item in prep['cases'] if item['field_degree'] == n)
    f = field(n)
    decode = f.from_integer
    raw = (HERE / f'input_{label}.txt').read_text().splitlines()
    header = raw[0].split()
    assert header[:3] == ['PAIR', str(n), str(len(case['free_positions']))]
    ccoef, hcoef, samples, random_seed = map(int, header[3:])
    assert ccoef == case['quadratic_c'] and hcoef == case['quadratic_h']
    assert samples == case['samples'] and random_seed == 898618
    cc, hh = decode(ccoef), decode(hcoef)
    seed = decode(case['seed_mask'] << 1)
    basis = [(decode(1 << (position + 1))**2 +
              seed * decode(1 << (position + 1)))**(1 << case['rotation'])
             for position in case['free_positions']]
    assert [int(x) for x in raw[1:1+len(basis)]] == list(map(encoded, basis))
    assert raw[1+len(basis)] == 'POS 64'
    expected = [tuple(map(int, line.split())) for line in
                raw[2+len(basis):2+len(basis)+64]]
    assert len(expected) == 64
    lines = (HERE / f'{label}.stdout').read_text().splitlines()
    pos = [line.split() for line in lines if line.startswith('POS ')]
    scans = [line.split() for line in lines if line.startswith('SAMPLE ')]
    finals = [line.split() for line in lines if line.startswith('RESULT ')]
    assert len(pos) == len(scans) == 64 and len(finals) == 1
    assert finals[0][1:5] == ['COMPLETE', str(n), str(len(basis)), str(samples)]
    assert int(finals[0][5]) == 0
    for i, (c_int, code) in enumerate(expected):
        assert pos[i] == ['POS', str(i), str(c_int), str(code)]
        c = decode(c_int)
        p = (cc*c**2 + hh) / c
        expected_p = sum((basis[j] for j in range(len(basis)) if code >> j & 1),f.zero())
        assert p == expected_p
        assert cc*c**2 + p*c + hh == 0
    columns = matrix(GF(2), n, len(basis), lambda i,j: (encoded(basis[j]) >> i) & 1)
    assert columns.rank() == len(basis)
    for i, row in enumerate(scans):
        assert row[0:2] == ['SAMPLE',str(i)]
        c_int,p_int = map(parse_limb_value,row[2:4])
        code = int(row[4])
        c,p = decode(c_int),decode(p_int)
        assert c != 0 and p == (cc*c**2 + hh) / c
        try:
            solution = columns.solve_right(vector(GF(2),[(p_int >> j)&1 for j in range(n)]))
            recovered = sum(int(bit)<<j for j,bit in enumerate(solution))
        except ValueError:
            recovered = -1
        assert recovered == code
    receipt = json.loads((HERE / f'{label}.receipt.json').read_text())
    assert receipt['status'] == 'COMPLETE' and receipt['exit_code'] == 0
    assert receipt['stdout_sha256'] == sha(HERE / f'{label}.stdout')
    assert receipt['stderr_sha256'] == sha(HERE / f'{label}.stderr')
    result = {'status': f'PASS_IMPLICIT_PAIR_AUDIT_{label.upper()}',
              'candidate_id': None, 'field_degree': n, 'positive_controls': len(pos),
              'random_samples_replayed': len(scans), 'full_random_scan': samples,
              'random_memberships_reported': int(finals[0][5]),
              'native_query_ns': int(finals[0][7]),
              'input_sha256': sha(HERE / f'input_{label}.txt'),
              'stdout_sha256': sha(HERE / f'{label}.stdout'),
              'protocol_sha256': sha(HERE / f'audit_protocol_{label}_v2.json'),
              'script_sha256': sha(__file__)}
    (HERE / f'audit_result_{label}.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__ == '__main__':
    main()
