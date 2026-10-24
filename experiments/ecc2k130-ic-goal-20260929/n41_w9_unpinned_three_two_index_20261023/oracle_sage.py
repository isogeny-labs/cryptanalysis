"""Exact S3 coordinate oracle for the N41 W9 two-pair source."""
import hashlib
import json
import resource
import sys
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
INPUT = ROOT / "n41_n131_fivepair_w9_w29_20261017/join_input.tsv"
R = PolynomialRing(GF(2), "u")
u = R.gen()
F = GF(2**41, name="u", modulus=u**41 + u**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dec(word):
    return F(R([(int(word) >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(c) << i for i, c in enumerate(value.polynomial().list()))


def point(row):
    return E(dec(row[0]), dec(row[1]))


def load():
    lines = INPUT.read_text().splitlines()
    header = lines[0].split()
    assert header[:3] == ["ECC2K41", "5", "284"]
    states = [[None] * 284 for _ in range(5)]
    columns = [[None] * 284 for _ in range(5)]
    for line in lines[1:]:
        fields = line.split()
        assert fields[0] == "S"
        slot, sid = map(int, fields[1:3])
        states[slot][sid] = point(fields[9:11])
        columns[slot][sid] = frozenset(map(int, fields[7:9]))
    assert all(all(s is not None for s in slot) for slot in states)
    return point(header[3:5]), states, columns


def halftrace(value):
    out = F.zero()
    for _ in range(21):
        out += value
        value = value**4
    return out


def s3_roots(a, t):
    """All nonzero reciprocal x of the third point in S3(a,b,t)=0."""
    if not a or not t:
        return None
    A = 1 + (a*t)**2
    B = a*t
    D = a**2 + t**2
    if not A:
        return [D/B] if B else None
    rhs = A*D/B**2
    if rhs.trace():
        return []
    h = halftrace(rhs)
    scale = B/A
    roots = [scale*h, scale*(h+1)]
    assert all(A*b*b + B*b + D == 0 for b in roots)
    return roots


def frozen():
    target, states, columns = load()
    for slot in range(5):
        for sid in range(284):
            assert len(columns[slot][sid]) == 2
            assert states[slot][sid] in E
    oriented = E(target[0]**8, target[1]**8)
    positives = [0, 130, 233, 283, 152]
    assert sum((states[i][s] for i, s in enumerate(positives)), E(0)) == oriented
    suffixes = [positives[2:]]
    seed = 0xC0DEC41
    while len(suffixes) < 17:
        seed = (1664525*seed + 1013904223) & 0xffffffff
        ids = [(seed >> shift) % 284 for shift in (0, 9, 18)]
        if len(set().union(*(columns[i+2][ids[i]] for i in range(3)))) != 6:
            continue
        if ids not in suffixes:
            suffixes.append(ids)
    keys = []
    for ids in suffixes:
        key = oriented - sum((states[i+2][ids[i]] for i in range(3)), E(0))
        assert key != E(0) and key[0]
        keys.append({"suffix_ids": ids, "key": [enc(key[0]), enc(key[1])]})
    receipt = {"status": "FROZEN", "candidate_id": None,
               "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
               "target_raw_point": [enc(target[0]), enc(target[1])],
               "orientation": 3, "known_positive_state_ids": positives,
               "query_count": len(keys), "keys": keys,
               "input_sha256": sha(INPUT), "script_sha256": sha(Path(__file__)),
               "runtime_info_sha256": sha(HERE / "sage_runtime_info.json"),
               "worker_count": 1, "wall_cap_seconds": 300,
               "rss_cap_bytes": 4*1024**3}
    with (HERE / "protocol.json").open("x") as out:
        json.dump(receipt, out, sort_keys=True, indent=2)
        out.write("\n")
    print(json.dumps({"status": "FROZEN", "query_count": len(keys)}))


def run():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert sha(INPUT) == protocol["input_sha256"]
    assert sha(Path(__file__)) == protocol["script_sha256"]
    assert sha(HERE / "sage_runtime_info.json") == protocol["runtime_info_sha256"]
    assert not (HERE / "result.json").exists()
    _, states, cols = load()
    begin = time.monotonic()
    right = {}
    for sid, P in enumerate(states[1]):
        assert P[0]
        right.setdefault(enc(1/P[0]), []).append(sid)
    left = {}
    for sid, P in enumerate(states[0]):
        assert P[0]
        left.setdefault(enc(1/P[0]), []).append(sid)
    setup_s = time.monotonic() - begin
    assert len(right) == len(left) == 142
    results = []
    total_root_calls = 0
    total_coordinate_hits = 0
    query_begin = time.monotonic()
    for item in protocol["keys"]:
        key = point(item["key"])
        t = 1/key[0]
        matches = set()
        exceptional = 0
        coordinate_hits = 0
        calls = 0
        for aword, a_ids in left.items():
            bs = s3_roots(dec(aword), t)
            calls += 1
            if bs is None:
                exceptional += 1
                continue
            for b in bs:
                for b_id in right.get(enc(b), []):
                    coordinate_hits += 1
                    for a_id in a_ids:
                        if cols[0][a_id].isdisjoint(cols[1][b_id]) and states[0][a_id] + states[1][b_id] == key:
                            matches.add((a_id, b_id))
        total_root_calls += calls
        total_coordinate_hits += coordinate_hits
        results.append({"suffix_ids": item["suffix_ids"],
                        "matches": [list(v) for v in sorted(matches)],
                        "root_calls": calls, "coordinate_hits": coordinate_hits,
                        "exceptional": exceptional})
    query_s = time.monotonic() - query_begin
    result = {"status": "PASS_ORACLE_QUERIES", "candidate_id": None,
              "protocol_sha256": sha(HERE / "protocol.json"),
              "setup_seconds": setup_s, "query_seconds": query_s,
              "total_seconds": time.monotonic()-begin,
              "left_distinct_coordinates": len(left),
              "right_distinct_coordinates": len(right),
              "total_root_calls": total_root_calls,
              "total_coordinate_hits": total_coordinate_hits,
              "self_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "queries": results}
    with (HERE / "result.json").open("x") as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write("\n")
    print(json.dumps({k: result[k] for k in ("status", "setup_seconds", "query_seconds", "total_root_calls", "total_coordinate_hits")}, sort_keys=True))


if __name__ == "__main__":
    {"freeze": frozen, "run": run}[sys.argv[1]]()
