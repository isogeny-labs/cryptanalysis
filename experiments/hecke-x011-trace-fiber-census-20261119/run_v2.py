#!/usr/bin/env python3
"""Versioned correction: evaluate the removable x=16 branch of the j-map."""
from collections import Counter, defaultdict
from pathlib import Path
import gzip
import hashlib
import json

H = Path(__file__).resolve().parent
P = json.loads((H / "protocol.json").read_text())
C = json.loads((H / "jfun.json").read_text())
N = 11


def mul(a, b, p):
    out = [0] * (N + 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            if i + j <= N:
                out[i + j] = (out[i + j] + x*y) % p
    return out


def power(a, k, p):
    out = [1] + [0]*N
    for _ in range(k):
        out = mul(out, a, p)
    return out


def local_j(p):
    """j at (16,60), with u=x-16 and y(0)=60 on the curve."""
    x = [16, 1] + [0]*(N-1)
    y = [60] + [0]*N
    xp = [power(x, i, p) for i in range(12)]
    assert (2*60+1) % p != 0
    for k in range(1, N+1):
        yy = mul(y, y, p)
        rhs = (xp[3][k]-xp[2][k]-10*xp[1][k]) % p
        y[k] = (rhs-yy[k]-y[k])*pow(121, -1, p) % p
    a = [0]*(N+1)
    for i, j, (num, den) in C["A_terms"]:
        assert den % p
        term = mul(xp[i], power(y, j, p), p)
        factor = num*pow(den, -1, p) % p
        a = [(v+factor*w)%p for v, w in zip(a, term)]
    assert a[:11] == [0]*11, (p, a)
    return a[11]


def main():
    original = (H / "points.jsonl.gz").read_bytes()
    prior = json.loads((H / "result.json").read_text())
    assert hashlib.sha256(original).hexdigest() == prior["ledger_gzip_sha256"]
    rows = [json.loads(x) for x in gzip.decompress(original).splitlines()]
    assert len(rows) == 2222
    replaced = []
    for p in P["primes"]:
        j = local_j(p)
        old = [r for r in rows if r["p"] == p and r["x"] == 16]
        assert sorted(r["y"] for r in old) == sorted((60, (-61) % p))
        trace_candidates = {r["abs_trace"] for r in rows if r.get("p") == p and r.get("j") == j and r["status"] == "regular"}
        assert len(trace_candidates) == 1, (p, j, trace_candidates)
        target = next(r for r in old if r["y"] == 60)
        assert target["status"] == "x16_denominator_zero"
        target.update({"status": "regular", "j": j, "abs_trace": trace_candidates.pop()})
        replaced.append({"p": p, "point": [16, 60], "j": j, "abs_trace": target["abs_trace"]})
    summary = []
    for p in P["primes"]:
        field = [r for r in rows if r["p"] == p]
        regular = [r for r in field if r["status"] == "regular"]
        hist = Counter(r["abs_trace"] for r in regular)
        archived = next((a for a in P["archived_trace_targets"] if a["p"] == p), None)
        summary.append({"p": p, "x011_points": len(field)+1, "regular_points": len(regular),
                        "distinct_regular_j": len({r["j"] for r in regular}),
                        "abs_trace_fibers": len(hist), "max_abs_trace_fiber": max(hist.values()),
                        "trace_histogram": {str(k): v for k,v in sorted(hist.items())},
                        "finite_exceptions": dict(Counter(r["status"] for r in field if r["status"] != "regular")),
                        "archived_trace_fiber": None if archived is None else {
                            "abs_trace": archived["abs_trace"], "full_fiber_points": hist[archived["abs_trace"]],
                            "archived_class_points": archived["archived_class_points"]}})
    raw = b"".join(json.dumps(r, sort_keys=True, separators=(",", ":")).encode()+b"\n" for r in rows)
    packed = gzip.compress(raw, compresslevel=9, mtime=0)
    (H / "points_v2.jsonl.gz").write_bytes(packed)
    result = {"schema": "x011-trace-fiber-result-v2", "status": "complete",
              "prior_result_sha256": hashlib.sha256((H / "result.json").read_bytes()).hexdigest(),
              "j_source_sha256": P["j_source_sha256"], "replaced": replaced,
              "ledger_rows": len(rows), "ledger_sha256": hashlib.sha256(raw).hexdigest(),
              "ledger_gzip_sha256": hashlib.sha256(packed).hexdigest(),
              "ledger_gzip_bytes": len(packed), "summary": summary}
    (H / "result_v2.json").write_text(json.dumps(result, sort_keys=True, indent=2)+"\n")
    print(json.dumps({"replaced": replaced, "summary": [{"p":s["p"],"regular_points":s["regular_points"],"archived_trace_fiber":s["archived_trace_fiber"]} for s in summary]}, sort_keys=True))


if __name__ == "__main__":
    main()
