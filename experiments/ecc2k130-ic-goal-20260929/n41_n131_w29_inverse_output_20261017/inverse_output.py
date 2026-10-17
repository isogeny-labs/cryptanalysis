"""Exact fixed-seed five-pair circuits with masks decoded from output inverses."""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
N41_PRIOR = ROOT / 'n41_w9_lazy_source_20261017/circuit.py'
N131_PRIOR = ROOT / 'n41_n131_fivepair_w9_w29_20261017/circuit_n131_3p2.py'


def import_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


n41 = import_file('w9_inverse_output_parent', N41_PRIOR)
n131 = import_file('w29_inverse_output_parent', N131_PRIOR)


def projection(basis, n):
    """Invert a full-rank binary source-product map using coordinate rows."""
    d = len(basis)
    coordinate_rows = [sum(((value >> bit) & 1) << i
                           for i, value in enumerate(basis)) for bit in range(n)]
    echelon = {}
    pivots = []
    for bit, row in enumerate(coordinate_rows):
        residual = row
        while residual:
            high = residual.bit_length() - 1
            if high not in echelon:
                echelon[high] = residual
                pivots.append(bit)
                break
            residual ^= echelon[high]
        if len(pivots) == d:
            break
    assert len(pivots) == d
    aug = [coordinate_rows[p] | (1 << (d + i)) for i, p in enumerate(pivots)]
    for col in range(d):
        index = next(i for i in range(col, d) if aug[i] >> col & 1)
        aug[col], aug[index] = aug[index], aug[col]
        for i in range(d):
            if i != col and aug[i] >> col & 1:
                aug[i] ^= aug[col]
    assert [row & ((1 << d) - 1) for row in aug] == [1 << i for i in range(d)]
    inverse_rows = [row >> d for row in aug]

    def decode(value):
        selected = sum(((value >> pivot) & 1) << i for i, pivot in enumerate(pivots))
        return sum(((inverse_rows[i] & selected).bit_count() & 1) << i
                   for i in range(d))

    assert all(decode(value) == 1 << i for i, value in enumerate(basis))
    return {'pivots': pivots, 'inverse_rows': inverse_rows,
            'basis_rank': d, 'decode': decode}


def build(target, field_name, add_target_trace=False):
    assert field_name in ('n41', 'n131') and target
    design = n41 if field_name == 'n41' else n131
    F = design.F
    n = design.N
    source_bits = design.BITS
    base = design.BASE
    product_basis = design.PB
    seed = design.SEED
    H = design.H
    C = design.C
    rotations = design.ROTATIONS
    links = design.LINKS
    trace = design.trace if field_name == 'n41' else design.previous.trace
    alg_class = design.Algebra if field_name == 'n41' else design.previous.Algebra
    circuit_class = design.KaratsubaCircuit if field_name == 'n41' else design.previous.KaratsubaCircuit
    trace_basis = design.TRACE
    decoder = projection(product_basis, n)
    circ = circuit_class(n, design.TAPS)
    alg = alg_class(circ, F, dense_and_threshold=3000)
    wires = {'mask': [], 'out': [], 'output_inverse': [],
             'source_inverse': [], 'middle': []}
    nodes = []
    for rotation in rotations:
        z = [circ.variable() for _ in range(n)]
        q = [circ.variable() for _ in range(n)]
        wires['out'].append(z)
        wires['output_inverse'].append(q)
        zz = alg.from_bits(z)
        qq = alg.from_bits(q)
        circ.require_zero(alg.add(alg.mul(zz, qq), alg.one).bits())
        circ.clauses.append(' '.join(map(str, z)) + ' 0')

        pbits = circ.linear_element(z + q,
            [F.mul(C, 1 << i) for i in range(n)] +
            [F.mul(H, 1 << i) for i in range(n)])
        masks = [circ.xor(pbits[decoder['pivots'][j]]
                          for j in range(len(source_bits))
                          if decoder['inverse_rows'][i] >> j & 1)
                 for i in range(len(source_bits))]
        wires['mask'].append(masks)
        product = alg.expression(zip(masks, product_basis))
        circ.require_zero(alg.add(alg.from_bits(pbits), product).bits())
        # The representative has source a in the canonical seed half-space.
        source = alg.expression(zip(masks, base))
        circ.require_zero([circ.xor(w for w, value in zip(masks, base)
                                    if trace(value))])

        v = [circ.variable() for _ in range(n)]
        wires['source_inverse'].append(v)
        tensor = {(i, j): circ.and_(masks[i], v[j])
                  for i in range(len(source_bits)) for j in range(n)}
        pv = alg.expression((wire, F.mul(product_basis[i], 1 << j))
                            for (i, j), wire in tensor.items())
        av = alg.expression((wire, F.mul(base[i], 1 << j))
                            for (i, j), wire in tensor.items())
        circ.require_zero(alg.add(pv, alg.one).bits())
        circ.require_zero([circ.xor(w for w, tr in zip(av.bits(), trace_basis) if tr)])
        circ.require_zero([circ.xor(w for j, w in enumerate(v)
                                    if trace(F.mul(seed, 1 << j)))])
        rotated = circ.linear_element(z, [F.frob(1 << i, rotation) for i in range(n)])
        nodes.append(alg.from_bits(rotated))
    for _ in range(3):
        middle = [circ.variable() for _ in range(n)]
        wires['middle'].append(middle)
        circ.clauses.append(' '.join(map(str, middle)) + ' 0')
        nodes.append(alg.from_bits(middle))
    nodes.append(alg.expression(((-1, target),)))
    for i, j, k in links:
        a, b, z = nodes[i], nodes[j], nodes[k]
        ab = alg.mul(a, b)
        abz = alg.mul(ab, z)
        circ.require_zero(alg.add(alg.square(abz), abz,
                                  alg.square(alg.add(a, b)), alg.square(z)).bits())
    if add_target_trace:
        parity_wires = [wire for row in wires['out']
                        for wire, bit in zip(row, trace_basis) if bit]
        circ.require_zero([circ.xor(parity_wires + ([-1] if trace(target) else []))])
    counts = {'and_gates': circ.and_count, 'variables': circ.next_var - 1,
              'clauses': len(circ.clauses), 'xor_rows': len(circ.xors),
              'sparse_mul_calls': alg.sparse_mul_calls,
              'generic_mul_calls': alg.generic_mul_calls}
    decoder_public = {key: value for key, value in decoder.items() if key != 'decode'}
    return circ, wires, counts, decoder_public
