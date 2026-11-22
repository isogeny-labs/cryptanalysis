"""Count canonical BDD nodes for joint (w,z-prefix) support."""
import bisect
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
p = json.loads((HERE / "bdd_protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in p["sources"].items():
    assert sha(path) == expected, path
assert not (HERE / "bdd_result.json").exists()


def timeout(_signum, _frame):
    raise TimeoutError("frozen joint BDD screen cap")


signal.signal(signal.SIGALRM, timeout)
signal.alarm(p["wall_cap_seconds"])
started = time.monotonic()
records = json.loads((HERE / "support.json").read_text())
source = json.loads((HERE / "result.json").read_text())
assert len(records) == source["usable_signed_pairs"] == 79424
assert source["status"] == "PASS_N41_TARGET_JOINT_RESIDUAL_SCREEN"


def reverse(value, bits):
    out = 0
    for _ in range(bits):
        out = (out << 1) | (value & 1)
        value >>= 1
    return out


class NodeCap(Exception):
    pass


def count_nodes(keys, width, cap):
    intern = {}
    level_counts = [0] * width

    def build(level, start, end):
        if start == end:
            return 0
        if level == width:
            assert end == start + 1
            return 1
        shift = width - level - 1
        prefix = keys[start] >> (shift + 1)
        threshold = (prefix << (shift + 1)) | (1 << shift)
        mid = bisect.bisect_left(keys, threshold, start, end)
        low = build(level+1, start, mid)
        high = build(level+1, mid, end)
        if low == high:
            return low
        identity = (level, low, high)
        if identity not in intern:
            if len(intern) >= cap:
                raise NodeCap
            intern[identity] = len(intern) + 2
            level_counts[level] += 1
        return intern[identity]

    root = build(0, 0, len(keys))
    assert root > 1
    return len(intern), level_counts


rows = []
for bits in p["prefix_bits"]:
    one_start = time.monotonic()
    mask = (1 << bits)-1
    keys = sorted({(reverse(w, 41) << bits) | reverse(z & mask, bits)
                   for w,z,_,_ in records})
    assert len(keys) == source["prefix_support_counts"][str(bits)]
    try:
        count, levels = count_nodes(keys, 41+bits, p["node_cap"])
        status = "PASS_EXACT_BDD_NODE_COUNT"
    except NodeCap:
        count, levels = None, None
        status = "BOUNDED_UNKNOWN_NODE_CAP"
    rows.append({"prefix_bits":bits,"status":status,
                 "support_words":len(keys),"bdd_nodes":count,
                 "bdd_clause_upper_bound":None if count is None else 4*count+1,
                 "level_nodes":levels,
                 "elapsed_seconds":time.monotonic()-one_start})

finished = time.monotonic()
signal.alarm(0)
result = {"status":"PASS_JOINT_PREFIX_BDD_SCREEN",
          "candidate_id":None,"curve_id":p["curve_id"],
          "rows":rows,"total_seconds":finished-started,
          "self_maxrss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "protocol_sha256":sha(HERE / "bdd_protocol.json")}
(HERE / "bdd_result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
print(json.dumps({"status":result["status"],
                  "counts":[[row["prefix_bits"],row["bdd_nodes"]] for row in rows],
                  "total_seconds":result["total_seconds"]},sort_keys=True))
