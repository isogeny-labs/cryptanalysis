"""Complete N41 four-free-pair-state exact join under a single-worker cap."""
import hashlib
import importlib.util
import json
import resource
import signal
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "traversal_protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for name, source in CFG["sources"].items():
    assert sha(source["path"]) == source["sha256"], name
assert not (HERE / "traversal_result.json").exists()
spec = importlib.util.spec_from_file_location("independent_sage_curve", CFG["sources"]["sage_curve_audit"]["path"])
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
curve, elem, integer = old.sage_curve()
geo = json.loads(Path(CFG["sources"]["geometry"]["path"]).read_text())
target_table = json.loads(Path(CFG["sources"]["target_table"]["path"]).read_text())
witness = json.loads(Path(CFG["sources"]["witness_protocol"]["path"]).read_text())
cases = [json.loads(line) for line in Path(CFG["sources"]["coordinate_audit"]["path"]).open()]
assert len(cases) == 1554
started = time.monotonic()
signal.alarm(CFG["wall_cap_seconds"])
blocks = geo["blocks"]
suffix_cols = set().union(*(set(blocks[axis]["states"][state]["columns"])
                            for axis, state in enumerate(CFG["suffix_state_ids"], 4)))
states = [[curve(*(elem(v) for v in state["raw_sum"])) for state in blocks[axis]["states"]]
          for axis in range(4)]
code_cols = [[set(blocks[axis]["states"][4*code]["columns"]) for code in range(40)]
             for axis in range(4)]
compatible_fourth = {}
for code0, code1, code2 in ((a, b, c) for a in range(40) for b in range(40) for c in range(40)):
    cs = [code_cols[axis][code] for axis, code in enumerate((code0, code1, code2))]
    if any(col & suffix_cols for col in cs) or any(cs[i] & cs[j] for i in range(3) for j in range(i+1, 3)):
        continue
    used = set().union(*cs)
    fourth = [code for code in range(40) if not code_cols[3][code] & (suffix_cols | used)]
    if fourth:
        compatible_fourth[code0, code1, code2] = set(fourth)
assert sum(map(len, compatible_fourth.values())) == CFG["eligible_quads"]
setup_seconds = time.monotonic() - started

target_map = {}
for code, entries in enumerate(target_table["rows"]):
    for offset, entry in enumerate(entries):
        point = curve(*(elem(v) for v in entry["raw_point"]))
        target_map.setdefault(point, []).append((code, 4*code+offset))
assert sum(map(len, target_map.values())) == 160
query_seconds = time.monotonic() - started - setup_seconds

progress = {"code_pairs": 0, "eligible_triples": 0, "eligible_quads": 0,
            "first_two_state_sums": 0, "first_three_state_sums": 0,
            "matches": []}


def finish(status):
    out = {"status": status, "candidate_id": None, "curve_id": geo["curve_id"],
           **progress, "setup_seconds": setup_seconds,
           "query_seconds": query_seconds,
           "traversal_seconds": time.monotonic()-started-setup_seconds-query_seconds,
           "wall_seconds": time.monotonic()-started,
           "self_maxrss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
           "protocol_sha256": sha(HERE / "traversal_protocol.json")}
    (HERE / "traversal_result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": status, "eligible_quads": progress["eligible_quads"],
                      "first_three_state_sums": progress["first_three_state_sums"],
                      "matches": len(progress["matches"]), "wall_seconds": out["wall_seconds"]}, sort_keys=True))


def on_alarm(_signum, _frame):
    finish("TIMEOUT_N41_FULL_FOUR_AXIS_TRAVERSAL")
    raise SystemExit(124)


signal.signal(signal.SIGALRM, on_alarm)
for case in cases:
    code0, code1 = case["left_code"], case["right_code"]
    two_sums = [(i, j, states[0][i]+states[1][j])
                for i in range(4*code0, 4*code0+4)
                for j in range(4*code1, 4*code1+4)]
    progress["code_pairs"] += 1
    progress["first_two_state_sums"] += len(two_sums)
    for code2 in range(40):
        fourth = compatible_fourth.get((code0, code1, code2))
        if not fourth:
            continue
        progress["eligible_triples"] += 1
        progress["eligible_quads"] += len(fourth)
        for state2 in range(4*code2, 4*code2+4):
            point2 = states[2][state2]
            for state0, state1, partial in two_sums:
                total = partial + point2
                progress["first_three_state_sums"] += 1
                for code3, state3 in target_map.get(total, ()):
                    if code3 not in fourth:
                        continue
                    ids = [state0, state1, state2, state3] + CFG["suffix_state_ids"]
                    sum_point = total + states[3][state3]
                    for axis, state_id in enumerate(CFG["suffix_state_ids"], 4):
                        x, y = blocks[axis]["states"][state_id]["raw_sum"]
                        sum_point += curve(elem(x), elem(y))
                    assert [integer(sum_point[0]), integer(sum_point[1])] == witness["raw_target"]
                    progress["matches"].append({"state_ids": ids,
                                                 "code_quad": [code0, code1, code2, code3],
                                                 "raw_target": witness["raw_target"]})
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < CFG["rss_cap_bytes"]
assert progress["eligible_quads"] == CFG["eligible_quads"]
assert any(match["state_ids"] == [97, 151, 42, 0, 14, 109, 51]
           for match in progress["matches"])
finish("PASS_N41_FULL_FOUR_AXIS_TRAVERSAL")
signal.alarm(0)
