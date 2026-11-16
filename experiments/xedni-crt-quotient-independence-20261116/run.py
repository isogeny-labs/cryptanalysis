"""Bounded exact quotient-certificate census on the archived CRT lift tests."""
import hashlib
import json
import time
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ

HERE = Path(__file__).resolve().parent
PROTOCOL = json.loads((HERE / "protocol.json").read_text())
PARENT = HERE.parent / "xedni-optimized-family-lift-replay-20261115"
PRIMES = PROTOCOL["ordered_primes"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert sha(PARENT / "protocol.json") == PROTOCOL["parent_protocol_sha256"]
assert sha(PARENT / "result.json") == PROTOCOL["parent_result_sha256"]
assert sha(PARENT / "SEAL.sha256") == PROTOCOL["parent_seal_sha256"]
parent = json.loads((PARENT / "result.json").read_text())
assert parent["status"] == "PASS"
field_specs = [(arm["arm"], field) for arm in parent["arms"] for field in arm["fields"]]
assert len(field_specs) == 16
for _, field in field_specs:
    assert sha(PARENT / field["tests_path"]) == field["tests_sha256"]
assert sum(field["counts"]["rational_group_tests"] for _, field in field_specs) == 9688

deadline = time.monotonic() + PROTOCOL["run_cap_seconds"]
output_dir = HERE / "rows"
output_dir.mkdir(exist_ok=True)
summary = {"schema": "xedni-crt-quotient-independence-result-v1",
           "parent_seal_sha256": PROTOCOL["parent_seal_sha256"],
           "status": "running", "expected_rows": 9688,
           "processed_rows": 0, "certified_independent": 0,
           "quotient_only": 0, "torsion_only": 0, "neither": 0,
           "parent_rational_relations": 0,
           "certified_parent_rational_relations": 0,
           "by_arm_field": []}


def save():
    (HERE / "result.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")


for arm, field in field_specs:
    source = PARENT / field["tests_path"]
    destination = output_dir / field["tests_path"]
    counts = Counter()
    with source.open() as stream, destination.open("w") as out:
        for ordinal, line in enumerate(stream):
            if time.monotonic() >= deadline:
                summary["status"] = "capped_900s"
                break
            record = json.loads(line)
            coefficients = [QQ(c) for c in record["coefficients"]]
            E = EllipticCurve(QQ, coefficients)
            point_inputs = record["points"]
            odd_prime = quotient_prime = None
            checks = []
            for prime in PRIMES:
                if any(c.denominator() % prime == 0 for c in coefficients):
                    checks.append({"prime": prime, "status": "nonintegral"})
                    continue
                F = GF(prime)
                if F(E.discriminant()) == 0:
                    checks.append({"prime": prime, "status": "bad_reduction"})
                    continue
                curve = EllipticCurve(F, [F(c) for c in coefficients])
                order = int(curve.cardinality())
                p, q = [curve(F(x), F(y)) for x, y in point_inputs]
                if odd_prime is None and order % 2:
                    odd_prime = prime
                quotient_tests = None
                if quotient_prime is None and order % 4 == 0:
                    doubles = {2*T for T in curve.points()}
                    quotient_tests = [p not in doubles, q not in doubles, p+q not in doubles]
                    if all(quotient_tests):
                        quotient_prime = prime
                checks.append({"prime": prime, "status": "complete", "curve_order": order,
                               "odd_order": bool(order % 2), "quotient_nonzero_tests": quotient_tests})
                if odd_prime is not None and quotient_prime is not None:
                    break
            status = ("certified_independent" if odd_prime is not None and quotient_prime is not None else
                      "quotient_only" if quotient_prime is not None else
                      "torsion_only" if odd_prime is not None else "neither")
            counts[status] += 1
            counts["rows"] += 1
            summary[status] += 1
            summary["processed_rows"] += 1
            summary["parent_rational_relations"] += int(record["rational_relation"])
            summary["certified_parent_rational_relations"] += int(record["rational_relation"] and status == "certified_independent")
            out.write(json.dumps({"source_path": field["tests_path"], "source_ordinal_zero_based": ordinal,
                                  "query_index_one_based": record["query_index_one_based"],
                                  "vector": record["vector"], "rational_relation": record["rational_relation"],
                                  "odd_order_prime": odd_prime, "quotient_prime": quotient_prime,
                                  "status": status, "prime_checks": checks},
                                 sort_keys=True, separators=(",", ":")) + "\n")
            if summary["processed_rows"] % 100 == 0:
                out.flush()
                save()
        else:
            assert counts["rows"] == field["counts"]["rational_group_tests"]
    summary["by_arm_field"].append({"arm": arm, "field_prime": field["field_prime"],
                                    "source_path": field["tests_path"],
                                    "output_path": str(destination.relative_to(HERE)),
                                    "output_sha256": sha(destination), "counts": dict(counts)})
    save()
    print(arm, field["field_prime"], dict(counts), flush=True)
    if summary["status"] == "capped_900s":
        break
else:
    summary["status"] = "complete"
    assert summary["processed_rows"] == 9688
save()
print(json.dumps({key: summary[key] for key in ("status", "processed_rows", "certified_independent", "quotient_only", "torsion_only", "neither", "parent_rational_relations", "certified_parent_rational_relations")}, sort_keys=True))
