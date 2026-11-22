"""Exact target-conditioned (z,w) support and prefix-filter screen."""
import hashlib
import importlib.util
import json
import random
import resource
import signal
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
p = json.loads((HERE / "protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in p["sources"].items():
    assert sha(path) == expected, path
assert not (HERE / "result.json").exists()


def timeout(_signal, _frame):
    raise TimeoutError("frozen joint residual screen cap")


signal.signal(signal.SIGALRM, timeout)
signal.alarm(p["wall_cap_seconds"])
started = time.monotonic()
spec = importlib.util.spec_from_file_location("joint_residual_field", p["group_source"])
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
F = module.Field()
source = json.loads(Path(p["states"]).read_text())
fixture = json.loads(Path(p["fixture"]).read_text())
w_table = json.loads(Path(p["w_table"]).read_text())
assert len(source["states"]) == 5
assert all(len(slot) == 284 for slot in source["states"])
assert len(w_table) == 284
assert source["rotations"] == [0, 0, 12, 12, 24]
Q = tuple(fixture["public_point"])


def inverse_many(values):
    if not values:
        return []
    prefix = [1]
    for value in values:
        assert value
        prefix.append(F.mul(prefix[-1], value))
    inverse = F.inv(prefix[-1])
    out = [0] * len(values)
    for i in range(len(values)-1, -1, -1):
        out[i] = F.mul(inverse, prefix[i])
        inverse = F.mul(inverse, values[i])
    assert inverse == 1
    return out


def negate(point):
    x, y = point
    return x, x ^ y


residuals = []
for state in source["states"][4]:
    residual = module.add(F, Q, negate(tuple(state["point"])))
    assert residual is not None and residual[0]
    residuals.append(residual)
assert [F.inv(point[0]) for point in residuals] == [
    next(row["w"] for row in w_table if row["final_state_id"] == i)
    for i in range(284)]
source_end = time.monotonic()

# A batched affine group subtraction computes Q-E4-E3 for every
# column-disjoint signed pair. A reciprocal of its x coordinate is z.
normal = []
special = []
collisions = 0
for last_id, R in enumerate(residuals):
    last_cols = set(source["states"][4][last_id]["columns"])
    for prior_id, prior in enumerate(source["states"][3]):
        if last_cols.intersection(prior["columns"]):
            collisions += 1
            continue
        E = tuple(prior["point"])
        denom = R[0] ^ E[0]
        if denom:
            normal.append((last_id, prior_id, denom, R[1] ^ E[0] ^ E[1]))
        else:
            special.append((last_id, prior_id))

denom_inverses = inverse_many([row[2] for row in normal])
intermediate = []
for (last_id, prior_id, _, numerator), inverse in zip(normal, denom_inverses):
    R = residuals[last_id]
    E = source["states"][3][prior_id]["point"]
    slope = F.mul(numerator, inverse)
    x = F.square(slope) ^ slope ^ R[0] ^ E[0]
    intermediate.append((last_id, prior_id, x))
for last_id, prior_id in special:
    R = residuals[last_id]
    E = tuple(source["states"][3][prior_id]["point"])
    output = module.add(F, R, negate(E))
    intermediate.append((last_id, prior_id, None if output is None else output[0]))

zero_x = [(last_id, prior_id) for last_id, prior_id, x in intermediate if x == 0]
identity = [(last_id, prior_id) for last_id, prior_id, x in intermediate if x is None]
nonzero = [(last_id, prior_id, x) for last_id, prior_id, x in intermediate if x]
z_inverses = inverse_many([row[2] for row in nonzero])
w_by_id = {row["final_state_id"]: row["w"] for row in w_table}
records = [(w_by_id[last_id], z, prior_id, last_id)
           for (last_id, prior_id, _), z in zip(nonzero, z_inverses)]
records.sort()
assert len(records) + len(zero_x) + len(identity) + collisions == 284**2
assert all(module.add(F, residuals[last_id],
               negate(tuple(source["states"][3][prior_id]["point"]))) ==
           (F.inv(z), module.add(F, residuals[last_id],
               negate(tuple(source["states"][3][prior_id]["point"])))[1])
           for w,z,prior_id,last_id in records[::997])
support = {(w,z) for w,z,_,_ in records}
assert len(support) <= len(records)
witness_key = (w_by_id[fixture["state_ids"][4]], fixture["left_reciprocal"])
assert witness_key in support
assert any(prior_id == fixture["state_ids"][3] and
           last_id == fixture["state_ids"][4] and
           (w,z) == witness_key
           for w,z,prior_id,last_id in records)
support_end = time.monotonic()

# These prefixes are necessary conditions on the first-three-pair sum,
# conditional on a valid final-pair w. They preserve all exact records.
prefix_bits = p["prefix_bits"]
prefix_sets = {bits: {(w, z & ((1 << bits)-1)) for w,z in support}
               for bits in prefix_bits}
assert all(all((w,z & ((1 << bits)-1)) in prefix_sets[bits]
                   for w,z in support) for bits in prefix_bits)

rng = random.Random(p["control_seed"])
controls = []
attempts = 0
while len(controls) < p["reachable_control_count"]:
    attempts += 1
    if attempts > p["control_attempt_cap"]:
        raise RuntimeError("reachable control generation cap")
    ids = [rng.randrange(284) for _ in range(3)]
    last_id = rng.randrange(284)
    selected = [source["states"][slot][ids[slot]] for slot in range(3)]
    selected.append(source["states"][4][last_id])
    columns = [column for state in selected for column in state["columns"]]
    if len(set(columns)) != len(columns):
        continue
    point = None
    for state in selected[:3]:
        point = module.add(F, point, tuple(state["point"]))
    if point is None or point[0] == 0:
        continue
    z = F.inv(point[0])
    w = w_by_id[last_id]
    controls.append((w,z,*ids,last_id))

exact_hits = []
for index, (w,z,*_) in enumerate(controls):
    if (w,z) in support:
        exact_hits.append(index)
hit_counts = {str(bits): sum((w,z & ((1 << bits)-1)) in prefix_sets[bits]
                             for w,z,*_ in controls)
              for bits in prefix_bits}
assert all(hit_counts[str(bits)] >= len(exact_hits) for bits in prefix_bits)

# A prefix hit is a filter pass, not an equation witness. Check any exact
# hits by full group addition and all column identities.
verified_relations = []
for index in exact_hits:
    w,z,i0,i1,i2,last_id = controls[index]
    first = None
    for slot,state_id in enumerate((i0,i1,i2)):
        first = module.add(F, first, tuple(source["states"][slot][state_id]["point"]))
    for rw,rz,prior_id,rlast in records:
        if rw != w or rz != z or rlast != last_id:
            continue
        prior = source["states"][3][prior_id]
        last = source["states"][4][last_id]
        all_states = [source["states"][slot][sid]
                      for slot,sid in enumerate((i0,i1,i2,prior_id,last_id))]
        columns = [column for state in all_states for column in state["columns"]]
        if len(set(columns)) != len(columns):
            continue
        total = module.add(F, first, tuple(prior["point"]))
        total = module.add(F, total, tuple(last["point"]))
        if total == Q:
            verified_relations.append({"control_index":index,
                                       "state_ids":[i0,i1,i2,prior_id,last_id]})

(HERE / "support.json").write_text(json.dumps(records,separators=(",",":"))+"\n")
(HERE / "controls.json").write_text(json.dumps(controls,separators=(",",":"))+"\n")
finished = time.monotonic()
signal.alarm(0)
result = {
    "status":"PASS_N41_TARGET_JOINT_RESIDUAL_SCREEN",
    "candidate_id":None,"curve_id":p["curve_id"],
    "raw_pairs":284**2,"column_collision_pairs":collisions,
    "special_denominator_pairs":len(special),
    "identity_pairs":len(identity),"zero_x_pairs":len(zero_x),
    "usable_signed_pairs":len(records),"distinct_w_z_pairs":len(support),
    "distinct_w":len({w for w,_ in support}),
    "witness_w_z":list(witness_key),
    "prefix_support_counts":{str(bits):len(prefix_sets[bits]) for bits in prefix_bits},
    "uniform_conditional_prefix_fractions":{
        str(bits):len(prefix_sets[bits])/(284*(1 << bits)) for bits in prefix_bits},
    "reachable_controls":len(controls),"control_generation_attempts":attempts,
    "reachable_prefix_hits":hit_counts,"reachable_exact_hits":len(exact_hits),
    "verified_control_relations":verified_relations,
    "support_sha256":sha(HERE / "support.json"),
    "controls_sha256":sha(HERE / "controls.json"),
    "phase_seconds":{"source":source_end-started,
                     "joint_support":support_end-source_end,
                     "prefix_and_controls":finished-support_end},
    "total_seconds":finished-started,
    "self_maxrss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    "protocol_sha256":sha(HERE / "protocol.json")}
(HERE / "result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
print(json.dumps(result,sort_keys=True))
