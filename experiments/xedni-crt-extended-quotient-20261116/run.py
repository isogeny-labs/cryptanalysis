"""Versioned extended quotient search for every unresolved CRT-lift row."""
import hashlib
import json
import time
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ, prime_range

HERE = Path(__file__).resolve().parent
PROTOCOL = json.loads((HERE / "protocol.json").read_text())
PARENT = HERE.parent / "xedni-crt-quotient-independence-20261116"
ARCHIVE = HERE.parent / "xedni-optimized-family-lift-replay-20261115"
PRIMES = [int(p) for p in prime_range(101, 500)]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert sha(PARENT / "protocol.json") == PROTOCOL["parent_protocol_sha256"]
assert sha(PARENT / "result.json") == PROTOCOL["parent_result_sha256"]
assert sha(PARENT / "SEAL.sha256") == PROTOCOL["parent_seal_sha256"]
parent = json.loads((PARENT / "result.json").read_text())
archive = json.loads((ARCHIVE / "result.json").read_text())
assert parent["status"] == "complete" and archive["status"] == "PASS"
assert parent["processed_rows"] == 9688
assert parent["torsion_only"] == 1798 and parent["quotient_only"] == 3

deadline = time.monotonic() + PROTOCOL["run_cap_seconds"]
rows_path = HERE / "rows.jsonl"
summary = {"schema": "xedni-crt-extended-quotient-result-v1", "status": "running",
           "parent_result_sha256": PROTOCOL["parent_result_sha256"],
           "prime_count": len(PRIMES), "first_prime": PRIMES[0], "last_prime": PRIMES[-1],
           "expected_unresolved_rows": 1801, "processed_unresolved_rows": 0,
           "new_quotient_certificates": 0, "new_torsion_certificates": 0,
           "still_torsion_only": 0, "still_quotient_only": 0,
           "cumulative_certified": parent["certified_independent"],
           "by_arm_field": []}


def save():
    (HERE / "result.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")


with rows_path.open("w") as output:
    for spec in parent["by_arm_field"]:
        path = spec["source_path"]
        original = ARCHIVE / path
        prior = PARENT / spec["output_path"]
        archive_spec = next(f for arm in archive["arms"] for f in arm["fields"] if f["tests_path"] == path)
        assert sha(original) == archive_spec["tests_sha256"]
        assert sha(prior) == spec["output_sha256"]
        local = Counter()
        with original.open() as original_stream, prior.open() as prior_stream:
            for ordinal, (original_line, prior_line) in enumerate(zip(original_stream, prior_stream)):
                row = json.loads(original_line)
                old = json.loads(prior_line)
                assert old["source_ordinal_zero_based"] == ordinal
                if old["status"] == "certified_independent":
                    continue
                if time.monotonic() >= deadline:
                    summary["status"] = "capped_900s"
                    break
                coefficients = [QQ(c) for c in row["coefficients"]]
                E = EllipticCurve(QQ, coefficients)
                checks = []
                quotient_prime = old["quotient_prime"]
                torsion_certificate = old["odd_order_prime"]
                rational_2_roots = None
                if old["status"] == "quotient_only":
                    rational_2_roots = [str(root) for root, _ in E.division_polynomial(2).roots(ring=QQ)]
                    if not rational_2_roots:
                        torsion_certificate = "rational_2_division_polynomial_has_no_root"
                        summary["new_torsion_certificates"] += 1
                else:
                    assert old["status"] == "torsion_only" and torsion_certificate is not None
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
                        tests = None
                        if order % 4 == 0:
                            P, Q = [curve(F(x), F(y)) for x, y in row["points"]]
                            doubles = {2*T for T in curve.points()}
                            tests = [P not in doubles, Q not in doubles, P+Q not in doubles]
                            if all(tests):
                                quotient_prime = prime
                                summary["new_quotient_certificates"] += 1
                        checks.append({"prime": prime, "status": "complete", "curve_order": order,
                                       "quotient_nonzero_tests": tests})
                        if quotient_prime is not None:
                            break
                status = "certified_independent" if quotient_prime is not None and torsion_certificate is not None else old["status"]
                if status == "certified_independent":
                    summary["cumulative_certified"] += 1
                elif status == "torsion_only":
                    summary["still_torsion_only"] += 1
                else:
                    summary["still_quotient_only"] += 1
                summary["processed_unresolved_rows"] += 1
                local[status] += 1
                local["rows"] += 1
                output.write(json.dumps({"source_path": path, "source_ordinal_zero_based": ordinal,
                                         "query_index_one_based": row["query_index_one_based"],
                                         "vector": row["vector"], "parent_status": old["status"],
                                         "status": status, "inherited_odd_order_prime": old["odd_order_prime"],
                                         "inherited_quotient_prime": old["quotient_prime"],
                                         "quotient_prime": quotient_prime, "torsion_certificate": torsion_certificate,
                                         "rational_2_torsion_x_roots": rational_2_roots,
                                         "extended_prime_checks": checks},
                                        sort_keys=True, separators=(",", ":")) + "\n")
                if summary["processed_unresolved_rows"] % 50 == 0:
                    output.flush()
                    save()
            if summary["status"] != "capped_900s":
                assert next(original_stream, None) is None and next(prior_stream, None) is None
        summary["by_arm_field"].append({"arm": spec["arm"], "field_prime": spec["field_prime"],
                                        "source_path": path, "counts": dict(local)})
        output.flush()
        save()
        print(path, dict(local), flush=True)
        if summary["status"] == "capped_900s":
            break
    else:
        summary["status"] = "complete"
        assert summary["processed_unresolved_rows"] == 1801
save()
summary["rows_sha256"] = sha(rows_path)
save()
print(json.dumps({key: summary[key] for key in ("status", "processed_unresolved_rows", "new_quotient_certificates", "new_torsion_certificates", "still_torsion_only", "still_quotient_only", "cumulative_certified")}, sort_keys=True))
