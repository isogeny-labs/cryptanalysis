#!/usr/bin/env python3
"""Count j multiplicities inside the frozen X0(11) trace fibers."""
import collections
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def main():
    protocol_bytes = (HERE / "protocol_v2.json").read_bytes()
    protocol = json.loads(protocol_bytes)
    source = (HERE / protocol["source"]).resolve()
    packed = source.read_bytes()
    assert hashlib.sha256(packed).hexdigest() == protocol["source_gzip_sha256"]
    raw = gzip.decompress(packed)
    assert hashlib.sha256(raw).hexdigest() == protocol["source_raw_sha256"]
    groups = collections.defaultdict(lambda: collections.Counter())
    regular = collections.Counter()
    exceptions = collections.Counter()
    for line in raw.splitlines():
        row = json.loads(line)
        p = row["p"]
        if row["status"] != "regular":
            exceptions[p] += 1
            continue
        groups[(p, row["abs_trace"])][row["j"]] += 1
        regular[p] += 1
    fibers = []
    for (p, trace), counts in sorted(groups.items()):
        hist = collections.Counter(counts.values())
        fibers.append({
            "p": p,
            "abs_trace": trace,
            "point_count": sum(counts.values()),
            "distinct_j": len(counts),
            "j_multiplicity_histogram": {str(k): v for k, v in sorted(hist.items())},
            "max_j_multiplicity": max(counts.values()),
            "same_j_unordered_pairs": sum(m * (m - 1) // 2 for m in counts.values()),
        })
    assert sorted(regular) == protocol["primes"]
    result = {
        "schema": "x011-fiber-multiplicity-result-v2",
        "protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(),
        "source_gzip_sha256": protocol["source_gzip_sha256"],
        "source_raw_sha256": protocol["source_raw_sha256"],
        "regular_rows": dict(sorted(regular.items())),
        "exception_rows": dict(sorted(exceptions.items())),
        "fibers": fibers,
    }
    (HERE / "result_v2.json").write_bytes(json.dumps(result, sort_keys=True, indent=2).encode() + b"\n")
    print(json.dumps({"fibers": len(fibers), "regular_rows": result["regular_rows"], "status": "complete"}, sort_keys=True))


if __name__ == "__main__":
    main()
