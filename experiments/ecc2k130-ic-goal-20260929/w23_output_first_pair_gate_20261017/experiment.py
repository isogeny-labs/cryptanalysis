"""Exact W23 pair gate comparison, with a checked constructed assignment."""
import hashlib
import json
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n131_w23_sixpair_shared_circuit_20261017'
sys.path.insert(0, str(SOURCE))
import circuit as src
sys.path.insert(0, str(ROOT / 'n131_w20_selector_elimination_v2_20261013'))
import selector


def xor(values):
    result = 0
    for value in values:
        result ^= value
    return result


def decoder():
    """Invert 22 independent coordinate rows of the product basis."""
    rank = len(src.PB)
    pivots, rows = [], []
    independent = {}
    for coordinate in range(src.N):
        row = sum(((value >> coordinate) & 1) << j
                  for j, value in enumerate(src.PB))
        reduced = row
        while reduced:
            leading = reduced.bit_length() - 1
            if leading in independent:
                reduced ^= independent[leading]
            else:
                independent[leading] = reduced
                pivots.append(coordinate)
                rows.append(row)
                break
        if len(rows) == rank:
            break
    assert len(rows) == rank
    aug = [row | (1 << (rank + i)) for i, row in enumerate(rows)]
    for col in range(rank):
        pivot = next(i for i in range(col, rank) if aug[i] >> col & 1)
        aug[col], aug[pivot] = aug[pivot], aug[col]
        for i in range(rank):
            if i != col and aug[i] >> col & 1:
                aug[i] ^= aug[col]
    assert [row & ((1 << rank) - 1) for row in aug] == [1 << i for i in range(rank)]
    inverse = [row >> rank for row in aug]
    code_images = [xor(1 << j for j, row in enumerate(inverse) if row >> i & 1)
                   for i in range(rank)]
    product_images = [xor(src.PB[j] for j in range(rank) if code_images[i] >> j & 1)
                      for i in range(rank)]
    for j, value in enumerate(src.PB):
        assert selector.reconstruct(value, code_images, pivots) == 1 << j
        assert selector.reconstruct(value, product_images, pivots) == value
    return pivots, code_images, product_images


def source_gate(circ, alg, masks):
    circ.require_zero([circ.xor(w for w, v in zip(masks, src.BASE) if src.trace(v))])
    witness = [circ.variable() for _ in range(src.N)]
    tensor = {(i, j): circ.and_(masks[i], witness[j])
              for i in range(len(src.BITS)) for j in range(src.N)}
    pv = alg.expression((w, src.F.mul(src.PB[i], 1 << j)) for (i, j), w in tensor.items())
    av = alg.expression((w, src.F.mul(src.BASE[i], 1 << j)) for (i, j), w in tensor.items())
    circ.require_zero(alg.add(pv, alg.one).bits())
    circ.require_zero([circ.xor(w for w, t in zip(av.bits(), src.TRACE) if t)])
    circ.require_zero([circ.xor(w for j, w in enumerate(witness)
                            if src.trace(src.F.mul(src.SEED, 1 << j)))])
    return witness


