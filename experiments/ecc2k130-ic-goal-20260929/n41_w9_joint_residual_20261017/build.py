"""Attach the exact (w,z-low16) BDD to the frozen N41 tower XCNF."""
import bisect
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
p = json.loads((HERE / "build_protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in p["sources"].items():
    assert sha(path) == expected, path
assert not (HERE / "formula.xcnf").exists()


def timeout(_signum, _frame):
    raise TimeoutError("frozen joint-prefix BDD build cap")


signal.signal(signal.SIGALRM, timeout)
signal.alarm(p["wall_cap_seconds"])
started = time.monotonic()
bits = p["prefix_bits"]
assert bits == 16
support = json.loads((HERE / "support.json").read_text())
controls = json.loads((HERE / "controls.json").read_text())
screen = json.loads((HERE / "bdd_result.json").read_text())
source_result = json.loads((HERE / "result.json").read_text())
wires = json.loads(Path(p["wires"]).read_text())
fixture = json.loads(Path(p["fixture"]).read_text())
base_result = json.loads(Path(p["base_result"]).read_text())
base = Path(p["base_formula"]).read_bytes()
header = f"p cnf {base_result['variables']} "\
         f"{base_result['clauses']+base_result['native_xor_rows']}\n".encode()
assert base.startswith(header)
assert sha(p["base_formula"]) == base_result["formula_sha256"]
assert len(wires["intermediate_reciprocal"]) == 41
assert len(wires["left_reciprocal"]) == 41
assert len(support) == source_result["usable_signed_pairs"] == 79424
assert len(controls) == source_result["reachable_controls"] == 2048


def reverse(value, width):
    out = 0
    for _ in range(width):
        out = (out << 1) | (value & 1)
        value >>= 1
    return out


mask = (1 << bits)-1
keys = sorted({(reverse(w,41) << bits) | reverse(z & mask,bits)
               for w,z,_,_ in support})
expected_screen = next(row for row in screen["rows"]
                       if row["prefix_bits"] == bits)
assert len(keys) == expected_screen["support_words"] == 79262
source_end = time.monotonic()

intern = {}
nodes = []
base_variables = base_result["variables"]
width = 41+bits
selector_wires = wires["intermediate_reciprocal"] + wires["left_reciprocal"][:bits]


def node(level, start, end):
    if start == end:
        return False
    if level == width:
        assert end == start+1
        return True
    shift = width-level-1
    prefix = keys[start] >> (shift+1)
    threshold = (prefix << (shift+1)) | (1 << shift)
    mid = bisect.bisect_left(keys, threshold, start, end)
    low = node(level+1, start, mid)
    high = node(level+1, mid, end)
    if low == high:
        return low
    identity = (level, low, high)
    if identity not in intern:
        out = base_variables+len(nodes)+1
        intern[identity] = out
        nodes.append((out, selector_wires[level], low, high))
    return intern[identity]


root = node(0, 0, len(keys))
assert len(nodes) == expected_screen["bdd_nodes"] == 100081
assert isinstance(root,int) and not isinstance(root,bool)


def negate(value):
    return not value if isinstance(value,bool) else -value


clauses = []


def clause(literals):
    if any(value is True for value in literals):
        return
    row = tuple(value for value in literals if value is not False)
    assert row and all(isinstance(value,int) and not isinstance(value,bool)
                       for value in row)
    if any(-value in row for value in row):
        return
    clauses.append(row)


for output,selector,low,high in nodes:
    clause((-selector,-output,high))
    clause((-selector,output,negate(high)))
    clause((selector,-output,low))
    clause((selector,output,negate(low)))
clause((root,))
assert len(clauses) <= expected_screen["bdd_clause_upper_bound"]
construction_end = time.monotonic()

by_output = {out:(selector,low,high) for out,selector,low,high in nodes}
bit_for_wire = {wire:("w",i) for i,wire in enumerate(wires["intermediate_reciprocal"])}
bit_for_wire.update({wire:("z",i) for i,wire in enumerate(wires["left_reciprocal"][:bits])})


def accepts(w,z):
    current = root
    while not isinstance(current,bool):
        selector,low,high = by_output[current]
        source,index = bit_for_wire[selector]
        value = w if source == "w" else z
        current = high if (value >> index) & 1 else low
    return current


assert all(accepts(w,z) for w,z,_,_ in support)
assert accepts(*source_result["witness_w_z"])
assert source_result["witness_w_z"][1] == fixture["left_reciprocal"]
passes = sum(accepts(w,z) for w,z,*_ in controls)
assert passes == source_result["reachable_prefix_hits"][str(bits)] == 10
controls_end = time.monotonic()

new_header = f"p cnf {base_variables+len(nodes)} "\
             f"{base_result['clauses']+base_result['native_xor_rows']+len(clauses)}\n".encode()
serialized = b"".join((" ".join(map(str,row))+" 0\n").encode()
                      for row in clauses)
formula = new_header + base[len(header):] + serialized
(HERE / "formula.xcnf").write_bytes(formula)
finished = time.monotonic()
signal.alarm(0)
result = {"status":"PASS_N41_JOINT_PREFIX16_BDD_BUILD",
          "candidate_id":None,"curve_id":p["curve_id"],
          "base_variables":base_variables,"base_constraints":base_result["clauses"]+base_result["native_xor_rows"],
          "bdd_nodes":len(nodes),"bdd_clauses":len(clauses),
          "variables":base_variables+len(nodes),
          "constraints":base_result["clauses"]+base_result["native_xor_rows"]+len(clauses),
          "support_rows_accepted":len(support),
          "reachable_control_passes":passes,
          "formula_bytes":len(formula),"formula_sha256":sha(HERE / "formula.xcnf"),
          "phase_seconds":{"source":source_end-started,
                           "construction":construction_end-source_end,
                           "control_evaluation":controls_end-construction_end,
                           "serialization":finished-controls_end},
          "total_seconds":finished-started,
          "self_maxrss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "protocol_sha256":sha(HERE / "build_protocol.json")}
(HERE / "build_result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
print(json.dumps({k:result[k] for k in ("status","bdd_nodes","bdd_clauses",
                                         "formula_bytes","total_seconds")},sort_keys=True))
