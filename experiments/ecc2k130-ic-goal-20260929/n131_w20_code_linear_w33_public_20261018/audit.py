"""Bind the independent code-linear and block-norm scans to one public point."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODULUS = (1 << 131) | (1 << 13) | (1 << 2) | (1 << 1) | 1
MASK = (1 << 131) - 1


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mul(a, b):
    out = 0
    while b:
        if b & 1:
            out ^= a
        b >>= 1
        a <<= 1
        if a >> 131:
            a ^= MODULUS
    return out


def inverse(a):
    assert a
    u, v, g, h = a, MODULUS, 1, 0
    while u != 1:
        assert u
        delta = u.bit_length() - v.bit_length()
        if delta < 0:
            u, v, g, h = v, u, h, g
            delta = -delta
        u ^= v << delta
        g ^= h << delta
    while g.bit_length() > 131:
        g ^= MODULUS << (g.bit_length() - 132)
    assert mul(a, g) == 1
    return g


def standard(z):
    return mul(z, inverse(z ^ 1))


def block_rows(receipt, begin, end):
    rows = [r.split() for r in receipt['block_lines'] if r.startswith('BLOCK 1 ')]
    assert len(rows) == end - begin
    assert [int(r[2]) for r in rows] == list(range(begin, end))
    assert all(int(r[3]) == (973 if int(r[2]) == 32 else 4096) for r in rows)
    assert all(r[5:7] == ['0', '0'] for r in rows)
    return sum(int(r[3]) for r in rows)


def main():
    protocol_path = HERE / 'audit_protocol.json'
    cfg = json.loads(protocol_path.read_text())
    for name, entry in cfg['sources'].items():
        assert sha(entry['path']) == entry['sha256'], name
    def source(name):
        return Path(cfg['sources'][name]['path'])

    coeff = json.loads(source('w33_coefficients').read_text())
    public = coeff['rows'][1]
    x, y = public['point']
    assert [x, y] == cfg['public_point']
    assert public['reciprocal'] == cfg['public_reciprocal']
    assert mul(x, public['reciprocal']) == 1
    terms = []
    for line in source('block_coefficients').read_text().splitlines():
        row = line.split()
        if row[0] == 'C' and row[1] == '1':
            terms.append(tuple(map(int, row[2:])))
    assert len(terms) == 13
    assert sorted(terms) == sorted(map(tuple, public['terms']))

    original = list(map(int, source('correct_fixture').read_text().split()))
    attempted = list(map(int, source('attempt_fixture').read_text().split()))
    assert len(original) == len(attempted) == 6
    assert original[0] == attempted[0] and original[2:] == attempted[2:]
    assert standard(original[1]) == public['reciprocal']
    assert attempted[1] == public['reciprocal']
    assert standard(attempted[1]) == original[1]
    assert standard(attempted[1]) != public['reciprocal']

    bitmap = source('valid_bitmap').read_bytes()
    assert len(bitmap) == 65536
    bitmap_codes = {i for i in range(1 << 19) if (bitmap[i >> 3] >> (i & 7)) & 1}
    columns = {}
    for line in source('support').read_text().splitlines():
        mask, column, _shift = map(int, line.split())
        assert mask not in columns
        columns[mask] = column
    assert len(columns) == 524493
    selected = set()
    for a, column in columns.items():
        b = a ^ 898618
        if a < b and b in columns and column != columns[b]:
            code = (a & ((1 << 19) - 1)) | ((a >> 20) << 19)
            assert code not in selected
            selected.add(code)
    assert selected == bitmap_codes and len(selected) == 132045

    prior_receipt = json.loads(source('correct_receipt').read_text())
    prior_native = json.loads(source('correct_native_result').read_text())
    assert prior_receipt['status'] == 'COMPLETE' and prior_receipt['exit_code'] == 0
    assert prior_receipt['monitor_failures'] == 0 and prior_receipt['stop_reason'] is None
    assert prior_receipt['native_result_sha256'] == sha(source('correct_native_result'))
    assert prior_native['status'] == 'COMPLETE_CODE_LINEAR'
    assert prior_native['valid_codes'] == 132045 and prior_native['left_roots'] == 264090
    assert prior_native['ordinary']['left'] == 264090
    assert all(prior_native['ordinary'][k] == 0 for k in
               ('full_span', 'source', 'distinct', 'exceptional', 'rank_defect', 'root_fallback'))
    assert prior_native['ordinary']['hits'] == []
    assert not prior_native['ordinary']['capped'] and not prior_native['ordinary']['oom']
    assert prior_native['positive']['distinct'] == 1
    assert prior_native['positive']['hits'][0]['codes'] == [3, 16722]
    assert json.loads(source('correct_verification').read_text())['status'] == 'PASS'

    first = json.loads(source('first_block_receipt').read_text())
    remainder = json.loads(source('remainder_receipt').read_text())
    assert first['status'] == 'BOUNDED_UNKNOWN' and first['stop_reason'] == 'WALL_CAP'
    assert remainder['status'] == 'COMPLETE_NATIVE_NTL_PUBLIC_REMAINDER_BLOCK_NORM'
    assert first['source_line'][0].split()[1:3] == ['132045', '132045']
    assert remainder['source_line'][0].split()[1:3] == ['132045', '132045']
    covered = block_rows(first, 0, 20) + block_rows(remainder, 20, 33)
    assert covered == 132045 and remainder['row_lines'][0].split()[:5] == ['ROW', '1', '20', '33', '0']

    attempt_receipt = json.loads(source('attempt_receipt').read_text())
    attempt_native = json.loads(source('attempt_native_result').read_text())
    assert attempt_receipt['status'] == 'COMPLETE_CODE_LINEAR_W33_PUBLIC_REPLAY'
    assert attempt_native['ordinary']['left'] == 264090
    result = {
        'status': 'PASS_SAME_PUBLIC_POINT_CROSS_AUDIT',
        'candidate_id': None,
        'curve_id': cfg['curve_id'],
        'public_point': [x, y],
        'public_reciprocal': public['reciprocal'],
        'correct_fixture_chart': original[1],
        'attempt_fixture_chart': attempted[1],
        'attempt_actual_reciprocal': standard(attempted[1]),
        'attempt_classification': 'INPUT_CHART_MISMATCH',
        'valid_source_codes': len(selected),
        'code_linear_left_roots_checked': prior_native['ordinary']['left'],
        'code_linear_public_span_hits': prior_native['ordinary']['full_span'],
        'block_norm_public_codes_covered': covered,
        'block_norm_public_gcd_zero_blocks': 33,
        'code_linear_public_query_ns': prior_native['ordinary_query_ns'],
        'prior_parent_wall_seconds': prior_receipt['parent_wall_seconds'],
        'audit_protocol_sha256': sha(protocol_path),
    }
    (HERE / 'audit_result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