def build(mode):
    circ = src.KaratsubaCircuit(src.N, src.TAPS)
    alg = src.Algebra(circ, src.F, dense_and_threshold=3000)
    if mode == 'code_first':
        masks = [circ.variable() for _ in src.BITS]
        z = [circ.variable() for _ in range(src.N)]
        p = alg.expression(zip(masks, src.PB))
        zz = alg.from_bits(z)
        cz2 = alg.expression((w, src.F.mul(src.C, basis))
                             for w, basis in alg.square(zz).terms)
        circ.require_zero(alg.add(cz2, alg.mul(p, zz),
                                  alg.expression(((-1, src.H),))).bits())
    else:
        assert mode == 'output_first'
        pivots, codes, products = decoder()
        z = [circ.variable() for _ in range(src.N)]
        inverse = [circ.variable() for _ in range(src.N)]
        columns = ([src.F.mul(src.C, 1 << i) for i in range(src.N)] +
                   [src.F.mul(src.H, 1 << i) for i in range(src.N)])
        wires = z + inverse
        code_columns = [selector.reconstruct(v, codes, pivots) for v in columns]
        error_columns = [v ^ selector.reconstruct(v, products, pivots)
                         for v in columns]
        masks = [circ.xor(w for w, value in zip(wires, code_columns) if value >> j & 1)
                 for j in range(len(src.BITS))]
        for bit in range(src.N):
            circ.require_zero([circ.xor(w for w, value in zip(wires, error_columns)
                                        if value >> bit & 1)])
        circ.require_zero(alg.add(alg.mul(alg.from_bits(z), alg.from_bits(inverse)),
                                  alg.one).bits())
    circ.clauses.append(' '.join(map(str, z)) + ' 0')
    witness = source_gate(circ, alg, masks)
    return circ, {'masks': masks, 'out': z, 'output_inverse': inverse if mode == 'output_first' else None,
                  'source_inverse': witness}, {
        'and_gates': circ.and_count, 'variables': circ.next_var - 1,
        'clauses': len(circ.clauses), 'xor_rows': len(circ.xors),
        'sparse_mul_calls': alg.sparse_mul_calls,
        'generic_mul_calls': alg.generic_mul_calls}


def bind(values, wires, value):
    values.update({wire: value >> i & 1 for i, wire in enumerate(wires)})


def main():
    fixture_path = SOURCE / 'fixture.json'
    fixture = json.loads(fixture_path.read_text())['pairs'][0]
    pivots, codes, products = decoder()
    rng = random.Random(20261017)
    for _ in range(1024):
        code = rng.getrandbits(len(src.BITS))
        product = xor(v for j, v in enumerate(src.PB) if code >> j & 1)
        assert selector.reconstruct(product, codes, pivots) == code
        assert product ^ selector.reconstruct(product, products, pivots) == 0
    z, inverse = fixture['output_reciprocal'], fixture['output_inv']
    assert src.F.mul(z, inverse) == 1
    assert src.F.mul(src.C, z) ^ src.F.mul(src.H, inverse) == fixture['source_product']
    rows = []
    for mode in ('code_first', 'output_first'):
        start = time.monotonic_ns()
        circ, wires, counts = build(mode)
        built = time.monotonic_ns()
        values = {}
        code = sum(((fixture['masks'][0] >> bit) & 1) << j
                   for j, bit in enumerate(src.BITS))
        if mode == 'code_first':
            bind(values, wires['masks'], code)
        bind(values, wires['out'], fixture['output_reciprocal'])
        if mode == 'output_first':
            bind(values, wires['output_inverse'], fixture['output_inv'])
        bind(values, wires['source_inverse'], fixture['source_inverse_product'])
        full = selector.old.complete_assignment(circ, values)
        assert [full[wire] for wire in wires['masks']] == [code >> j & 1 for j in range(len(src.BITS))]
        check = selector.old.check_assignment(circ, full)
        assert check['clauses'] == len(circ.clauses) and check['native_xor_rows'] == len(circ.xors)
        rows.append({'mode': mode, **counts, 'build_ns': built - start,
                     'check_ns': time.monotonic_ns() - built, 'check': check})
        print(json.dumps(rows[-1], sort_keys=True), flush=True)
    result = {'status': 'COMPLETE', 'candidate_id': None, 'rows': rows,
              'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in (Path(__file__), fixture_path, SOURCE / 'circuit.py',
                                          ROOT / 'n131_w18_allseed_fourpair_20261012/fourpair_v2.py',
                                          Path(selector.__file__), Path(selector.old.__file__),
                                          ROOT / 'n131_w20_output_inverse_linear_20261012/OutputLinearization.lean',
                                          ROOT / 'n131_w20_output_inverse_linear_20261012/lean-toolchain',
                                          HERE / 'sage_runtime_info.json')},
              'source_curve_id': json.loads(fixture_path.read_text())['curve_id'],
              'decoder_pivots': pivots,
              'decoder_rank': len(pivots), 'decoder_random_checks': 1024,
              'syndrome_codimension': src.N - len(pivots),
              'pair_field_identity_check': 'PASS'}
    (HERE / 'result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')


if __name__ == '__main__':
    main()
