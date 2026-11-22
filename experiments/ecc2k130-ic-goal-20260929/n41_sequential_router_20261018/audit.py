"""Independent low-pivot replay and exact staged-router cost accounting."""
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
protocol = json.loads((HERE / "protocol.json").read_text())
result = json.loads((HERE / "result.json").read_text())
old_protocol = json.loads((HERE / "protocol_v1.json").read_text())
old_result = json.loads((HERE / "result_v1.json").read_text())
assert result["status"] == old_result["status"] == "COMPLETE_SEQUENTIAL_ROUTER_SYNTHESIS"
for archived, extended in zip(old_result["stages"], result["stages"][:4]):
    assert all(extended[key] == value for key, value in archived.items())
assert old_result["protocol_sha256"] == hashlib.sha256(
    (HERE / "protocol_v1.json").read_bytes()).hexdigest()
assert result["protocol_sha256"] == hashlib.sha256(
    (HERE / "protocol.json").read_bytes()).hexdigest()

for relative, expected in protocol["sources_sha256"].items():
    assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected

source = ROOT / "n41_w8_two_code_affine_span_20261013" / "cases.jsonl"
geometry_file = ROOT / "n41_w8_fixed_sum_table_20261009" / "geometry.json"
cases = [json.loads(line) for line in source.read_text().splitlines()]
geometry = json.loads(geometry_file.read_text())
codes = [[block["states"][4*c]["a"] for c in range(40)]
         for block in geometry["blocks"][:2]]
monomials = [sum(1 << bit for bit in group)
             for degree in range(6)
             for group in itertools.combinations(range(16), degree)]
prefix = [sum(__import__("math").comb(16, k) for k in range(d+1))
          for d in range(6)]
selected = [list(itertools.combinations(range(41),2))[bit-42]
            for bit in protocol["selected_features"]]
assert len(selected) == 37
rows = []
for index, case in enumerate(cases):
    if (case["x_coordinates"][0] & 1) != (protocol["target"] & 1):
        continue
    code = codes[0][case["left_code"]] | codes[1][case["right_code"]] << 8
    features = sum(1 << pos for pos, mon in enumerate(monomials)
                   if code & mon == mon)
    label = 0
    for bit, (i,j) in enumerate(selected):
        if all(not (x >> i & 1 and x >> j & 1) for x in case["x_coordinates"]):
            label |= 1 << bit
    rows.append((index, features, label))
assert len(rows) == 766


def low_rank(active, count):
    pivots = {}
    mask = (1 << count)-1
    for _, feature, _ in active:
        value = feature & mask
        while value:
            bit = (value & -value).bit_length()-1
            if bit not in pivots:
                pivots[bit] = value
                break
            value ^= pivots[bit]
    return len(pivots)


active = rows
remaining = list(range(37))
checkpoints = []
for stage in result["stages"]:
    assert stage["surviving_source_indices"] == [i for i,_,_ in active]
    assert stage["survivor_count"] == len(active)
    assert stage["remaining_gate_count"] == len(remaining)
    for direction in ("high", "low"):
        predicates = stage["variants"][direction]["predicates"]
        assert [p["gate_index"] for p in predicates] == remaining
        for p in predicates:
            positions = p["coefficient_positions"]
            assert len(positions) == p["monomial_count"]
            mask = sum(1 << pos for pos in positions)
            assert all(((feature & mask).bit_count() & 1) == (label >> p["gate_index"] & 1)
                       for _, feature, label in active)
    if stage["stage"] in (0,1,5,16,28,37):
        got = low_rank(active, prefix[stage["first_full_rank_degree"]])
        assert got == len(active)
        checkpoints.append({"stage": stage["stage"], "survivors": len(active),
                            "degree": stage["first_full_rank_degree"], "low_pivot_rank": got})
    if stage["stage"] == 37:
        break
    best = max((sum(label >> bit & 1 for _,_,label in active), -bit, bit)
               for bit in remaining)
    assert best[2] == stage["selected_gate_index"]
    assert best[0] == stage["rejected_family_count"]
    active = [row for row in active if not (row[2] >> best[2] & 1)]
    remaining.remove(best[2])
assert len(active) == 1 and active[0][0] == 966 and not remaining

costs = {}
for direction in ("high", "low"):
    static = {p["gate_index"]: p for p in result["stages"][0]["variants"][direction]["predicates"]}
    static_weighted = 0
    staged_weighted = 0
    staged_terms = 0
    staged_separated_rank = 0
    for stage in result["stages"][:-1]:
        bit = stage["selected_gate_index"]
        current = next(p for p in stage["variants"][direction]["predicates"]
                       if p["gate_index"] == bit)
        static_weighted += stage["survivor_count"] * static[bit]["monomial_count"]
        staged_weighted += stage["survivor_count"] * current["monomial_count"]
        staged_terms += current["monomial_count"]
        staged_separated_rank += current["separated_matrix_rank"]
    costs[direction] = {"same_order_static_term_evaluations": static_weighted,
                        "staged_term_evaluations": staged_weighted,
                        "staged_formula_monomial_occurrences": staged_terms,
                        "staged_separated_rank_sum": staged_separated_rank}

out = {"status": "INDEPENDENT_SEQUENTIAL_ROUTER_AUDIT_PASS",
       "result_sha256": hashlib.sha256((HERE / "result.json").read_bytes()).hexdigest(),
       "v1_result_sha256": hashlib.sha256((HERE / "result_v1.json").read_bytes()).hexdigest(),
       "checkpoints": checkpoints, "final_source_index": 966, "costs": costs}
(HERE / "audit_result.json").write_text(json.dumps(out, sort_keys=True, indent=2)+"\n")
print(json.dumps({"status": out["status"], "checkpoints": checkpoints,
                  "costs": costs}, sort_keys=True))
