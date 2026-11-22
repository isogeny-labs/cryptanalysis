"""Prepare noncyclic fiber coordinates and run a cyclic-subgroup target pair."""

import json
import math
import time
from hashlib import sha256
from pathlib import Path
from common import B, G, GROUP_ORDER, N, add, mul, valid

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "protocol.json").read_text())
for key in ("fiber_source", "hnf_source"):
    path = HERE / protocol[key]
    digest_key = "fiber_source_sha256" if key == "fiber_source" else "hnf_sha256"
    assert sha256(path.read_bytes()).hexdigest() == protocol[digest_key]
H = json.loads((HERE / protocol["hnf_source"]).read_text())
records = json.loads((HERE / protocol["fiber_source"]).read_text())["source_records"]["2"]
points = [tuple(r["point"]) for r in records]
assert len(points) == len(H) == 112 and points[3] == G and points[4] == B
assert all(valid(p) for p in points) and len(set(points)) == 112
Q = tuple(json.loads((HERE / "public.json").read_text())["point"])
assert valid(Q) and mul(N, Q) is None


def normal(vec):
    v = list(vec)
    for i, row in enumerate(H):
        q = v[i] // row[i]
        if q:
            for j in range(i, len(v)):
                v[j] -= q * row[j]
    return tuple(v)


def basis(a, b):
    v = [0] * 112
    v[3] = a
    v[4] = b
    return v


def unit(i):
    v = [0] * 112
    v[i] = 1
    return v


prep_start = time.perf_counter_ns()
coordinates = {}
for a in range(180):
    for b in range(60):
        coordinates.setdefault(normal(basis(a, b)), (a, b))
assert len(coordinates) == GROUP_ORDER
fiber_cosets = [normal(unit(i)) for i in range(112)]
fiber_coordinates = [coordinates[c] for c in fiber_cosets]
assert all(add(mul(a, G), mul(b, B)) == p for (a, b), p in zip(fiber_coordinates, points))
subgroup_cosets = {normal(basis(k, 0)): k for k in range(N)}
assert len(subgroup_cosets) == N
table = {p: subgroup_cosets[c] for p, c in zip(points, fiber_cosets) if c in subgroup_cosets}
assert all(mul(k, G) == p for p, k in table.items())
prep_ns = time.perf_counter_ns() - prep_start
(HERE / "prepared-coordinates.json").write_text(json.dumps(fiber_coordinates, separators=(",", ":")) + "\n")


def connector():
    start = time.perf_counter_ns()
    probe = Q
    for k in range(N):
        if probe in table:
            x = (table[probe] - k) % N
            assert mul(x, G) == Q
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
                            return {"status": "verified", "scalar": x, "walk_transitions": steps,
                                    "collisions": collisions, "restarts": restart,
                                    "online_ns": time.perf_counter_ns() - start}
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
out = {"schema": "x011-p941-one-target-result-v1", "public_point": Q,
       "fiber_size": len(points), "group_order": GROUP_ORDER,
       "full_quotient_cosets": len(coordinates), "prepared_coordinates_verified": len(fiber_coordinates),
       "target_subgroup_order": N, "target_subgroup_prepared_points": len(table),
       "prepared_coordinate_derivation_ns": prep_ns,
       "prepared_coordinates_sha256": sha256(json.dumps(fiber_coordinates, separators=(",", ":")).encode()).hexdigest(),
       "runs": runs, "candidate_id": None, "benchmark_tier": protocol["benchmark_tier"]}
(HERE / "result.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
