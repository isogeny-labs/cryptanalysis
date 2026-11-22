"""Recover last-pair codes from a target-conditioned intermediate coordinate."""
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
assert not (HERE / "result.json").exists()
assert protocol["curve_id"] == "EC1N41Ckb1h7d5e80d3c4d0"
assert protocol["worker_count"] == 1
assert protocol["uniform_count"] == 1024
assert protocol["reachable_count"] == 256


def timeout(_signum, _frame):
    raise TimeoutError("frozen image-filter wall cap")


signal.signal(signal.SIGALRM, timeout)
signal.alarm(protocol["wall_cap_seconds"])
start = time.monotonic()
spec = importlib.util.spec_from_file_location("n41_field", protocol["field_source"])
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
F = module.Field()
source = json.loads(Path(protocol["states"]).read_text())
fixture = json.loads(Path(protocol["fixture"]).read_text())
witness = json.loads(Path(protocol["witness"]).read_text())
wire_record = json.loads(Path(protocol["wires"]).read_text())
assert source["rotations"] == [0, 0, 12, 12, 24]
assert fixture["public_reciprocal"] == wire_record["public_reciprocal"]
assert len(wire_record["allowed_code_words"]) == 71
allowed = set(wire_record["allowed_code_words"])
bits = [i for i in range(9) if i != 5]
seed = source["seed"] << 1


def frob(value, count):
    for _ in range(count):
        value = F.square(value)
    return value


def xor(values):
    result = 0
    for value in values:
        result ^= value
    return result


base_products = [F.mul((1 << bit) << 1, ((1 << bit) << 1) ^ seed)
                 for bit in bits]
products = [frob(value, source["rotations"][4]) for value in base_products]
product_to_code = {}
for code in range(256):
    product = xor(products[j] for j in range(8) if code >> j & 1)
    product_to_code.setdefault(product, []).append(code)
assert len(product_to_code) == 256
assert all(len(codes) == 1 for codes in product_to_code.values())
assert all(code in allowed for code in fixture["code_bit_words"])

H = frob(F.square(F.halftrace(seed)), source["rotations"][4])
C = H ^ 1
t = fixture["public_reciprocal"]
assert H and C and t not in (0, 1)
assert witness["intermediate_reciprocal"] != 0
setup_end = time.monotonic()


def coefficients(w):
    B = F.mul(t, w)
    A = 1 ^ F.square(B)
    D = F.square(t) ^ F.square(w)
    M = F.mul(A, H) ^ F.mul(C, D)
    a = F.mul(A, D)
    b = F.mul(B, M)
    q = F.square(M) ^ F.mul(F.mul(C, H), F.square(B))
    return a, b, q


def field_trace(value):
    acc = 0
    for _ in range(41):
        acc ^= value
        value = F.square(value)
    assert acc in (0, 1)
    return acc


def solve(w):
    a, b, q = coefficients(w)
    if not a and not b:
        possible = list(product_to_code) if q == 0 else []
        rank = 0
        chart = "ZERO_MAP"
    elif not a:
        possible = [F.mul(q, F.inv(b))]
        rank = 8
        chart = "LINEAR"
    elif not b:
        possible = [frob(F.mul(q, F.inv(a)), 40)]
        rank = 8
        chart = "SQUARE"
    else:
        rhs = F.mul(F.mul(q, a), F.inv(F.square(b)))
        if field_trace(rhs):
            possible = []
        else:
            h = F.halftrace(rhs)
            step = F.mul(b, F.inv(a))
            p0 = F.mul(step, h)
            possible = [p0, p0 ^ step]
        step = F.mul(b, F.inv(a))
        rank = 7 if step in product_to_code else 8
        chart = "ARTIN_SCHREIER"
    codes = sorted(code for value in possible
                   for code in product_to_code.get(value, []))
    return {"w": w, "chart": chart, "map_rank": rank,
            "field_root_count": len(possible), "linear_image_codes": codes,
            "allowed_codes": [code for code in codes if code in allowed]}


def direct_codes(w, permitted):
    a, b, q = coefficients(w)
    out = []
    for code in permitted:
        p = xor(products[j] for j in range(8) if code >> j & 1)
        if F.mul(a, F.square(p)) ^ F.mul(b, p) ^ q == 0:
            out.append(code)
    return sorted(out)


def code_of_state(state):
    mask = state["masks"][0]
    return sum(((mask >> bit) & 1) << j for j, bit in enumerate(bits))


