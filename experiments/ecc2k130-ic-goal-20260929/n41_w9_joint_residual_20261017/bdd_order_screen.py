"""Compare exact reduced-BDD sizes under three frozen bit orders."""
import bisect
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
p = json.loads((HERE / "order_protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in p["sources"].items():
    assert sha(path) == expected, path
assert not (HERE / "order_result.json").exists()


def timeout(_signum, _frame):
    raise TimeoutError("frozen BDD bit-order screen cap")


signal.signal(signal.SIGALRM, timeout)
signal.alarm(p["wall_cap_seconds"])
started = time.monotonic()
support = json.loads((HERE / "support.json").read_text())
assert len(support) == 79424
bits = p["prefix_bits"]
assert bits == 16


def order(name):
    if name == "w_first":
        return [("w",i) for i in range(41)]+[("z",i) for i in range(bits)]
    if name == "z_first":
        return [("z",i) for i in range(bits)]+[("w",i) for i in range(41)]
    if name == "interleaved":
        return [item for i in range(bits) for item in (("w",i),("z",i))]+\
               [("w",i) for i in range(bits,41)]
    raise ValueError(name)


def key_for(w,z,positions):
    out = 0
    for field,bit in positions:
        out = (out << 1) | (((w if field == "w" else z) >> bit) & 1)
    return out


class NodeCap(Exception):
    pass


def count_nodes(keys,width,cap):
    intern = {}

    def build(level,start,end):
        if start == end:
            return 0
        if level == width:
            assert end == start+1
            return 1
        shift = width-level-1
        prefix = keys[start] >> (shift+1)
        threshold = (prefix << (shift+1)) | (1 << shift)
        mid = bisect.bisect_left(keys,threshold,start,end)
        low = build(level+1,start,mid)
        high = build(level+1,mid,end)
        if low == high:
            return low
        identity = (level,low,high)
        if identity not in intern:
            if len(intern) >= cap:
                raise NodeCap
            intern[identity] = len(intern)+2
        return intern[identity]

    root = build(0,0,len(keys))
    assert root > 1
    return len(intern)


rows = []
for name in p["orders"]:
    began = time.monotonic()
    positions = order(name)
    assert len(set(positions)) == len(positions) == 57
    keys = sorted({key_for(w,z,positions) for w,z,_,_ in support})
    assert len(keys) == 79262
    try:
        count = count_nodes(keys,57,p["node_cap"])
        status = "PASS_EXACT_BDD_ORDER_COUNT"
    except NodeCap:
        count = None
        status = "BOUNDED_UNKNOWN_NODE_CAP"
    rows.append({"order":name,"status":status,"support_words":len(keys),
                 "bdd_nodes":count,"elapsed_seconds":time.monotonic()-began})
finished = time.monotonic()
signal.alarm(0)
result = {"status":"PASS_BDD_ORDER_SCREEN","candidate_id":None,
          "curve_id":p["curve_id"],"rows":rows,
          "total_seconds":finished-started,
          "self_maxrss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "protocol_sha256":sha(HERE / "order_protocol.json")}
(HERE / "order_result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
print(json.dumps({"status":result["status"],
                  "rows":[[row["order"],row["bdd_nodes"]] for row in rows],
                  "total_seconds":result["total_seconds"]},sort_keys=True))
