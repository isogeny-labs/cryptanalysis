"""Independent low-pivot replay of the W18 root and ANF ranks."""
import gzip
import hashlib
import itertools
import json
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
TABLE = BASE.parent / 'n131_w18_linked_signature_prefix_20261012' / 'rows.tsv.gz'
N = 131
K = 17


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def put(name, obj):
    with (BASE / name).open('x') as out:
        json.dump(obj, out, sort_keys=True, indent=2)
        out.write('\n')


def insert(basis, value):
    while value:
        bit = (value & -value).bit_length() - 1
        if bit not in basis:
            basis[bit] = value
            return True
        value ^= basis[bit]
    return False


def rows():
    result = []
    with gzip.open(TABLE, 'rt') as source:
        assert source.readline().strip().split('\t') == [
            'code', 'mask_a', 'mask_b', 'root_bit', 'a0', 'a1',
            'plus0', 'minus0', 'plus1', 'minus1']
        for line in source:
            code, ma, mb, rb, x, y, *_ = map(int, line.split('\t'))
            assert 0 <= code < 1 << K and mb == ma ^ 212 and 0 <= rb <= 16
            assert 0 < x < 1 << N and 0 < y < 1 << N and x != y
            result.append((code, x, y))
    assert len(result) == 33191 and len({code for code, _, _ in result}) == len(result)
    return result


def main(mode):
    if mode == 'freeze':
        put('audit_protocol.json', {'status': 'FROZEN_INDEPENDENT_LOW_PIVOT_REPLAY',
             'table_sha256': digest(TABLE), 'script_sha256': digest(Path(__file__)),
             'census_sha256': digest(BASE / 'result.json'),
             'intersection_sha256': digest(BASE / 'intersection_result.json'),
             'degree_max': 5, 'wall_cap_seconds': 180, 'worker_count': 1})
        return
    assert mode == 'run'
    start = time.monotonic_ns()
    protocol = json.loads((BASE / 'audit_protocol.json').read_text())
    assert protocol['status'] == 'FROZEN_INDEPENDENT_LOW_PIVOT_REPLAY'
    assert protocol['table_sha256'] == digest(TABLE)
    assert protocol['script_sha256'] == digest(Path(__file__))
    assert protocol['census_sha256'] == digest(BASE / 'result.json')
    assert protocol['intersection_sha256'] == digest(BASE / 'intersection_result.json')
    table = rows()
    delta = {}
    for _, x, y in table:
        insert(delta, x ^ y)
    assert len(delta) == K
    # Eliminate each pivot from all other rows to expose a dual basis.
    for bit in sorted(delta, reverse=True):
        for other in delta:
            if other != bit and delta[other] >> bit & 1:
                delta[other] ^= delta[bit]
    free = [bit for bit in range(N) if bit not in delta]
    dual = [1 << bit | sum((1 << pivot) for pivot, row in delta.items()
                            if row >> bit & 1) for bit in free]
    assert len(dual) == 114
    assert all((mask & (x ^ y)).bit_count() % 2 == 0
               for _, x, y in table for mask in dual)
    dual_rank = {}
    for mask in dual:
        assert insert(dual_rank, mask)
    code_vectors = [0] * K
    labels = [0] * len(dual)
    output_basis = {}
    for index, (code, x, y) in enumerate(table):
        bit = 1 << index
        for j in range(K):
            if code >> j & 1:
                code_vectors[j] |= bit
        for j, mask in enumerate(dual):
            if (x & mask).bit_count() & 1:
                labels[j] |= bit
        insert(output_basis, x)
        insert(output_basis, y)
    assert len(output_basis) == 130
    label_basis = {}
    for label in labels:
        insert(label_basis, label)
    assert len(label_basis) == 113
    # Verify the particular null functional found by the high-pivot run.
    published = json.loads((BASE / 'intersection_result.json').read_text())
    census = json.loads((BASE / 'result.json').read_text())
    combination = published['screens'][0]['first_dependency_mask']
    global_mask = 0
    for index, mask in enumerate(census['dual_masks']):
        if combination >> index & 1:
            global_mask ^= mask
    assert global_mask and all((global_mask & x).bit_count() % 2 == 0 and
                               (global_mask & y).bit_count() % 2 == 0
                               for _, x, y in table)
    feature_basis = {}
    full = (1 << len(table)) - 1
    feature_count = 0
    screens = []
    for degree in range(6):
        for vars_ in itertools.combinations(range(K), degree):
            value = full
            for variable in vars_:
                value &= code_vectors[variable]
            insert(feature_basis, value)
            feature_count += 1
        quotient = {}
        for label in labels:
            value = label
            for pivot in sorted(feature_basis):
                if value >> pivot & 1:
                    value ^= feature_basis[pivot]
            insert(quotient, value)
        intersection = len(label_basis) - len(quotient)
        expected = published['screens'][degree]
        assert (feature_count, len(feature_basis), len(quotient), intersection) == (
            expected['feature_count'], expected['feature_rank'],
            expected['quotient_signature_rank'], expected['intersection_dimension'])
        screens.append({'degree': degree, 'feature_count': feature_count,
                        'feature_rank': len(feature_basis),
                        'quotient_signature_rank': len(quotient),
                        'intersection_dimension': intersection})
    result = {'status': 'PASS_INDEPENDENT_LOW_PIVOT_REPLAY',
              'source_rows': len(table), 'root_difference_rank': len(delta),
              'dual_rank': len(dual_rank), 'output_span_rank': len(output_basis),
              'signature_rank': len(label_basis),
              'global_zero_mask_hex': hex(global_mask),
              'global_zero_mask_weight': global_mask.bit_count(),
              'screens': screens, 'elapsed_ns': time.monotonic_ns() - start,
              'protocol_sha256': digest(BASE / 'audit_protocol.json')}
    put('audit_result.json', result)
    print(result['status'], result['output_span_rank'],
          [s['intersection_dimension'] for s in screens])


if __name__ == '__main__':
    assert len(sys.argv) == 2
    main(sys.argv[1])
