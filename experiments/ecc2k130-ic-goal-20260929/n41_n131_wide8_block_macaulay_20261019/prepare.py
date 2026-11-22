"""Freeze degree-four ANFs for eight free left bits and the full right code."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CORE = ROOT / 'n41_w11_block_macaulay_20261019' / 'run.py'
spec = importlib.util.spec_from_file_location('wide8_block_core', CORE)
block = importlib.util.module_from_spec(spec)
spec.loader.exec_module(block)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def product_anf(terms, anchor, width):
    assert anchor & ((1 << width) - 1) == 0
    p = {0: block.source_value(anchor, block.LEFT)}
    p.update({1 << bit: block.LEFT[bit] for bit in range(width)})
    q = {1 << (width + bit): value for bit, value in enumerate(block.RIGHT)}
    pp, qq = block.poly_powers(p), block.poly_powers(q)
    result = {}
    for (i, j), scalar in terms.items():
        for mask, value in block.poly_mul(pp[i], qq[j]).items():
            result[mask] = result.get(mask, 0) ^ block.F.mul(scalar, value)
    return {mask: value for mask, value in result.items() if value}


def evaluate(poly, left_code, right_code, anchor, width):
    assignment = (left_code - anchor) | (right_code << width)
    value = 0
    for mask, coefficient in poly.items():
        if assignment & mask == mask:
            value ^= coefficient
    return value


def coordinate_supports(poly, field_bits):
    rows = [[] for _ in range(field_bits)]
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
    with path.open('x') as stream:
        stream.write(f'EQS {variables} {field_bits} 4 2\n')
        for bit, row in enumerate(supports):
            stream.write(f'{bit} {len(row)}')
            for mask in row:
                stream.write(f' {mask}')
            stream.write('\n')


def instances():
    width = 8
    block.F = block.Field(41, 9)
    block.WIDTH = width
    block.VARIABLES = width + 10
    positions = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10]
    block.LEFT = block.source_basis(block.F, 112, positions, 12)
    block.RIGHT = block.source_basis(block.F, 112, positions, 24)
    terms = {i: {} for i in (0, 1)}
    for line in (ROOT / 'n41_w11_freecode_resultant_20261018' /
                 'resultant_input.tsv').read_text().splitlines():
        row = line.split()
        if row[0] == 'C' and int(row[1]) in terms:
            terms[int(row[1])][int(row[2]), int(row[3])] = int(row[4])
    for target in (0, 1):
        yield {'label': f'n41_t{target}_a0_w8', 'field_bits': 41,
               'variables': 18, 'terms': terms[target], 'anchor': 0,
               'target_index': target, 'positive': (253, 63) if target == 0 else None,
               'width': width}

    block.F = block.Field(131, (1 << 13) | (1 << 2) | (1 << 1) | 1)
    block.WIDTH = width
    block.VARIABLES = width + 32
    seed_mask = 898618
    positions = [i for i in range(33) if i != seed_mask.bit_length() - 1]
    block.LEFT = block.source_basis(block.F, seed_mask << 1, positions, 0)
    block.RIGHT = block.source_basis(block.F, seed_mask << 1, positions, 18)
    source = json.loads((ROOT / 'n131_w33_freecode_resultant_20261018' /
                         'coefficients.json').read_text())
    for target in (0, 1):
        terms = {(i, j): value for i, j, value in source['rows'][target]['terms']}
        yield {'label': f'n131_t{target}_a0_w8', 'field_bits': 131,
               'variables': 40, 'terms': terms, 'anchor': 0,
               'target_index': target, 'positive': (3, 16722) if target == 0 else None,
               'width': width}


def main():
    cfg = json.loads((HERE / 'prepare_protocol.json').read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_WIDE8_PREPARATION'
    assert cfg['left_free_bits'] == 8
    assert sha(__file__) == cfg['script_sha256']
    for item in cfg['sources'].values():
        assert sha(item['path']) == item['sha256']
    started = time.monotonic()
    output = []
    for record in instances():
        poly = product_anf(record['terms'], record['anchor'], record['width'])
        assert max(mask.bit_count() for mask in poly) <= 4
        if record['positive'] is not None:
            assert evaluate(poly, *record['positive'], record['anchor'],
                            record['width']) == 0
        supports = coordinate_supports(poly, record['field_bits'])
        path = HERE / (record['label'] + '.eqs')
        write_equations(path, record['variables'], record['field_bits'], supports)
        output.append({'label': record['label'], 'field_degree': record['field_bits'],
                       'variables': record['variables'], 'target_index': record['target_index'],
                       'anchor': record['anchor'], 'left_free_bits': record['width'],
                       'anf_terms': len(poly), 'support_entries': sum(map(len, supports)),
                       'positive': record['positive'], 'path': str(path),
                       'sha256': sha(path)})
    assert [item['label'] for item in output] == cfg['labels']
    result = {'status': 'PASS_WIDE8_PREPARATION', 'candidate_id': None,
              'curve_ids': cfg['curve_ids'], 'outputs': output,
              'wall_seconds': time.monotonic() - started,
              'protocol_sha256': sha(HERE / 'prepare_protocol.json'),
              'script_sha256': sha(__file__)}
    (HERE / 'prepare_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'wall_seconds': result['wall_seconds'],
                      'outputs': [(item['label'], item['anf_terms']) for item in output]},
                     sort_keys=True))


if __name__ == '__main__':
    main()
