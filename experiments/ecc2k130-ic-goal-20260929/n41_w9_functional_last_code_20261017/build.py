"""Add a guarded functional last-code decoder to the frozen N41 tower."""
import hashlib
import importlib.util
import json
import resource
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol["sources"].items():
    assert sha(path) == expected, path
assert not (HERE / "formula.xcnf").exists()


def timeout(_signal, _frame):
    raise TimeoutError("frozen functional-decoder build cap")


signal.signal(signal.SIGALRM, timeout)
signal.alarm(protocol["wall_cap_seconds"])
started = time.monotonic()
sys.path.insert(0, str(Path(protocol["karatsuba_source"]).parent))
sys.path.append(str(Path(protocol["inverse_source"]).parent))
sys.path.insert(0, str(Path(protocol["field_dependency_source"]).parent))
from karatsuba_circuit import KaratsubaCircuit  # noqa: E402
from functional_inverse_circuit import inverse  # noqa: E402

spec = importlib.util.spec_from_file_location("functional_decoder_field", protocol["field_source"])
field_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = field_module
spec.loader.exec_module(field_module)
field = field_module.Field()
source = json.loads(Path(protocol["states"]).read_text())
fixture = json.loads(Path(protocol["fixture"]).read_text())
wires = json.loads(Path(protocol["wires"]).read_text())
table = json.loads(Path(protocol["table"]).read_text())
base_path = Path(protocol["base_formula"])
header = base_path.open().readline().split()
assert header[:2] == ["p", "cnf"]
base_variables, base_rows = map(int, header[2:])
assert base_variables == 123218 and base_rows == 339484
assert len(table) == 284


def frob(value, steps):
    for _ in range(steps):
        value = field.square(value)
    return value


seed = source["seed"] << 1
h = frob(field.square(field.halftrace(seed)), 24)
c = h ^ 1
t = fixture["public_reciprocal"]
basis = [frob(field.mul((1 << bit) << 1, ((1 << bit) << 1) ^ seed), 24)
         for bit in range(9) if bit != 5]
assert len(basis) == 8
code_inputs = wires["codes"][4]
w_inputs = wires["intermediate_reciprocal"]
assert len(code_inputs) == 8 and len(w_inputs) == 41
assert max(code_inputs + w_inputs) <= base_variables

def numeric_coefficients(w):
    B = field.mul(t, w)
    A = 1 ^ field.square(B)
    D = field.square(t) ^ field.square(w)
    M = field.mul(A, h) ^ field.mul(c, D)
    a = field.mul(A, D)
    b = field.mul(B, M)
    q = field.square(M) ^ field.mul(field.mul(c, h), field.square(B))
    return a, b, q


def halftrace_value(value):
    out = 0
    for _ in range(21):
        out ^= value
        value = field.square(field.square(value))
    return out


def numeric_branch(w, code):
    a, b, q = numeric_coefficients(w)
    assert a and b
    rhs = field.mul(field.mul(q, a), field.inv(field.square(b)))
    step = field.mul(b, field.inv(a))
    p0 = field.mul(step, halftrace_value(rhs))
    product = 0
    for bit, value in enumerate(basis):
        if code >> bit & 1:
            product ^= value
    assert field.mul(a, field.square(product)) ^ field.mul(b, product) == q
    if product == p0:
        return 0
    assert product == p0 ^ step
    return 1


assert all(numeric_coefficients(row["w"])[0] and
           numeric_coefficients(row["w"])[1] for row in table)
branches = [numeric_branch(row["w"], row["code"]) for row in table]

circuit = KaratsubaCircuit(41, [0, 3])
circuit.next_var = base_variables + 1
branch = circuit.variable()
one = circuit.constant(1)
w = w_inputs
B = circuit.mul(circuit.constant(t), w)
A = circuit.add(one, circuit.square(B))
D = circuit.add(circuit.constant(field.square(t)), circuit.square(w))
M = circuit.add(circuit.mul(A, circuit.constant(h)),
                circuit.mul(circuit.constant(c), D))
a = circuit.mul(A, D)
b = circuit.mul(B, M)
q = circuit.add(circuit.square(M),
                circuit.mul(circuit.constant(field.mul(c, h)), circuit.square(B)))
