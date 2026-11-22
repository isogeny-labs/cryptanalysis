"""Independent checked-Sage audit of screen cells and all p=313 relation rows."""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
from sage.all import EllipticCurve, GF, QQ

HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

screen = json.loads((HERE / "result.json").read_text())
relation = json.loads((HERE / "relation-result.json").read_text())
assert screen["protocol_sha256"] == sha(HERE / "protocol.json")
assert screen["source_sha256"] == sha(HERE / "screen.py")
assert screen["worker_sha256"] == sha(HERE / "worker.py")
assert relation["protocol_sha256"] == sha(HERE / "relation-protocol.json")
assert relation["screen_sha256"] == sha(HERE / "result.json")
assert relation["generator_sha256"] == sha(HERE / "generator.json")
assert relation["source_sha256"] == sha(HERE / "relation.py")
assert sha(HERE / "relation-rows.jsonl.gz") == relation["raw_sha256"]
assert len(screen["rows"]) == 16
statuses = Counter()
for row in screen["rows"]:
    statuses[row["status"]] += 1
    stdout, stderr = HERE / row["stdout_path"], HERE / row["stderr_path"]
    assert sha(stdout) == row["stdout_sha256"] and sha(stderr) == row["stderr_sha256"]
    if "candidate" not in row:
        assert row["status"] == "timeout"
        continue
    c = row["candidate"]
    p, q, m, u = (row[k] for k in ("field_prime", "subgroup_order", "multiplier_m", "u"))
    E0 = EllipticCurve(GF(p), [-1, -2])
    G = m * E0(2, 2)
    R = u * G
    assert int(G.order()) == q and list(map(int, R.xy())) == c["reduced_point"]
    x, y = c["centered_point"]
    assert [x % p, y % p] == c["reduced_point"]
    B = y * y - x * x * x + x
    E = EllipticCurve(QQ, [-1, B])
    P = E(x, y)
    assert B == c["curve_B"] and E.discriminant() != 0
    assert int(E.discriminant()) % p != 0
    assert int(E.torsion_subgroup().order()) == c["torsion_order"]
    assert E.change_ring(GF(p))(x, y) == R
    assert str(E.j_invariant()) == c["j_invariant"]
    if c["rank_status"] == "proved" and c["rank"] == 1:
        assert int(E.rank(proof=True)) == 1
assert dict(statuses) == screen["status_counts"]

g = json.loads((HERE / "generator.json").read_text())
assert (g["field_prime"], g["u"], g["curve_B"], g["rank"], g["torsion_order"]) == (313, 5, 804408, 1, 1)
E = EllipticCurve(QQ, [-1, 804408]); P = E(-93, -12)
gens = list(E.gens(proof=True))
assert len(gens) == 1 and (P == gens[0] or P == -gens[0])
assert g["point_is_signed_generator"] and g["point_index_up_to_20"] == 1
assert E.j_invariant() != EllipticCurve(QQ, [-1, -2]).j_invariant()

p, q = 313, 331
F = GF(p); E0 = EllipticCurve(F, [-1, -2]); G = E0(2, 2); Q = 17 * G
assert int(G.order()) == q and E.change_ring(F)(-93, -12) == 5 * G
points = [Q - t * G for t in range(q)]
models = [(EllipticCurve(QQ, [-1, -2]), EllipticCurve(QQ, [-1, -2])(2, 2)), (E, P)]
maps = [{k * (u * G): k for k in range(-4, 5)} for u in (1, 5)]
assert len(set(maps[0]) | set(maps[1])) == 17
counts = [Counter(), Counter()]; hits = [[], []]
with gzip.open(HERE / "relation-rows.jsonl.gz", "rt") as raw:
    for t1, R1 in enumerate(points):
        for t2, R2 in enumerate(points):
            row = json.loads(next(raw))
            assert row["t"] == [t1, t2] and len(row["status"]) == 2
            for j, mapping in enumerate(maps):
                if R1.is_zero() or R2.is_zero(): status = "identity"
                elif R1 == R2: status = "duplicate"
                elif R1 not in mapping or R2 not in mapping: status = "outside_cap"
                else:
                    a, b = mapping[R1], mapping[R2]
                    curve, generator = models[j]
                    rational = (a * generator + 2 * (b * generator)).is_zero()
                    public = (R1 + 2 * R2).is_zero()
                    assert rational == public == (a + 2 * b == 0)
                    status = "rational_relation" if rational else "admitted_nonrelation"
                    if rational:
                        recovered = ((t1 + 2 * t2) * pow(3, -1, q)) % q
                        assert recovered * G == Q
                        hits[j].append({"t": [t1, t2], "k": [a, b],
                                        "query_index_one_based": t1 * q + t2 + 1,
                                        "recovered_scalar": recovered})
                assert row["status"][j] == status
                counts[j][status] += 1
    assert next(raw, None) is None
for j, model in enumerate(relation["models"]):
    assert model["counts"] == dict(counts[j]) and model["hits"] == hits[j]
assert relation["queries"] == q * q and relation["membership_tests"] == 2 * q * q
print(json.dumps({"schema": "xedni-nonisomorphic-expansion-audit-v1", "status": "PASS",
                  "screen_cells": len(screen["rows"]), "queries": q * q,
                  "membership_tests": 2 * q * q, "relations": sum(map(len, hits)),
                  "scalar_replays": sum(map(len, hits))}, sort_keys=True, indent=2))
