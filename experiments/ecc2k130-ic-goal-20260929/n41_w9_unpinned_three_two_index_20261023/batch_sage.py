"""Frozen 256-key target-derived cost panel for the coordinate oracle."""
import hashlib
import json
import resource
import statistics
import sys
import time
from pathlib import Path

from oracle_sage import HERE, INPUT, dec, enc, load, s3_roots, point


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze():
    target, states, cols = load()
    oriented = point([enc(target[0]**8), enc(target[1]**8)])
    suffixes = [[233, 283, 152]]
    seen = {tuple(suffixes[0])}
    seed = 0x0BADC41
    while len(suffixes) < 256:
        seed = (1664525*seed + 1013904223) & 0xffffffff
        ids = tuple((seed >> shift) % 284 for shift in (0, 9, 18))
        if ids in seen or len(set().union(*(cols[i+2][ids[i]] for i in range(3)))) != 6:
            continue
        seen.add(ids)
        suffixes.append(list(ids))
    keys = []
    for ids in suffixes:
        key = oriented - sum((states[i+2][ids[i]] for i in range(3)), states[0][0]*0)
        assert key != states[0][0]*0 and key[0]
        keys.append({"suffix_ids": ids, "key": [enc(key[0]), enc(key[1])]})
    protocol = {"status": "FROZEN", "candidate_id": None,
                "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
                "target_raw_point": [enc(target[0]), enc(target[1])],
                "orientation": 3, "key_count": len(keys), "keys": keys,
                "input_sha256": sha(INPUT),
                "oracle_script_sha256": sha(HERE/"oracle_sage.py"),
                "batch_script_sha256": sha(Path(__file__)),
                "runtime_info_sha256": sha(HERE/"sage_runtime_info.json"),
                "worker_count": 1, "wall_cap_seconds": 120,
                "rss_cap_bytes": 4*1024**3}
    with (HERE/"batch_protocol.json").open("x") as out:
        json.dump(protocol, out, sort_keys=True, indent=2)
        out.write("\n")
    print(json.dumps({"status": "FROZEN", "key_count": len(keys)}))


def run():
    protocol = json.loads((HERE/"batch_protocol.json").read_text())
    assert sha(INPUT) == protocol["input_sha256"]
    assert sha(HERE/"oracle_sage.py") == protocol["oracle_script_sha256"]
    assert sha(Path(__file__)) == protocol["batch_script_sha256"]
    assert sha(HERE/"sage_runtime_info.json") == protocol["runtime_info_sha256"]
    assert not (HERE/"batch_result.json").exists()
    _, states, cols = load()
    prep = time.monotonic()
    left = {}
    right = {}
    for sid in range(284):
        left.setdefault(enc(1/states[0][sid][0]), []).append(sid)
        right.setdefault(enc(1/states[1][sid][0]), []).append(sid)
    prep_seconds = time.monotonic()-prep
    assert len(left) == len(right) == 142
    rows = []
    start = time.monotonic()
    for item in protocol["keys"]:
        key = point(item["key"])
        t = 1/key[0]
        tick = time.monotonic_ns()
        hits = set()
        coord_hits = 0
        exceptional = 0
        for aword, a_ids in left.items():
            bs = s3_roots(dec(aword), t)
            if bs is None:
                exceptional += 1
                continue
            for b in bs:
                for bid in right.get(enc(b), []):
                    coord_hits += 1
                    for aid in a_ids:
                        if cols[0][aid].isdisjoint(cols[1][bid]) and states[0][aid]+states[1][bid] == key:
                            hits.add((aid,bid))
        rows.append({"suffix_ids": item["suffix_ids"],
                     "matches": [list(v) for v in sorted(hits)],
                     "coordinate_hits": coord_hits, "exceptional": exceptional,
                     "query_ns": time.monotonic_ns()-tick})
    elapsed = time.monotonic()-start
    times = sorted(row["query_ns"] for row in rows)
    result = {"status": "PASS_BATCH_ORACLE", "candidate_id": None,
              "protocol_sha256": sha(HERE/"batch_protocol.json"),
              "setup_seconds": prep_seconds, "query_seconds": elapsed,
              "query_ns_min_median_p90_max": [times[0], times[len(times)//2],
                                              times[(9*len(times))//10], times[-1]],
              "root_calls": 142*len(rows),
              "coordinate_hit_count": sum(row["coordinate_hits"] for row in rows),
              "exceptional_chart_count": sum(row["exceptional"] for row in rows),
              "self_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "rows": rows}
    with (HERE/"batch_result.json").open("x") as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write("\n")
    print(json.dumps({k:result[k] for k in ("status", "query_seconds", "query_ns_min_median_p90_max", "coordinate_hit_count", "exceptional_chart_count")}))


if __name__ == "__main__":
    {"freeze": freeze, "run": run}[sys.argv[1]]()