def group_witness(first_ids, code):
    columns = [column for slot, state_id in enumerate(first_ids)
               for column in source["states"][slot][state_id]["columns"]]
    if len(set(columns)) != 8:
        return []
    subtotal = None
    for slot, state_id in enumerate(first_ids):
        subtotal = module.add(F, subtotal,
                              tuple(source["states"][slot][state_id]["point"]))
    hits = []
    for final_id, state in enumerate(source["states"][4]):
        if code_of_state(state) != code:
            continue
        if set(columns) & set(state["columns"]):
            continue
        if module.add(F, subtotal, tuple(state["point"])) == tuple(fixture["public_point"]):
            hits.append(final_id)
    return hits


positive = solve(witness["intermediate_reciprocal"])
assert fixture["code_bit_words"][4] in positive["allowed_codes"]
assert direct_codes(positive["w"], range(256)) == positive["linear_image_codes"]
assert fixture["state_ids"][4] in group_witness(fixture["state_ids"][:4],
                                                   fixture["code_bit_words"][4])
positive_end = time.monotonic()

uniform = []
seen = {positive["w"]}
counter = 0
while len(uniform) < protocol["uniform_count"]:
    raw = hashlib.sha256(
        f"{protocol['uniform_seed']}:{counter}".encode()).digest()
    counter += 1
    w = int.from_bytes(raw, "big") & ((1 << 41) - 1)
    if w in seen:
        continue
    seen.add(w)
    row = solve(w)
    if len(uniform) < 64:
        assert direct_codes(w, range(256)) == row["linear_image_codes"]
    uniform.append(row)
uniform_end = time.monotonic()

reachable = []
seen_reachable = {positive["w"]}
draws = 0
while len(reachable) < protocol["reachable_count"]:
    raw = hashlib.sha256(
        f"{protocol['reachable_seed']}:{draws}".encode()).digest()
    draws += 1
    assert draws <= protocol["reachable_draw_cap"]
    ids = [int.from_bytes(raw[2*slot:2*slot+2], "big") %
           len(source["states"][slot]) for slot in range(4)]
    states = [source["states"][slot][state_id]
              for slot, state_id in enumerate(ids)]
    cols = [column for state in states for column in state["columns"]]
    if len(set(cols)) != 8:
        continue
    subtotal = None
    for state in states:
        subtotal = module.add(F, subtotal, tuple(state["point"]))
    if subtotal is None or subtotal[0] == 0:
        continue
    w = F.inv(subtotal[0])
    if w in seen_reachable:
        continue
    seen_reachable.add(w)
    row = solve(w)
    row["first_four_state_ids"] = ids
    if len(reachable) < 64:
        assert direct_codes(w, range(256)) == row["linear_image_codes"]
    for code in row["allowed_codes"]:
        row.setdefault("exact_group_hits", {})[str(code)] = group_witness(ids, code)
    reachable.append(row)
reachable_end = time.monotonic()

special_values = sorted({0, t, F.inv(t), positive["w"]})
special = [solve(w) for w in special_values]
for row in special:
    assert direct_codes(row["w"], range(256)) == row["linear_image_codes"]
finished = time.monotonic()
signal.alarm(0)


def summary(rows):
    return {"count": len(rows),
            "chart_counts": {chart: sum(row["chart"] == chart for row in rows)
                             for chart in sorted({row["chart"] for row in rows})},
            "rank_counts": {str(rank): sum(row["map_rank"] == rank for row in rows)
                            for rank in sorted({row["map_rank"] for row in rows})},
            "linear_image_hits": sum(bool(row["linear_image_codes"]) for row in rows),
            "allowed_code_hits": sum(bool(row["allowed_codes"]) for row in rows)}


result = {"status": "PASS_EXACT_FINALPAIR_CODE_RECOVERY_PANEL",
          "candidate_id": None, "curve_id": protocol["curve_id"],
          "protocol_sha256": sha(HERE / "protocol.json"),
          "positive": positive, "uniform": uniform, "reachable": reachable,
          "special": special,
          "uniform_summary": summary(uniform),
          "reachable_summary": summary(reachable),
          "reachable_draws": draws,
          "phase_seconds": {"source_preparation": setup_end-start,
                            "positive_group_control": positive_end-setup_end,
                            "uniform_decode": uniform_end-positive_end,
                            "reachable_generation_and_decode": reachable_end-uniform_end,
                            "special_checks_and_summary": finished-reachable_end},
          "total_wall_seconds": finished-start,
          "self_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(HERE / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2)+"\n")
print(json.dumps({"status": result["status"],
                  "uniform_summary": result["uniform_summary"],
                  "reachable_summary": result["reachable_summary"],
                  "total_wall_seconds": result["total_wall_seconds"]}, sort_keys=True))
