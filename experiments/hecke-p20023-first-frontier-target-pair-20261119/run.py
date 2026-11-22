"""Prepared-table target shifts and a same-public-point rho reference."""

import json
import math
import time
from hashlib import sha256
from pathlib import Path
from common import G, N, add, mul, valid

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "protocol.json").read_text())
pre_run = json.loads((HERE / "pre-run.json").read_text())
assert sha256((HERE / "protocol.json").read_bytes()).hexdigest() == pre_run["protocol_sha256"]
assert sha256((HERE / "public.json").read_bytes()).hexdigest() == pre_run["public_sha256"]
for key in ("fresh_source", "solved_table"):
    path = HERE / protocol[key]
    assert sha256(path.read_bytes()).hexdigest() == protocol[key + "_sha256"]
fresh = json.loads((HERE / protocol["fresh_source"]).read_text())
solved = json.loads((HERE / protocol["solved_table"]).read_text())
assert solved["fresh_source_sha256"] == protocol["fresh_source_sha256"]
reps = [tuple(x) for x in fresh["column_representatives"]]
logs = solved["logs_by_column"]
assert len(reps) == len(logs) == 1760
Q = tuple(json.loads((HERE / "public.json").read_text())["point"])
assert valid(Q) and mul(N, Q) is None

prep_start = time.perf_counter_ns()
table = {}
for rep, log in zip(reps, logs):
    point = None if rep == (-1, -1) else rep
    projected = mul(5, point)
    assert valid(projected) and mul(log, G) == projected
    assert projected not in table
    table[projected] = log
assert len(table) == 1760 and Q not in table
prep_ns = time.perf_counter_ns() - prep_start


def connector():
    start = time.perf_counter_ns()
    probe = Q
    for k in range(N):
        if probe in table:
            x = (table[probe] - k) % N
            assert mul(x, G) == Q
            return {"status": "verified", "scalar": x, "shift": k,
                    "probes": k + 1, "group_additions": k,
                    "online_ns": time.perf_counter_ns() - start}
        probe = add(probe, G)
    return {"status": "cap", "probes": N, "online_ns": time.perf_counter_ns() - start}


def rho(repetition):
    start = time.perf_counter_ns()
    steps = 0
    collisions = 0
    for restart in range(100):
        seed = sha256(f"rho:{Q}:{repetition}:{restart}".encode()).digest()
        a, b = int.from_bytes(seed[:8], "big") % N, int.from_bytes(seed[8:16], "big") % N
        state = (add(mul(a, G), mul(b, Q)), a, b)

        def advance(s):
            point, aa, bb = s
            partition = 0 if point is None else point[0] % 3
            if partition == 0:
                return add(point, G), (aa + 1) % N, bb
            if partition == 1:
                return add(point, Q), aa, (bb + 1) % N
            return add(point, point), (2 * aa) % N, (2 * bb) % N

        slow = advance(state)
        fast = advance(advance(state))
        steps += 3
        while steps < 200000:
            if slow[0] == fast[0]:
                collisions += 1
                delta_b = (slow[2] - fast[2]) % N
                delta_a = (fast[1] - slow[1]) % N
                divisor = math.gcd(delta_b, N)
                if delta_a % divisor == 0:
                    reduced = N // divisor
                    root = (delta_a // divisor * pow(delta_b // divisor, -1, reduced)) % reduced if reduced > 1 else 0
                    for j in range(divisor):
                        x = root + j * reduced
                        if mul(x, G) == Q:
                            return {"status": "verified", "scalar": x,
                                    "walk_transitions": steps, "collisions": collisions,
                                    "restarts": restart, "online_ns": time.perf_counter_ns() - start}
                break
            slow = advance(slow)
            fast = advance(advance(fast))
            steps += 3
        if steps >= 200000:
            break
    return {"status": "cap", "walk_transitions": steps, "collisions": collisions,
            "online_ns": time.perf_counter_ns() - start}


runs = []
for i, arm in enumerate(protocol["order"]):
    result = connector() if arm == "connector" else rho(i)
    result["arm"] = arm
    result["order_index"] = i
    runs.append(result)
out = {"schema": "hecke-p20023-first-frontier-target-pair-result-v1",
       "protocol_sha256": pre_run["protocol_sha256"],
       "public_sha256": pre_run["public_sha256"],
       "public_point": Q, "subgroup_order": N, "prepared_points": len(table),
       "prepared_table_check_ns": prep_ns, "runs": runs,
       "candidate_id": None, "benchmark_tier": protocol["benchmark_tier"]}
(HERE / "result.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
