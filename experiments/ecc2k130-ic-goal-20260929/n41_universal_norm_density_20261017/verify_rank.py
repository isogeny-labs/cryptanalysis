"""Independent field elimination on the serialized p-by-r coefficient matrix."""
import hashlib
import json
from pathlib import Path

from verify import mul

HERE = Path(__file__).resolve().parent
ORDER = 1 << 41


def power(base, exponent):
    out = 1
    while exponent:
        if exponent & 1:
            out = mul(out, base)
        base = mul(base, base)
        exponent >>= 1
    return out


def rank(rows, columns):
    pivots = {}
    pivot_rows = []
    for row_index, raw in enumerate(rows):
        row = raw[:]
        for col in sorted(pivots):
            pivot = pivots[col]
            factor = row[col]
            if factor:
                for j in range(col, columns):
                    row[j] ^= mul(factor, pivot[j])
        col = next((j for j, value in enumerate(row) if value), None)
        if col is None:
            continue
        inverse = power(row[col], ORDER - 2)
        assert mul(row[col], inverse) == 1
        for j in range(col, columns):
            row[j] = mul(row[j], inverse)
        pivots[col] = row
        pivot_rows.append(row_index)
        if len(pivots) == columns:
            break
    return len(pivots), pivot_rows


def main():
    protocol_path = HERE / 'protocol_v4.json'
    result_path = HERE / 'result_v4.json'
    matrix_path = HERE / 'coefficient_matrix_v4.bin'
    protocol = json.loads(protocol_path.read_text())
    result = json.loads(result_path.read_text())
    checkpoint = result['panels'][0]['checkpoints'][-1]
    assert result['protocol_sha256'] == hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    assert result['source_sha256'] == protocol['source_sha256']
    raw = matrix_path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == checkpoint['matrix_sha256']
    columns, row_count = checkpoint['column_count'], checkpoint['row_count']
    assert len(raw) == checkpoint['matrix_bytes'] == columns * row_count * 8
    values = [int.from_bytes(raw[i:i+8], 'little') for i in range(0, len(raw), 8)]
    assert all(0 <= x < ORDER for x in values)
    rows = [values[i*columns:(i+1)*columns] for i in range(row_count)]
    occupied = sum(bool(x) for x in values)
    assert occupied == checkpoint['nonzero_coefficients']
    actual_rank, pivot_rows = rank(rows, columns)
    assert actual_rank == checkpoint['separation_rank'] == columns
    receipt = {'status': 'PASS_INDEPENDENT_GF2_41_FULL_COLUMN_RANK',
               'rank': actual_rank, 'row_count': row_count, 'column_count': columns,
               'occupied': occupied, 'pivot_rows': pivot_rows,
               'matrix_sha256': checkpoint['matrix_sha256'],
               'result_sha256': hashlib.sha256(result_path.read_bytes()).hexdigest(),
               'verifier_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (HERE / 'rank_verification.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(receipt['status'], actual_rank, occupied)


if __name__ == '__main__':
    main()
