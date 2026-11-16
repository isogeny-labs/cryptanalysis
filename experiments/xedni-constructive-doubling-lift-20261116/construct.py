"""Construct rational tangent lifts from every frozen selected-vector query."""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
protocol = json.loads((HERE / "protocol.json").read_text())
rows_path = ROOT / "xedni-vector-shift-lift-search-20261116" / "rows.jsonl"
registry_path = ROOT / "xedni-crt-band-panel-20261115" / "result.json"
assert hashlib.sha256(rows_path.read_bytes()).hexdigest() == protocol["source_rows_sha256"]
assert hashlib.sha256(registry_path.read_bytes()).hexdigest() == protocol["source_registry_sha256"]
registry = {r["field_prime"]: r for r in json.loads(registry_path.read_text())["fields"]}


def centered(z, p):
    z %= p
    return z if z <= p//2 else z-p


seen = set()
counts = Counter()
out = HERE / "rows.jsonl"
with out.open("w") as stream:
    for line in rows_path.open():
        row = json.loads(line)
        if row.get("kind") != "candidate" or row["vector"] != [2, -1]:
            continue
        key = (row["field_prime"], row["target_index"], *row["offsets"])
        if key in seen:
            continue
        seen.add(key)
        p = row["field_prime"]
        q = registry[p]["subgroup_order"]
        U, V = row["public_points"]
        record = {"field_prime": p, "subgroup_order": q,
                  "target_index": row["target_index"], "offsets": row["offsets"],
                  "fixture_scalar": row["fixture_scalar"], "U": U, "V": V,
                  "public_relation_diagnostic": row["public_relation_diagnostic"],
                  "status": None}
        counts["query_events"] += 1
        if U is None:
            record["status"] = "U_infinity"
        elif U[1] % p == 0:
            record["status"] = "U_y_zero"
        else:
            x, y = centered(U[0], p), centered(U[1], p)
            s = centered((3*U[0]**2 - 1) * pow(2*U[1], -1, p), p)
            A = 2*y*s - 3*x*x
            B = y*y - x*x*x - A*x
            u = s*s - 2*x
            v = s*(x-u) - y
            disc = -16*(4*A**3 + 27*B**2)
            predicted = [u % p, v % p]
            matches = predicted == V
            record.update({"x": x, "y": y, "s": s, "A": A, "B": B,
                           "R": [u, v], "discriminant": disc,
                           "R_reduction": predicted, "matches_V": matches,
                           "derived_scalar": (2*row["offsets"][0]-row["offsets"][1]) % q})
            if disc == 0:
                record["status"] = "singular_rational_curve"
            elif disc % p == 0 or A % p != p-1 or B % p != p-2:
                record["status"] = "bad_reduction"
            else:
                record["status"] = "constructed"
                counts["matches_V"] += int(matches)
                counts["nonmatching_V"] += int(not matches)
                if matches:
                    assert record["derived_scalar"] == row["fixture_scalar"]
        counts[record["status"]] += 1
        stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")

assert counts["query_events"] == 8*4*16
result = {"schema": "xedni-constructive-doubling-lift-result-v1",
          "status": "complete" if counts["constructed"] == 512 else "exceptional",
          "counts": dict(sorted(counts.items())),
          "source_rows_sha256": protocol["source_rows_sha256"],
          "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest(),
          "rows_sha256": hashlib.sha256(out.read_bytes()).hexdigest()}
(HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2, sort_keys=True))
