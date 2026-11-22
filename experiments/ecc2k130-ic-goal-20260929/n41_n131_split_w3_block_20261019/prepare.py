"""Build the second width-two case for the exact width-three partition."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CORE = ROOT / 'n41_w11_block_macaulay_20261019' / 'run.py'
spec = importlib.util.spec_from_file_location('split_block_core', CORE)
block = importlib.util.module_from_spec(spec)
spec.loader.exec_module(block)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def supports(poly, n):
    rows = [[] for _ in range(n)]
    for mask, value in poly.items():
        while value:
            low = value & -value
            rows[low.bit_length() - 1].append(mask)
            value ^= low
    for row in rows:
        row.sort()
        assert len(row) == len(set(row))
    return rows


def write(path, variables, n, rows):
    with path.open('x') as output:
        output.write(f'EQS {variables} {n} 4 2\n')
        for bit, row in enumerate(rows):
            output.write(f'{bit} {len(row)}' + ''.join(f' {mask}' for mask in row) + '\n')


def cells():
    block.F = block.Field(41, 9)
    block.WIDTH, block.VARIABLES = 2, 12
    positions = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10]
    block.LEFT = block.source_basis(block.F, 112, positions, 12)
    block.RIGHT = block.source_basis(block.F, 112, positions, 24)
    terms = {}
    source = ROOT / 'n41_w11_freecode_resultant_20261018' / 'resultant_input.tsv'
    for line in source.read_text().splitlines():
        row = line.split()
        if row[0] == 'C' and int(row[1]) == 1:
            terms[int(row[2]), int(row[3])] = int(row[4])
    yield 'n41_t1_a4', 41, 12, terms, 4

    block.F = block.Field(131, (1 << 13) | (1 << 2) | (1 << 1) | 1)
    block.WIDTH, block.VARIABLES = 2, 34
    seed = 898618
    positions = [i for i in range(33) if i != seed.bit_length() - 1]
    block.LEFT = block.source_basis(block.F, seed << 1, positions, 0)
    block.RIGHT = block.source_basis(block.F, seed << 1, positions, 18)
    source = json.loads((ROOT / 'n131_w33_freecode_resultant_20261018' /
                         'coefficients.json').read_text())
    terms = {(i, j): value for i, j, value in source['rows'][1]['terms']}
    yield 'n131_t1_a4', 131, 34, terms, 4


def main():
    cfg = json.loads((HERE / 'prepare_protocol.json').read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_SPLIT_PREPARATION'
    assert sha(__file__) == cfg['script_sha256']
    for rec in cfg['sources'].values():
        assert sha(rec['path']) == rec['sha256']
    start = time.monotonic()
    outputs = []
    for label, n, variables, terms, anchor in cells():
        poly = block.product_anf(terms, anchor)
        assert max(mask.bit_count() for mask in poly) == 4
        rows = supports(poly, n)
        path = HERE / (label + '.eqs')
        write(path, variables, n, rows)
        outputs.append({'label': label, 'field_degree': n, 'variables': variables,
                        'target_index': 1, 'anchor': anchor, 'anf_terms': len(poly),
                        'support_entries': sum(map(len, rows)), 'path': str(path),
                        'sha256': sha(path)})
    assert [row['label'] for row in outputs] == cfg['labels']
    result = {'status': 'PASS_SPLIT_PREPARATION', 'candidate_id': None,
              'outputs': outputs, 'wall_seconds': time.monotonic() - start,
              'protocol_sha256': sha(HERE / 'prepare_protocol.json'),
              'script_sha256': sha(__file__)}
    (HERE / 'prepare_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
