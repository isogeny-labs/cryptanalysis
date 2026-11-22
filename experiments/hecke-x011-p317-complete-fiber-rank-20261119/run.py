"""Exhaustive signed direct relations on the corrected 40-point p317 fiber."""
from collections import Counter
from fractions import Fraction
from pathlib import Path
import gzip
import hashlib
import itertools
import json
import time

H = Path(__file__).resolve().parent
P = json.loads((H / "protocol.json").read_text())
PRE = json.loads((H / "pre-run.json").read_text())
start = time.monotonic()
p = P["p"]


def neg(A):
    return None if A is None else (A[0], (-A[1]-1) % p)


def add(A, B):
    if A is None:
        return B
    if B is None:
        return A
    x,y = A
    u,v = B
    if x == u and (y+v+1) % p == 0:
        return None
    if A == B:
        top, bottom = 3*x*x-2*x-10, 2*y+1
    else:
        top, bottom = v-y, u-x
    slope = top*pow(bottom % p, -1, p) % p
    intercept = (y-slope*x) % p
    X = (slope*slope+1-x-u) % p
    Y = (-slope*X-intercept-1) % p
    assert (Y*Y+Y-X*X*X+X*X+10*X+20) % p == 0
    return (X,Y)


def scalar(n, A):
    acc = None
    while n:
        if n & 1:
            acc = add(acc,A)
        A = add(A,A)
        n >>= 1
    return acc


def rank(rows, modulus=None):
    pivots = {}
    for raw in rows:
        values = ({i: Fraction(v) for i,v in raw.items() if v} if modulus is None else
                  {i: v % modulus for i,v in raw.items() if v % modulus})
        while values:
            i = min(values)
            if i not in pivots:
                t = values[i]
                pivots[i] = ({j: v/t for j,v in values.items()} if modulus is None else
                             {j: v*pow(t,-1,modulus)%modulus for j,v in values.items()})
                break
            t = values[i]
            for j,v in pivots[i].items():
                w = values.get(j,0)-t*v
                if modulus is not None:
                    w %= modulus
                if w:
                    values[j] = w
                else:
                    values.pop(j,None)
    return len(pivots)


def row(raw):
    return {int(i):int(v) for i,v in raw.items() if v}


def checked_row(r, points):
    total = None
    for i,c in r.items():
        for _ in range(abs(c)):
            total = add(total, points[i] if c>0 else neg(points[i]))
    assert total is None


def main():
    blob = (H / "archived-inputs.json").read_bytes()
    assert hashlib.sha256(blob).hexdigest() == PRE["archived_inputs_sha256"]
    archived = json.loads(blob)
    ledger_blob = (H / P["corrected_ledger"]).resolve().read_bytes()
    assert hashlib.sha256(ledger_blob).hexdigest() == P["corrected_ledger_sha256"] == PRE["corrected_ledger_sha256"]
    ledger = [json.loads(x) for x in gzip.decompress(ledger_blob).splitlines()]
    fiber = {(r["x"],r["y"]) for r in ledger if r["p"] == p and r["status"] == "regular" and r["abs_trace"] == 2}
    points = [tuple(A) for A in archived["class_points"]] + [(16,60)]
    assert len(points) == len(set(points)) == len(fiber) == 40 and set(points) == fiber
    assert scalar(305, points[-1]) is None
    assert scalar(5, points[-1]) is None
    generator = tuple(archived["projection_generator"])
    assert scalar(61,generator) is None and generator is not None
    qcoords = []
    multiples = {scalar(k,generator):k for k in range(61)}
    assert len(multiples) == 61
    for A in points:
        qcoords.append(multiples[scalar(5,A)])
    assert qcoords[:39] == archived["projection_coordinates_mod61"]
    base = [row(x) for x in archived["base_rows"]]
    closed = [row(x) for x in archived["closed_rows"]]
    short = [row(x) for x in archived["short_cancellation_rows"]]
    for r in base+closed+short:
        checked_row(r,points)
        assert sum(c*qcoords[i] for i,c in r.items()) % 61 == 0
    candidate_rows = []
    counts = Counter()
    new_point_rows = Counter()
    for support in range(1,4):
        for inds in itertools.combinations(range(40),support):
            for rest in itertools.product(P["signed_coefficient_order"],repeat=support-1):
                signs = (1,)+rest
                total = None
                for i,sgn in zip(inds,signs):
                    total = add(total,points[i] if sgn==1 else neg(points[i]))
                if total is not None:
                    continue
                r = dict(zip(inds,signs))
                assert sum(c*qcoords[i] for i,c in r.items()) % 61 == 0
                candidate_rows.append({"indices":list(inds),"coefficients":list(signs)})
                counts[support] += 1
                if 39 in inds:
                    new_point_rows[support] += 1
        assert time.monotonic()-start < P["resource_cap_seconds"]
    direct = [dict(zip(c["indices"],c["coefficients"])) for c in candidate_rows]
    rank_sets = {"archived_base":base,"archived_base_closed":base+closed,
                 "archived_all":base+closed+short,"direct_only":direct,
                 "archived_all_plus_direct":base+closed+short+direct}
    ranks = {name:{"QQ":rank(rows),"F61":rank(rows,61)} for name,rows in rank_sets.items()}
    raw = b"".join(json.dumps(r,sort_keys=True,separators=(",", ":")).encode()+b"\n" for r in candidate_rows)
    packed = gzip.compress(raw,compresslevel=9,mtime=0)
    (H / "direct-rows.jsonl.gz").write_bytes(packed)
    result = {"schema":"x011-p317-complete-fiber-rank-result-v1","status":"complete",
              "protocol_sha256":hashlib.sha256((H/"protocol.json").read_bytes()).hexdigest(),
              "pre_run_sha256":hashlib.sha256((H/"pre-run.json").read_bytes()).hexdigest(),
              "points":len(points),"new_point_index":39,"new_point_order":5,
              "new_point_q_coordinate_mod61":qcoords[39],
              "candidate_counts":{str(k):counts[k] for k in range(1,4)},
              "new_point_candidate_counts":{str(k):new_point_rows[k] for k in range(1,4)},
              "archived_direct_39_count":archived["direct_candidate_count"],
              "ranks":ranks,"direct_rows_sha256":hashlib.sha256(raw).hexdigest(),
              "direct_rows_gzip_sha256":hashlib.sha256(packed).hexdigest(),
              "candidate_id":None,"target_online_ms":None}
    (H/"result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"candidate_counts":result["candidate_counts"],"new_point_candidate_counts":result["new_point_candidate_counts"],"ranks":ranks},sort_keys=True))


if __name__ == "__main__":
    main()
