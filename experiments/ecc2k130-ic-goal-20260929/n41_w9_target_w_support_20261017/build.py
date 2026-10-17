"""Exact target-w and final-code support clauses on the frozen N41 circuit."""
import hashlib
import importlib.util
import json
import resource
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
p = json.loads((HERE / "build_protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in p["sources"].items():
    assert sha(path) == expected, path
assert not (HERE / "formula.xcnf").exists()
assert p["curve_id"] == "EC1N41Ckb1h7d5e80d3c4d0"


def timeout(_signum, _frame):
    raise TimeoutError("target-w support build cap")


signal.signal(signal.SIGALRM, timeout)
signal.alarm(p["wall_cap_seconds"])
started = time.monotonic()
spec = importlib.util.spec_from_file_location("n41_group", p["group_source"])
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
F = module.Field()
source = json.loads(Path(p["states"]).read_text())
fixture = json.loads(Path(p["fixture"]).read_text())
wires = json.loads(Path(p["wires"]).read_text())
base_result = json.loads(Path(p["base_build_result"]).read_text())
base = Path(p["base_formula"]).read_bytes()
old_header = b"p cnf 123218 339484\n"
assert base.startswith(old_header)
assert sha(p["base_formula"]) == base_result["formula_sha256"]
assert len(source["states"][4]) == 284
assert len(wires["intermediate_reciprocal"]) == 41
assert len(wires["codes"][4]) == 8
allowed = set(wires["allowed_code_words"])
bits = [i for i in range(9) if i != 5]
Q = tuple(fixture["public_point"])
table = []
for state_id, state in enumerate(source["states"][4]):
    x, y = state["point"]
    residual = module.add(F, Q, (x, x ^ y))
    assert residual is not None and residual[0] != 0
    mask = state["masks"][0]
    code = sum(((mask >> bit) & 1) << j for j, bit in enumerate(bits))
    assert code in allowed
    table.append({"w": F.inv(residual[0]), "code": code,
                  "final_state_id": state_id})
table.sort(key=lambda row: row["w"])
assert len(table) == len({row["w"] for row in table}) == 284
assert len({row["code"] for row in table}) == 71
assert [(row["w"],row["code"],row["final_state_id"]) for row in table] == [
    (row["w"],row["code"],row["final_state_id"]) for row in
    json.loads(Path(p["audited_table"]).read_text())]
table_end = time.monotonic()

selectors = list(range(base_result["variables"]+1,
                       base_result["variables"]+1+len(table)))
clauses = [tuple(selectors)]
for selector, row in zip(selectors, table):
    clauses.extend((-selector, wire if (row["w"] >> bit) & 1 else -wire)
                   for bit, wire in enumerate(wires["intermediate_reciprocal"]))
    clauses.extend((-selector, wire if (row["code"] >> bit) & 1 else -wire)
                   for bit, wire in enumerate(wires["codes"][4]))
assert len(clauses) == 1+284*(41+8)


def extension_valid(row):
    assignment = {wire: bool((row["w"] >> bit) & 1)
                  for bit, wire in enumerate(wires["intermediate_reciprocal"])}
    assignment.update({wire: bool((row["code"] >> bit) & 1)
                       for bit, wire in enumerate(wires["codes"][4])})
    # The selectors are ordered by w; locate the row by its actual position.
    selected = next(i for i, candidate in enumerate(table)
                    if candidate["w"] == row["w"])
    for selector in selectors:
        assignment[selector] = selector == selectors[selected]
    return all(any(assignment[abs(lit)] if lit > 0 else
                   not assignment[-lit] for lit in clause) for clause in clauses)


assert all(extension_valid(row) for row in table)
assert next(row for row in table if row["final_state_id"] ==
            fixture["state_ids"][4])["code"] == fixture["code_bit_words"][4]
controls_end = time.monotonic()

new_header = f"p cnf {selectors[-1]} {339484+len(clauses)}\n".encode()
serialized = b"".join((" ".join(map(str, clause))+" 0\n").encode()
                      for clause in clauses)
formula = new_header+base[len(old_header):]+serialized
(HERE / "formula.xcnf").write_bytes(formula)
(HERE / "w_code_table.json").write_text(json.dumps(table,sort_keys=True,
                                                 separators=(",",":"))+"\n")
finished = time.monotonic()
signal.alarm(0)
result = {"status": "PASS_EXACT_TARGET_W_CODE_SUPPORT_BUILD",
          "curve_id": p["curve_id"], "candidate_id": None,
          "table_entries": len(table), "distinct_w": len(table),
          "distinct_codes": len(allowed),
          "selector_variables": len(selectors),
          "support_clauses": len(clauses),
          "variables": selectors[-1],
          "constraints": 339484+len(clauses),
          "formula_bytes": len(formula),
          "formula_sha256": sha(HERE / "formula.xcnf"),
          "table_sha256": sha(HERE / "w_code_table.json"),
          "phase_seconds": {"source_and_table": table_end-started,
                            "support_and_controls": controls_end-table_end,
                            "serialization": finished-controls_end},
          "total_seconds": finished-started,
          "self_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "protocol_sha256": sha(HERE / "build_protocol.json")}
(HERE / "build_result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
print(json.dumps({k:result[k] for k in ("status","selector_variables",
                                        "support_clauses","formula_bytes",
                                        "total_seconds")},sort_keys=True))
