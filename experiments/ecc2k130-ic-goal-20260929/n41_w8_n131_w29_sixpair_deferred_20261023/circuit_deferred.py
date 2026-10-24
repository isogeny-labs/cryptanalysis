"""Six pair-code circuit with three exact source gates and three deferred gates."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
prior_path = ROOT / "n41_w8_sixpair_sat_20261016/circuit.py"
spec = importlib.util.spec_from_file_location("n41_w8_sixpair_prior", prior_path)
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)

F = prior.F
N = 41
BITS = [0, 1, 2, 3, 4, 6, 7]
BASE = [1 << (bit + 1) for bit in BITS]
SEED = 56 << 1
PB = [F.square(a) ^ F.mul(SEED, a) for a in BASE]
H = F.square(F.halftrace(SEED))
C = 1 ^ H
TRACE = [prior.trace(1 << i) for i in range(N)]
ROTATIONS = [0, 6, 12, 18, 24, 30]
LINKS = prior.BALANCED_LINKS
assert len(BITS) == 7 and len(set(PB)) == 7 and H and C


def build(target, exact_slots=(0, 1, 2)):
    assert target and tuple(sorted(exact_slots)) == tuple(exact_slots)
    circ = prior.old.KaratsubaCircuit(N, [0, 3])
    alg = prior.old.Algebra(circ, prior.Field(), dense_and_threshold=3000)
    wires = {"mask": [], "out": [], "source_inverse": [], "middle": []}
    nodes = []
    for slot, rotation in enumerate(ROTATIONS):
        masks = [circ.variable() for _ in BITS]
        wires["mask"].append(masks)
        circ.clauses.append(" ".join(map(str, masks)) + " 0")
        product = alg.expression(zip(masks, PB))
        if slot in exact_slots:
            circ.require_zero([circ.xor(w for w, a in zip(masks, BASE)
                                        if prior.trace(a))])
            inverse = [circ.variable() for _ in range(N)]
            wires["source_inverse"].append(inverse)
            tensor = {(i, j): circ.and_(masks[i], inverse[j])
                      for i in range(len(BITS)) for j in range(N)}
            product_inverse = alg.expression(
                (w, F.mul(PB[i], 1 << j)) for (i, j), w in tensor.items())
            source_inverse = alg.expression(
                (w, F.mul(BASE[i], 1 << j)) for (i, j), w in tensor.items())
            circ.require_zero(alg.add(product_inverse, alg.one).bits())
            circ.require_zero([circ.xor(w for w, tr in zip(source_inverse.bits(), TRACE) if tr)])
            circ.require_zero([circ.xor(w for j, w in enumerate(inverse)
                                        if prior.trace(F.mul(SEED, 1 << j)))])
        else:
            wires["source_inverse"].append(None)
        out = [circ.variable() for _ in range(N)]
        wires["out"].append(out)
        circ.clauses.append(" ".join(map(str, out)) + " 0")
        z = alg.from_bits(out)
        cz2 = alg.expression((w, F.mul(C, basis)) for w, basis in alg.square(z).terms)
        circ.require_zero(alg.add(cz2, alg.mul(product, z),
                                  alg.expression(((-1, H),))).bits())
        rotated = circ.linear_element(out, [prior.frob(1 << i, rotation)
                                           for i in range(N)])
        nodes.append(alg.from_bits(rotated))
    for i in range(len(wires["mask"])):
        for j in range(i + 1, len(wires["mask"])):
            for code in range(1 << len(BITS)):
                literals = [(-w if code >> k & 1 else w)
                            for k, w in enumerate(wires["mask"][i])]
                literals += [(-w if code >> k & 1 else w)
                             for k, w in enumerate(wires["mask"][j])]
                circ.clauses.append(" ".join(map(str, literals)) + " 0")
    for _ in range(4):
        middle = [circ.variable() for _ in range(N)]
        wires["middle"].append(middle)
        circ.clauses.append(" ".join(map(str, middle)) + " 0")
        nodes.append(alg.from_bits(middle))
    nodes.append(alg.expression(((-1, target),)))
    for i, j, k in LINKS:
        a, b, z = nodes[i], nodes[j], nodes[k]
        ab = alg.mul(a, b)
        abz = alg.mul(ab, z)
        circ.require_zero(alg.add(alg.square(abz), abz,
                                  alg.square(alg.add(a, b)), alg.square(z)).bits())
    counts = {"and_gates": circ.and_count, "variables": circ.next_var - 1,
              "clauses": len(circ.clauses), "native_xor_rows": len(circ.xors),
              "generic_mul_calls": alg.generic_mul_calls,
              "sparse_mul_calls": alg.sparse_mul_calls}
    return circ, wires, counts
