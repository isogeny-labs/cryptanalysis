"""Direct bilinear leaves with two overlapping public-target S3 trees."""
import importlib.util
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
SOURCE = ROOT / "n41_s3_rationality_propagation_20261017" / "circuit.py"
spec = importlib.util.spec_from_file_location("n41_direct_leaf_base", SOURCE)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

F = base.F
N = base.N
LINKS = base.LINKS
old = base.old
DUAL_LINKS = ((0, 3, 6), (1, 4, 7), (2, 5, 8), (6, 7, 9), (9, 8, 10))


def build(target_reciprocal):
    machine, wires = base.build(target_reciprocal)
    leaf_and_count = machine.and_count
    alg = old.old.Algebra(machine, old.Field(), dense_and_threshold=3000)
    geometry = old.geometry()
    rotated = []
    for slot, output in enumerate(wires["outputs"]):
        images = [old.frob(1 << bit, geometry["rotations"][slot]) for bit in range(N)]
        rotated.append(alg.from_bits(machine.linear_element(output, images)))
    middle = [[machine.variable() for _ in range(N)] for _ in range(4)]
    branches = [machine.variable() for _ in range(5)]
    nodes = rotated + [alg.from_bits(row) for row in middle] + [
        alg.expression(((-1, target_reciprocal),))]
    ht_basis = []
    for bit in range(N):
        value, image = F.square(1 << bit), 0
        for _ in range((N + 1) // 2):
            image ^= value
            value = F.square(F.square(value))
        ht_basis.append(image)
    for gate, (left, right, out) in enumerate(DUAL_LINKS):
        a, b, z = nodes[left], nodes[right], nodes[out]
        total = alg.add(a, b, z)
        ht = machine.linear_element(total.bits(), ht_basis)
        machine.require_zero(alg.add(alg.mul(alg.mul(a, b), z),
                                     alg.from_bits(ht),
                                     alg.expression(((branches[gate], 1),))).bits())
        machine.require_zero([machine.xor(w for w, tr in zip(
            total.bits(), [old.trace(1 << k) for k in range(N)]) if tr)])
        if out < 10:
            machine.clauses.append(" ".join(map(str, middle[out - 6])) + " 0")
    wires["dual_middle"] = middle
    wires["dual_branches"] = branches
    wires["dual_links"] = DUAL_LINKS
    wires["first_tree_and_count"] = leaf_and_count
    return machine, wires
