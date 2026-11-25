"""Six-slot N41 public query: three-code norm joined to an explicit right triple."""
import importlib.util
import sys
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
DIRECT = ROOT / "n41_s3_direct_orbit_20261017/circuit.py"
NORM = ROOT / "n41_three_code_nested_norm_20261015"
sys.path.insert(0, str(NORM))
from three_norm import Ops, three_source_norm

spec = importlib.util.spec_from_file_location("n41_direct_hybrid_source", DIRECT)
direct = importlib.util.module_from_spec(spec)
spec.loader.exec_module(direct)
F = direct.F
N = 41


def nonzero(machine, wires):
    machine.clauses.append(" ".join(map(str, wires)) + " 0")


def build(target_reciprocal):
    geometry = direct.old.geometry()
    seed_mask = geometry["fixed_seed_sum_code"]
    bits = [i for i in range(8) if i != seed_mask.bit_length() - 1]
    allowed = {sum(((mask >> bit) & 1) << j for j, bit in enumerate(bits)): mask
               for mask in geometry["permitted_canonical_a"]}
    assert len(bits) == 7 and len(allowed) == 40
    machine = direct.old.old.KaratsubaCircuit(N, [0, 3])
    algebra = direct.old.old.Algebra(machine, direct.old.Field(), dense_and_threshold=3000)
    code_wires = [[machine.variable() for _ in bits] for _ in range(6)]
    for wires in code_wires:
        for forbidden in range(1 << 7):
            if forbidden not in allowed:
                machine.clauses.append(" ".join(
                    str(-wire if forbidden >> j & 1 else wire)
                    for j, wire in enumerate(wires)) + " 0")
    columns = {int(key): value for key, value in geometry["mask_columns"].items()}
    def mismatch(wires, code):
        return [-wire if code >> j & 1 else wire for j, wire in enumerate(wires)]
    for i in range(6):
        for j in range(i + 1, 6):
            for a_code, a in allowed.items():
                a_columns = {columns[a], columns[a ^ seed_mask]}
                for b_code, b in allowed.items():
                    if a_columns & {columns[b], columns[b ^ seed_mask]}:
                        machine.clauses.append(" ".join(map(str,
                            mismatch(code_wires[i], a_code) + mismatch(code_wires[j], b_code))) + " 0")

    # The left three source x roots are eliminated inside their quadratic
    # algebras. Only their source-code bits and output reciprocal remain.
    left_bits = [machine.variable() for _ in range(N)]
    nonzero(machine, left_bits)
    seed = F.square(geometry["blocks"][0]["s"]) ^ geometry["blocks"][0]["s"]
    h2 = F.square(F.halftrace(seed))
    product_basis = geometry["blocks"][0]["product_basis"]
    coefficients = []
    for slot in range(3):
        rotation = geometry["rotations"][slot]
        hs = direct.old.frob(h2, rotation)
        leading = 1 ^ hs
        assert leading
        inv_leading = F.inv(leading)
        alpha = algebra.expression((wire,
            F.mul(direct.old.frob(product_basis[bit], rotation), inv_leading))
            for wire, bit in zip(code_wires[slot], bits))
        beta = algebra.expression(((-1, F.mul(hs, inv_leading)),))
        coefficients.extend((alpha, beta))
    operations = Ops(algebra.zero, algebra.one, algebra.add, algebra.mul)
    operations.square = algebra.square
    norm = three_source_norm(*coefficients, algebra.from_bits(left_bits), operations)
    machine.require_zero(norm.bits())
    norm_checkpoint = machine.and_count

    # Right source points retain explicit pair-output reciprocal roots.
    outputs = []
    rotated = []
    product_basis = geometry["blocks"][0]["product_basis"]
    seed = geometry["blocks"][0]["s"]
    seed_plus_one = algebra.expression(((-1, seed ^ 1),))
    seed_constant = algebra.expression(((-1, seed),))
    for slot in range(3, 6):
        c_bits = [machine.variable() for _ in range(N)]
        nonzero(machine, c_bits)
        machine.clauses.append(" ".join(map(str, [-c_bits[0], *c_bits[1:]])) + " 0")
        product = algebra.expression((wire, product_basis[bit])
                                     for wire, bit in zip(code_wires[slot], bits))
        c = algebra.from_bits(c_bits)
        affine = algebra.add(algebra.mul(seed_plus_one, c), seed_constant)
        machine.require_zero(algebra.add(algebra.mul(product, c),
                                          algebra.square(affine)).bits())
        images = [direct.old.frob(1 << bit, geometry["rotations"][slot])
                  for bit in range(N)]
        rotated.append(algebra.from_bits(machine.linear_element(c_bits, images)))
        outputs.append(c_bits)
    right34 = [machine.variable() for _ in range(N)]
    right345 = [machine.variable() for _ in range(N)]
    nonzero(machine, right34)
    nonzero(machine, right345)
    branches = [machine.variable() for _ in range(3)]
    ht_basis = []
    for bit in range(N):
        value, image = F.square(1 << bit), 0
        for _ in range((N + 1) // 2):
            image ^= value
            value = F.square(F.square(value))
        ht_basis.append(image)
    target = algebra.expression(((-1, target_reciprocal),))
    links = [
        (rotated[0], rotated[1], algebra.from_bits(right34)),
        (algebra.from_bits(right34), rotated[2], algebra.from_bits(right345)),
        (algebra.from_bits(left_bits), algebra.from_bits(right345), target),
    ]
    trace_basis = [direct.old.trace(1 << bit) for bit in range(N)]
    for gate, (a, b, z) in enumerate(links):
        total = algebra.add(a, b, z)
        ht = machine.linear_element(total.bits(), ht_basis)
        machine.require_zero(algebra.add(algebra.mul(algebra.mul(a, b), z),
                          algebra.from_bits(ht),
                          algebra.expression(((branches[gate], 1),))).bits())
        machine.require_zero([machine.xor(w for w, trace_bit in
            zip(total.bits(), trace_basis) if trace_bit)])
    return machine, {"codes": code_wires, "source_bits": bits,
                     "left_sum": left_bits, "right_outputs": outputs,
                     "right34": right34, "right345": right345,
                     "branches": branches, "norm_checkpoint": norm_checkpoint,
                     "target_reciprocal": target_reciprocal}
