"""Independent full-table GF(2^131) audit of adjacent reciprocal outputs."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'n131_projected_root_lookup_screen_20261015' / 'canonical_table.bin'
MODULUS = (1 << 131) | (1 << 13) | (1 << 2) | (1 << 1) | 1
MASK = (1 << 131) - 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def multiply(a, b):
    answer = 0
    while b:
        if b & 1:
            answer ^= a
        b >>= 1
        a <<= 1
        if a & (1 << 131):
            a ^= MODULUS
    return answer


def read17(data, offset):
    value = int.from_bytes(data[offset:offset+17], 'little')
    assert value <= MASK
    return value


def main():
    protocol = json.loads((HERE / 'n131_protocol.json').read_text())
    result = json.loads((HERE / 'n131_result.json').read_text())
    assert sha(SOURCE) == protocol['source_sha256']['raw_root_table']
    assert sha(HERE / 'adjacent_roots.bin') == result['output_sha256']
    source = SOURCE.read_bytes()
    mapped = (HERE / 'adjacent_roots.bin').read_bytes()
    assert len(mapped) == 66382 * 34
    roots = 0
    checks = 0
    for code in range(1 << 17):
        for branch in range(2):
            a = read17(source, code*68 + branch*17)
            if a == 0:
                continue
            b = read17(mapped, roots*34)
            c = read17(mapped, roots*34+17)
            assert multiply(b, 1 ^ multiply(a, a)) == a, (code, branch, 'plus')
            assert multiply(c, 1 ^ multiply(b, b)) == b, (code, branch, 'minus')
            roots += 1
            checks += 2
    assert roots == result['raw_roots'] == 66382
    assert checks == 132764
    record = {'status': 'PASS_INDEPENDENT_FULL_ADJACENT_ROOT_TABLE',
              'root_count': roots, 'field_equations_checked': checks,
              'source_sha256': sha(SOURCE),
              'mapped_sha256': sha(HERE / 'adjacent_roots.bin'),
              'verifier_sha256': sha(Path(__file__))}
    with (HERE / 'n131_verify_result.json').open('x') as file:
        json.dump(record, file, indent=2, sort_keys=True)
        file.write('\n')
    print(record['status'], roots, checks)


if __name__ == '__main__':
    main()
