"""Add an exact target-translated final-pair w-domain BDD to the N41 XCNF."""
import hashlib
import importlib.util
import json
import resource
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "build_protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol["sources"].items():
    assert sha(path) == expected, path
assert not (HERE / "formula.xcnf").exists()
assert protocol["curve_id"] == "EC1N41Ckb1h7d5e80d3c4d0"
assert protocol["bit_order"] == list(range(41))


def timeout(_signum, _frame):
    raise TimeoutError("target-w BDD build cap")


signal.signal(signal.SIGALRM, timeout)
signal.alarm(protocol["wall_cap_seconds"])
started = time.monotonic()
spec = importlib.util.spec_from_file_location("n41_group", protocol["group_source"])
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
F = module.Field()
source = json.loads(Path(protocol["states"]).read_text())
fixture = json.loads(Path(protocol["fixture"]).read_text())
wires = json.loads(Path(protocol["wires"]).read_text())
base_result = json.loads(Path(protocol["base_build_result"]).read_text())
base = Path(protocol["base_formula"]).read_bytes()
old_header = b"p cnf 123218 339484\n"
assert base.startswith(old_header)
assert sha(protocol["base_formula"]) == base_result["formula_sha256"]
assert wires["public_reciprocal"] == fixture["public_reciprocal"]
assert len(wires["intermediate_reciprocal"]) == 41
assert len(source["states"][4]) == 284
bits = [i for i in range(9) if i != 5]
allowed = set(wires["allowed_code_words"])


def code_of_state(state):
    mask = state["masks"][0]
    return sum(((mask >> bit) & 1) << j for j, bit in enumerate(bits))


Q = tuple(fixture["public_point"])
table = []
for state_id, state in enumerate(source["states"][4]):
    x, y = state["point"]
    residual = module.add(F, Q, (x, x ^ y))
    assert residual is not None and residual[0] != 0
    code = code_of_state(state)
    assert code in allowed
    table.append({"w": F.inv(residual[0]), "code": code,
                  "final_state_id": state_id})
table.sort(key=lambda row: row["w"])
assert len(table) == len({row["w"] for row in table}) == 284
assert len({row["code"] for row in table}) == 71
assert (next(row for row in table if row["final_state_id"] ==
             fixture["state_ids"][4])["w"] ==
        json.loads(Path(protocol["witness"]).read_text())["intermediate_reciprocal"])
table_end = time.monotonic()

source_words = tuple(row["w"] for row in table)
wires_w = wires["intermediate_reciprocal"]
nodes = []
cache = {}
next_variable = base_result["variables"]


def node(level, values):
    global next_variable
    if not values:
        return False
    if level == 41:
        assert len(values) == 1
        return True
    key = level, values
    if key in cache:
        return cache[key]
    bit = protocol["bit_order"][level]
    low = tuple(value for value in values if not (value >> bit) & 1)
    high = tuple(value for value in values if (value >> bit) & 1)
    lo = node(level+1, low)
    hi = node(level+1, high)
    if lo == hi:
        out = lo
    else:
        next_variable += 1
        out = next_variable
        nodes.append((out, wires_w[bit], lo, hi))
    cache[key] = out
    return out


root = node(0, source_words)
assert isinstance(root, int) and not isinstance(root, bool)


def negate(value):
    return not value if isinstance(value, bool) else -value


clauses = []


def clause(literals):
    if any(value is True for value in literals):
        return
    row = tuple(value for value in literals if value is not False)
    assert row and all(isinstance(value, int) and not isinstance(value, bool)
                       for value in row)
    if any(-value in row for value in row):
        return
    clauses.append(row)


for output, selector, lo, hi in nodes:
    clause((-selector, -output, hi))
    clause((-selector, output, negate(hi)))
    clause((selector, -output, lo))
    clause((selector, output, negate(lo)))
clause((root,))
assert clauses[-1] == (root,)


def evaluates_at(value):
    assignment = {wire: (value >> bit) & 1 for bit, wire in enumerate(wires_w)}

    def get(literal):
        if isinstance(literal, bool):
            return literal
        return bool(assignment[abs(literal)]) if literal > 0 else not bool(assignment[-literal])

    for output, selector, lo, hi in nodes:
        assignment[output] = get(hi if assignment[selector] else lo)
    assert all(any(get(literal) for literal in row) for row in clauses[:-1])
    return bool(assignment[root])


assert all(evaluates_at(row["w"]) for row in table)
negative_controls = tuple(value for value in range(4) if value not in source_words)[:2]
assert len(negative_controls) == 2
assert all(not evaluates_at(value) for value in negative_controls)
bdd_end = time.monotonic()

new_header = f"p cnf {next_variable} {339484+len(clauses)}\n".encode()
serialized = b"".join((" ".join(map(str, row))+" 0\n").encode() for row in clauses)
formula = new_header + base[len(old_header):] + serialized
(HERE / "formula.xcnf").write_bytes(formula)
(HERE / "w_table.json").write_text(json.dumps(table, sort_keys=True,
                                              separators=(",", ":"))+"\n")
finished = time.monotonic()
signal.alarm(0)
receipt = {"status": "PASS_EXACT_TARGET_W_BDD_BUILD",
           "curve_id": protocol["curve_id"], "candidate_id": None,
           "public_point": fixture["public_point"],
           "table_entries": len(table), "distinct_w": len(source_words),
           "distinct_codes": len(allowed),
           "bdd_nodes": len(nodes), "bdd_clauses": len(clauses),
           "variables": next_variable,
           "constraints": 339484+len(clauses),
           "formula_bytes": len(formula),
           "formula_sha256": sha(HERE / "formula.xcnf"),
           "table_sha256": sha(HERE / "w_table.json"),
           "positive_w_accepted": True,
           "phase_seconds": {"source_and_table": table_end-started,
                             "bdd_and_controls": bdd_end-table_end,
                             "serialization": finished-bdd_end},
           "total_seconds": finished-started,
           "self_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
           "protocol_sha256": sha(HERE / "build_protocol.json")}
(HERE / "build_result.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
print(json.dumps({k:receipt[k] for k in ("status","table_entries","bdd_nodes",
                                         "bdd_clauses","formula_bytes",
                                         "total_seconds")},sort_keys=True))
