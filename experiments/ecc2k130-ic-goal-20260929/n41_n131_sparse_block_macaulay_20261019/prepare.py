"""Freeze coordinate equations for sparse degree-six block elimination."""
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CORE = ROOT / 'n41_w11_block_macaulay_20261019' / 'run.py'
spec = importlib.util.spec_from_file_location('block_core_sparse', CORE)
block = importlib.util.module_from_spec(spec)
spec.loader.exec_module(block)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def coordinate_supports(poly, n):
    rows = [[] for _ in range(n)]
    for monomial, value in poly.items():
        while value:
            low = value & -value
            rows[low.bit_length() - 1].append(monomial)
            value ^= low
    for row in rows:
        row.sort()
        assert len(row) == len(set(row))
    return rows


def write_equations(path, variables, field_bits, supports):
    with path.open('x') as output:
        output.write(f'EQS {variables} {field_bits} 4 2\n')
        for bit, row in enumerate(supports):
            output.write(f'{bit} {len(row)}')
            for mask in row:
                output.write(f' {mask}')
            output.write('\n')


def n41_cells():
    block.F = block.Field(41, 9)
    block.WIDTH = 2
    block.VARIABLES = 12
    positions = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10]
    block.LEFT = block.source_basis(block.F, 112, positions, 12)
    block.RIGHT = block.source_basis(block.F, 112, positions, 24)
    terms = {i: {} for i in range(2)}
    lines = (ROOT / 'n41_w11_freecode_resultant_20261018' / 'resultant_input.tsv').read_text().splitlines()
    for line in lines:
        row = line.split()
        if row[0] == 'C' and int(row[1]) < 2:
            terms[int(row[1])][int(row[2]), int(row[3])] = int(row[4])
    for target in [0, 1]:
        for anchor in [0, 252, 512]:
            yield f'n41_t{target}_a{anchor}', 41, 12, terms[target], anchor, target


def n131_cells():
    block.F = block.Field(131, (1 << 13) | (1 << 2) | (1 << 1) | 1)
    block.WIDTH = 2
    block.VARIABLES = 34
    seed_mask = 898618
    positions = [i for i in range(33) if i != seed_mask.bit_length() - 1]
    block.LEFT = block.source_basis(block.F, seed_mask << 1, positions, 0)
    block.RIGHT = block.source_basis(block.F, seed_mask << 1, positions, 18)
    source = json.loads((ROOT / 'n131_w33_freecode_resultant_20261018' /
                         'coefficients.json').read_text())
    for target in [0, 1]:
        terms = {(i, j): value for i, j, value in source['rows'][target]['terms']}
        yield f'n131_t{target}_a0', 131, 34, terms, 0, target


def main():
    protocol = json.loads((HERE / 'prepare_protocol.json').read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_SPARSE_BLOCK_PREPARATION'
    for item in protocol['sources'].values():
        assert sha(item['path']) == item['sha256']
    start = time.monotonic()
    outputs = []
    for label, n, variables, terms, anchor, target in n41_cells():
        poly = block.product_anf(terms, anchor)
        assert max(mask.bit_count() for mask in poly) == 4
        supports = coordinate_supports(poly, n)
        path = HERE / (label + '.eqs')
        write_equations(path, variables, n, supports)
        outputs.append({'label': label, 'field_degree': n, 'variables': variables,
                        'target_index': target, 'anchor': anchor,
                        'anf_terms': len(poly), 'support_entries': sum(map(len, supports)),
                        'path': str(path), 'sha256': sha(path)})
    for label, n, variables, terms, anchor, target in n131_cells():
        poly = block.product_anf(terms, anchor)
        assert max(mask.bit_count() for mask in poly) == 4
        if target == 0:
            assert block.evaluate_anf(poly, 3, 16722) == 0
        supports = coordinate_supports(poly, n)
        path = HERE / (label + '.eqs')
        write_equations(path, variables, n, supports)
        outputs.append({'label': label, 'field_degree': n, 'variables': variables,
                        'target_index': target, 'anchor': anchor,
                        'anf_terms': len(poly), 'support_entries': sum(map(len, supports)),
                        'path': str(path), 'sha256': sha(path)})
    assert [row['label'] for row in outputs] == protocol['labels']
    result = {'status': 'PASS_SPARSE_BLOCK_PREPARATION', 'candidate_id': None,
              'outputs': outputs, 'wall_seconds': time.monotonic() - start,
              'protocol_sha256': sha(HERE / 'prepare_protocol.json'),
              'script_sha256': sha(__file__)}
    (HERE / 'prepare_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'outputs': len(outputs),
                      'wall_seconds': result['wall_seconds']}, sort_keys=True))


if __name__ == '__main__':
    main()
