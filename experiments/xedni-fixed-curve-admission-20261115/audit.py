"""Independent checked-Sage replay of the full fixed-curve pair census."""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
from sage.all import EllipticCurve, GF

HERE = Path(__file__).resolve().parent
result = json.loads((HERE / "result.json").read_text())
assert result["status"] == "PASS"
queries = admitted = full = 0
for field in result["fields"]:
    p, q = field["field_prime"], field["subgroup_order"]
    E = EllipticCurve(GF(p), [-1, -2])
    P = E(2, 2)
    assert int(P.order()) == field["generator_reduction_order"]
    m = field["subgroup_multiplier_m"]
    G = m * P
    Q = 17 * G
    assert int(G.order()) == q
    assert list(map(int, G.xy())) == field["public_generator"]
    assert list(map(int, Q.xy())) == field["public_target"]
    image = {k * P for k in range(-4, 5)}
    assert len(image) == 9
    points = [Q - t * G for t in range(q)]
    offsets = [t for t, R in enumerate(points) if R in image]
    assert offsets == field["admitted_offsets"]
    assert len(offsets) == field["admitted_offset_count"]
    assert field["admitted_full_pair_support"] == len(offsets) ** 2
    raw = HERE / field["raw_path"]
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == field["raw_sha256"]
    counts = Counter()
    with gzip.open(raw, "rt") as rows:
        for t1 in range(q):
            R1 = points[t1]
            for t2 in range(q):
                R2 = points[t2]
                row = json.loads(next(rows))
                assert row["t"] == [t1, t2]
                if R1.is_zero() or R2.is_zero():
                    status = "identity"
                elif R1 == R2:
                    status = "duplicate"
                elif R1 in image and R2 in image:
                    status = "admitted"
                else:
                    status = "outside_cap"
                assert row["status"] == status
                counts[status] += 1
        assert next(rows, None) is None
    assert dict(counts) == field["counts"]
    assert counts["admitted"] == field["admitted_distinct_nonidentity_pairs"]
    queries += q * q
    admitted += counts["admitted"]
    full += len(offsets) ** 2
assert result["totals"] == {"queries": queries,
                            "admitted_full_pair_support": full,
                            "admitted_distinct_nonidentity_pairs": admitted}
print(json.dumps({"schema": "xedni-fixed-curve-admission-audit-v1",
                  "status": "PASS", "fields": 8, "queries": queries,
                  "admitted_full_pair_support": full,
                  "admitted_distinct_nonidentity_pairs": admitted}, sort_keys=True, indent=2))
