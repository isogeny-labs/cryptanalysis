#!/usr/bin/env python3
"""Independent sort-and-group replay of the frozen census ledger."""
import gzip
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    protocol = json.loads((HERE / "protocol_v2.json").read_text())
    result = json.loads((HERE / "result_v2.json").read_text())
    data = (HERE / protocol["source"]).resolve().read_bytes()
    assert hashlib.sha256(data).hexdigest() == protocol["source_gzip_sha256"]
    raw = gzip.decompress(data)
    assert hashlib.sha256(raw).hexdigest() == protocol["source_raw_sha256"]
    rows = [json.loads(line) for line in raw.splitlines()]
    assert len(rows) == 2222
    point_keys = [(r["p"], r["x"], r["y"]) for r in rows if r["status"] == "regular"]
    assert len(point_keys) == len(set(point_keys))
    regular = sorted((r["p"], r["abs_trace"], r["j"]) for r in rows if r["status"] == "regular")
    assert len(regular) == sum(int(n) for n in result["regular_rows"].values())
    replay = []
    for (p, t), fiber_it in itertools.groupby(regular, key=lambda v: v[:2]):
        js = [v[2] for v in fiber_it]
        counts = [len(list(g)) for _, g in itertools.groupby(js)]
        multiplicities = {str(m): counts.count(m) for m in sorted(set(counts))}
        replay.append({
            "p": p, "abs_trace": t, "point_count": len(js),
            "distinct_j": len(counts), "j_multiplicity_histogram": multiplicities,
            "max_j_multiplicity": max(counts),
            "same_j_unordered_pairs": sum((m * m - m) // 2 for m in counts),
        })
    assert replay == result["fibers"]
    source_result = json.loads((HERE / "../hecke-x011-trace-fiber-census-20261119/result_v2.json").read_text())
    for s in source_result["summary"]:
        p = s["p"]
        assert sum(f["point_count"] for f in replay if f["p"] == p) == s["regular_points"]
        assert {str(f["abs_trace"]): f["point_count"] for f in replay if f["p"] == p} == s["trace_histogram"]
    audit = {"schema": "x011-fiber-multiplicity-audit-v2", "status": "PASS",
             "source_rows": len(rows), "regular_rows": len(regular), "fibers": len(replay),
             "result_sha256": hashlib.sha256((HERE / "result_v2.json").read_bytes()).hexdigest()}
    (HERE / "audit_v2.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
