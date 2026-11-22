"""Derive prepared fiber logs from row HNF and compare one-point solvers."""

import json
import math
import time
from hashlib import sha256
from pathlib import Path
from common import G, N, add, mul, neg, valid

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "protocol.json").read_text())
public = json.loads((HERE / "public.json").read_text())
Q = tuple(public["point"])
assert valid(Q) and mul(N, Q) is None
hnf_path = HERE / protocol["hnf_source"]
assert sha256(hnf_path.read_bytes()).hexdigest() == protocol["hnf_sha256"]
H = json.loads(hnf_path.read_text())
points = [tuple(r["point"]) for r in json.loads((HERE / protocol["fiber_source"]).read_text())["source_records"]]
assert len(H) == len(points) == 84 and points[0] == G and len(set(points)) == 84


def normal(vec):
    vec = list(vec)
    for i, row in enumerate(H):
        d = row[i]
        q = vec[i] // d
        if q:
            for j in range(i, len(vec)):
                vec[j] -= q * row[j]
    return tuple(vec)


def unit(i, scale=1):
    v = [0] * len(points)
    v[i] = scale
    return v


prep_start = time.perf_counter_ns()
cosets = {normal(unit(0, k)): k for k in range(N)}
assert len(cosets) == N
logs = [cosets[normal(unit(i))] for i in range(len(points))]
assert all(mul(k) == point for k, point in zip(logs, points))
(HERE / "prepared-logs.json").write_text(json.dumps(logs, separators=(",", ":")) + "\n")
table = dict(zip(points, logs))
prep_ns = time.perf_counter_ns() - prep_start


def connector():
    start = time.perf_counter_ns()
    probe = Q
    for k in range(N):
        if probe in table:
            x = (table[probe] - k) % N
            assert mul(x) == Q
            return {"status": "verified", "scalar": x, "shift": k, "probes": k + 1,
                    "group_additions": k, "online_ns": time.perf_counter_ns() - start}
        probe = add(probe, G)
    return {"status": "cap", "probes": N, "online_ns": time.perf_counter_ns() - start}


def rho(repetition):
    start = time.perf_counter_ns()
    steps = 0
    collisions = 0
    for restart in range(100):
        seed = sha256(f"rho:{Q}:{repetition}:{restart}".encode()).digest()
        a, b = int.from_bytes(seed[:8], "big") % N, int.from_bytes(seed[8:16], "big") % N
        state = (add(mul(a), mul(b, Q)), a, b)

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
                        if mul(x) == Q:
                            return {"status": "verified", "scalar": x, "group_steps": steps,
                                    "collisions": collisions, "restarts": restart,
                                    "online_ns": time.perf_counter_ns() - start}
                break
            slow = advance(slow)
            fast = advance(advance(fast))
            steps += 3
        if steps >= 200000:
            break
    return {"status": "cap", "group_steps": steps, "collisions": collisions,
            "online_ns": time.perf_counter_ns() - start}


results = []
for i, arm in enumerate(protocol["order"]):
    result = connector() if arm == "connector" else rho(i)
    result["arm"] = arm
    result["order_index"] = i
    results.append(result)
out = {"schema": "x011-p1009-one-target-result-v1", "public_point": Q,
       "fiber_size": len(table), "group_order": N, "prepared_log_derivation_ns": prep_ns,
       "prepared_log_sha256": sha256(json.dumps(logs, separators=(",", ":")).encode()).hexdigest(),
       "prepared_log_first12": logs[:12], "runs": results,
       "candidate_id": None, "benchmark_tier": protocol["benchmark_tier"]}
(HERE / "result.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