inverse_a = inverse(circuit, a)
inverse_b = inverse(circuit, b)
rhs = circuit.mul(circuit.mul(q, a), circuit.square(inverse_b))

# Halftrace is an F2-linear map even when its argument has trace one.
images = [halftrace_value(1 << bit) for bit in range(41)]
halftrace = circuit.linear_element(rhs, images)
step = circuit.mul(b, inverse_a)
p0 = circuit.mul(step, halftrace)
p = circuit.add(p0, [circuit.and_(branch, bit) for bit in step])
product = circuit.linear_element(code_inputs, basis)


def or_all(items):
    out = 0
    for bit in items:
        out = circuit.xor((out, bit, circuit.and_(out, bit)))
    return out


regular = circuit.and_(or_all(a), or_all(b))
for left, right in zip(p, product):
    difference = circuit.xor((left, right))
    circuit.require_zero([circuit.and_(regular, difference)])
construction_end = time.monotonic()

# Evaluate every extension gate on distributed positive controls. The frozen
# base formula already has an independently checked full assignment.
def evaluate(row, root_bit):
    values = {wire: (row["w"] >> bit) & 1 for bit, wire in enumerate(w_inputs)}
    values.update({wire: (row["code"] >> bit) & 1
                   for bit, wire in enumerate(code_inputs)})
    values[branch] = root_bit
    definitions = {out: ("and", pair) for pair, out in circuit.and_cache.items()}
    for line in circuit.xors:
        literals = [int(v) for v in line.split()[1:-1]]
        definitions[abs(literals[0])] = ("xor", literals)

    def value(wire):
        return 0 if wire == 0 else 1 if wire == -1 else values[wire]

    for wire in range(base_variables + 2, circuit.next_var):
        kind, data = definitions[wire]
        if kind == "and":
            values[wire] = value(data[0]) & value(data[1])
        else:
            bit = int(data[0] > 0)
            for literal in data[1:]:
                bit ^= value(abs(literal)) ^ int(literal < 0)
            values[wire] = bit
    for line in circuit.clauses:
        literals = [int(v) for v in line.split()[:-1]]
        assert any(value(abs(v)) == int(v > 0) for v in literals), line
    for line in circuit.xors:
        literals = [int(v) for v in line.split()[1:-1]]
        assert sum(value(abs(v)) ^ int(v < 0) for v in literals) & 1, line
    return len(values)


control_indices = sorted(set(range(0, len(table), 19)) | {len(table)-1})
evaluated = [evaluate(table[i], branches[i]) for i in control_indices]
controls_end = time.monotonic()

with (HERE / "formula.xcnf").open("w") as out, base_path.open() as inp:
    out.write(f"p cnf {circuit.next_var-1} "
              f"{base_rows+len(circuit.clauses)+len(circuit.xors)}\n")
    inp.readline()
    for line in inp:
        out.write(line)
    for line in circuit.clauses:
        out.write(line + "\n")
    for line in circuit.xors:
        out.write(line + "\n")
finished = time.monotonic()
signal.alarm(0)
result = {
    "status": "PASS_N41_GUARDED_FUNCTIONAL_LAST_CODE_BUILD",
    "candidate_id": None, "curve_id": protocol["curve_id"],
    "base_variables": base_variables, "base_rows": base_rows,
    "extension_and_gates": circuit.and_count,
    "extension_clauses": len(circuit.clauses),
    "extension_native_xor_rows": len(circuit.xors),
    "variables": circuit.next_var-1,
    "formula_bytes": (HERE / "formula.xcnf").stat().st_size,
    "formula_sha256": sha(HERE / "formula.xcnf"),
    "source_positive_count": len(table),
    "root_choice_counts": {str(bit): branches.count(bit) for bit in (0, 1)},
    "extension_assignments_checked": len(evaluated),
    "extension_assignment_sizes": [min(evaluated), max(evaluated)],
    "phase_seconds": {"construction": construction_end-started,
                      "assignment_controls": controls_end-construction_end,
                      "serialization": finished-controls_end},
    "total_seconds": finished-started,
    "self_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    "protocol_sha256": sha(HERE / "protocol.json"),
    "branch_wire": branch,
}
(HERE / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2)+"\n")
print(json.dumps(result, sort_keys=True))
