"""Independent Sage arithmetic on frozen W33 code slices of the block ANF."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PILOT = ROOT / 'n41_w11_block_macaulay_20261019' / 'run.py'
spec = importlib.util.spec_from_file_location('block_pilot_sage_audit', PILOT)
block = importlib.util.module_from_spec(spec)
spec.loader.exec_module(block)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    cfg = json.loads((HERE / 'audit_protocol.json').read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_N131_W33_BLOCK_SAGE_AUDIT'
    for item in cfg['sources'].values():
        assert sha(item['path']) == item['sha256']
    result = json.loads((HERE / 'result.json').read_text())
    source = json.loads(Path(cfg['sources']['coefficients']['path']).read_text())
    ring = PolynomialRing(GF(2), 'u')
    u = ring.gen()
    field = GF(2**131, name='u', modulus=u**131 + u**13 + u**2 + u + 1)
    decode = field.from_integer
    encode = lambda value: sum(int(bit) << i for i, bit in
                               enumerate(value.polynomial().list()))
    seed_mask = 898618
    seed = decode(seed_mask << 1)
    positions = [i for i in range(33) if i != seed_mask.bit_length() - 1]
    bases = []
    for rotation in [0, 18]:
        bases.append([(decode(1 << (bit + 1))**2 +
                       seed * decode(1 << (bit + 1)))**(1 << rotation)
                      for bit in positions])

    def product(code, basis):
        value = field.zero()
        for bit, term in enumerate(basis):
            if code >> bit & 1:
                value += term
        return value

    block.F = block.Field(131, (1 << 13) | (1 << 2) | (1 << 1) | 1)
    block.WIDTH = 2
    block.VARIABLES = 34
    block.LEFT = block.source_basis(block.F, seed_mask << 1, positions, 0)
    block.RIGHT = block.source_basis(block.F, seed_mask << 1, positions, 18)
    left = {code: product(code, bases[0]) for code in range(4)}
    right_codes = [anchor + low for anchor in cfg['right_anchors'] for low in range(1024)]
    sample_codes = {code for row in result['rows'] for _, code, _ in row['samples']}
    right = {code: product(code, bases[1]) for code in set(right_codes) | sample_codes}
    right_powers = {code: [field.one(), q, q**2, q**3, q**4]
                    for code, q in right.items()}
    start = time.monotonic()
    checks = []
    for row in result['rows']:
        index = row['target_index']
        terms = {(i, j): value for i, j, value in source['rows'][index]['terms']}
        anf = block.product_anf(terms, 0)
        assert len(anf) == row['anf_terms']
        coeff = {}
        for code in range(4):
            p = left[code]
            powers = [field.one(), p, p**2, p**3, p**4]
            by_q_degree = [field.zero() for _ in range(5)]
            for (i, j), value in terms.items():
                by_q_degree[j] += decode(value) * powers[i]
            coeff[code] = by_q_degree
        roots = []
        checked = 0
        for left_code in range(4):
            for right_code in right_codes:
                a = coeff[left_code]
                direct = sum((a[j] * right_powers[right_code][j]
                              for j in range(5)), field.zero())
                encoded = encode(direct)
                assert encoded == block.evaluate_anf(anf, left_code, right_code)
                checked += 1
                if not direct:
                    roots.append([left_code, right_code])
        assert checked == 8192
        if index == 0:
            assert [3, 16722] in roots
        for left_code, right_code, zero in row['samples']:
            assert (encode(sum((coeff[left_code][j] * right_powers[right_code][j]
                                for j in range(5)), field.zero())) == 0) == zero
        checks.append({'target_index': index, 'slice_values_checked': checked,
                       'roots_in_slices': roots, 'anf_terms': len(anf)})
    out = {'status': 'PASS_N131_W33_BLOCK_SAGE_SLICE_AUDIT',
           'candidate_id': None, 'curve_id': result['curve_id'],
           'checks': checks, 'values_checked': sum(x['slice_values_checked'] for x in checks),
           'wall_seconds': time.monotonic() - start,
           'protocol_sha256': sha(HERE / 'audit_protocol.json'),
           'script_sha256': sha(__file__), 'result_sha256': sha(HERE / 'result.json')}
    (HERE / 'audit_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'values_checked': out['values_checked'],
                      'wall_seconds': out['wall_seconds']}, sort_keys=True))


if __name__ == '__main__':
    main()
