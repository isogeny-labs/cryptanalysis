"""Exact representation counts for the next dense Macaulay degree."""
import hashlib
import json
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_N131_W33_BLOCK_PILOT'
    variables = protocol['free_right_bits'] + len(protocol['free_left_bits'])
    assert variables == 34
    levels = []
    for degree in [4, 5, 6]:
        columns = sum(comb(variables, k) for k in range(degree + 1))
        multiplier_degree = degree - 4
        multiplier_monomials = sum(comb(variables, k)
                                   for k in range(multiplier_degree + 1))
        rows = 131 * multiplier_monomials
        row_bytes = (columns + 7) // 8
        levels.append({'degree': degree, 'variables': variables,
                       'columns': columns, 'rows': rows,
                       'row_bytes_rectangular': row_bytes,
                       'matrix_bytes_rectangular': row_bytes * rows})
    out = {'status': 'PASS_N131_W33_DENSE_REPRESENTATION_COUNT',
           'candidate_id': None, 'curve_id': protocol['curve_id'],
           'protocol_sha256': sha(HERE / 'protocol.json'),
           'script_sha256': sha(__file__), 'levels': levels}
    (HERE / 'resource_bound.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'degree6_rectangular_bytes':
                      levels[-1]['matrix_bytes_rectangular']}, sort_keys=True))


if __name__ == '__main__':
    main()
