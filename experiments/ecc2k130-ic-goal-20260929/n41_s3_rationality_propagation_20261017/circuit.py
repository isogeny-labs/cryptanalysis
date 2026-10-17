"""Six-pair N41 S3 tree with a direct bilinear product-image leaf gate."""
import importlib.util
from pathlib import Path


D = Path(__file__).resolve().parent
ROOT = D.parent
OLD = ROOT / "n41_sixpair_shared_target_20261017" / "circuit.py"
spec = importlib.util.spec_from_file_location("n41_previous_circuit", OLD)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)

F = old.F
N = 41
LINKS = old.BALANCED_LINKS


def nonzero(machine, wires):
    machine.clauses.append(" ".join(map(str, wires)) + " 0")


def not_one(machine, wires):
    machine.clauses.append(" ".join(map(str, [-wires[0], *wires[1:]])) + " 0")


def build(target_reciprocal):
    g = old.geometry()
    seed_mask = g["fixed_seed_sum_code"]
    bits = [i for i in range(8) if i != seed_mask.bit_length() - 1]
    allowed = {sum(((mask >> bit) & 1) << j for j, bit in enumerate(bits)):
               mask for mask in g["permitted_canonical_a"]}
    assert len(allowed) == 40 and len(bits) == 7
    product_basis = g["blocks"][0]["product_basis"]
    seed = g["blocks"][0]["s"]
    machine = old.old.KaratsubaCircuit(N, [0, 3])
    alg = old.old.Algebra(machine, old.Field(), dense_and_threshold=3000)
    codes, outputs, rotated = [], [], []
    leaf_checkpoints = []
    for rotation in g["rotations"][:6]:
        code = [machine.variable() for _ in bits]
        c_bits = [machine.variable() for _ in range(N)]
        codes.append(code)
        outputs.append(c_bits)
        nonzero(machine, c_bits)
        not_one(machine, c_bits)
        for forbidden in range(1 << len(bits)):
            if forbidden in allowed:
                continue
            machine.clauses.append(" ".join(
                str(-wire if forbidden >> j & 1 else wire)
                for j, wire in enumerate(code)) + " 0")
        product = alg.expression((wire, product_basis[bit])
                                 for wire, bit in zip(code, bits))
        c = alg.from_bits(c_bits)
        seed_plus_one = alg.expression(((-1, seed ^ 1),))
        seed_const = alg.expression(((-1, seed),))
        affine = alg.add(alg.mul(seed_plus_one, c), seed_const)
        # P(a) c = ((s+1)c+s)^2; c is the unrotated reciprocal pair x.
        machine.require_zero(alg.add(alg.mul(product, c), alg.square(affine)).bits())
        leaf_checkpoints.append(machine.and_count)
        images = [old.frob(1 << i, rotation) for i in range(N)]
        rotated.append(alg.from_bits(machine.linear_element(c_bits, images)))
    columns = {int(k): v for k, v in g["mask_columns"].items()}
    def mismatch(wires, code):
        return [(-wire if code >> j & 1 else wire) for j, wire in enumerate(wires)]
    for i in range(6):
        for j in range(i + 1, 6):
            for a_code, a in allowed.items():
                acol = {columns[a], columns[a ^ seed_mask]}
                for b_code, b in allowed.items():
                    bcol = {columns[b], columns[b ^ seed_mask]}
                    if acol & bcol:
                        machine.clauses.append(" ".join(map(str,
                            mismatch(codes[i], a_code) + mismatch(codes[j], b_code))) + " 0")
    middle = [[machine.variable() for _ in range(N)] for _ in range(4)]
    branches = [machine.variable() for _ in range(5)]
    ht_basis = []
    for bit in range(N):
        value, image = F.square(1 << bit), 0
        for _ in range((N + 1) // 2):
            image ^= value
            value = F.square(F.square(value))
        ht_basis.append(image)
    nodes = rotated + [alg.from_bits(row) for row in middle] + [
        alg.expression(((-1, target_reciprocal),))]
    for gate, (left, right, out) in enumerate(LINKS):
        a, b, z = nodes[left], nodes[right], nodes[out]
        total = alg.add(a, b, z)
        ht = machine.linear_element(total.bits(), ht_basis)
        machine.require_zero(alg.add(alg.mul(alg.mul(a, b), z),
                                     alg.from_bits(ht),
                                     alg.expression(((branches[gate], 1),))).bits())
        machine.require_zero([machine.xor(w for w, t in zip(total.bits(),
                                                            [old.trace(1 << k) for k in range(N)]) if t)])
        if out < 10:
            nonzero(machine, middle[out - 6])
    return machine, {"codes": codes, "outputs": outputs, "middle": middle,
                     "branches": branches, "source_bits": bits,
                     "leaf_and_checkpoints": leaf_checkpoints,
                     "topology": LINKS}
