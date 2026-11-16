"""Independent Python enumeration of both frozen quotient certificates."""
import gzip
import json
from fractions import Fraction
from pathlib import Path

import audit  # Rechecks the parent seal, all mod-7 rows and rational 2-torsion.

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "xedni-varying-curve-selection-20261115" / "rows-v2.jsonl.gz"
with gzip.open(PARENT, "rt") as stream:
    source = [json.loads(line) for line in stream]
rows = json.loads((HERE / "rows-v2.json").read_text())
result = json.loads((HERE / "result-v2.json").read_text())
assert len(source) == 1722 and len(rows) == 20
accepted = [(i, r) for i, r in enumerate(source) if r["accepted"]]
assert len(accepted) == 20
count = {7: 0, 11: 0}
for (index, parent), row in zip(accepted, rows):
    assert row["parent_row_index"] == index
    assert row["lifted_points"] == parent["lifted_points"]
    assert row["reduced_relation"] == parent["reduced_relation"]
    A, B = Fraction(parent["A"]), Fraction(parent["B"])
    assert row["rational_2_torsion_x_roots"] == [str(x) for x in audit.roots_of_cubic(A, B)]
    first = None
    for check, prime in zip(row["prime_checks"], (7, 11)):
        assert check["prime"] == prime and check["status"] == "complete"
        a, b = audit.mod(A, prime), audit.mod(B, prime)
        assert (4*a**3 + 27*b**2) % prime != 0
        points = [(x, y) for x in range(prime) for y in range(prime)
                  if (y*y-x*x*x-a*x-b) % prime == 0]
        assert check["curve_order"] == len(points) + 1
        P, Q = [tuple(c % prime for c in pair) for pair in row["lifted_points"]]
        assert P in points and Q in points
        assert check["point_orders"] == [audit.order(P, a, prime), audit.order(Q, a, prime)]
        doubled = {audit.add(T, T, a, prime) for T in points + [None]}
        tests = [P not in doubled, Q not in doubled, audit.add(P, Q, a, prime) not in doubled]
        assert check["quotient_nonzero_tests"] == tests
        assert check["quotient_independent"] == all(tests)
        if first is None and all(tests):
            first = prime
    assert row["certificate_prime"] == first
    if first is not None and not row["rational_2_torsion_x_roots"]:
        count[first] += 1
assert count == {7: 16, 11: 4}
assert result["certified_rows"] == sum(count.values()) == 20
assert result["certificates_by_prime"] == {str(k): v for k, v in count.items()}
assert result["uncertified_parent_indices"] == []
receipt = {"status": "PASS", "accepted_rows": 20, "certified_rows": 20,
           "certificates_by_prime": {str(k): v for k, v in count.items()},
           "method": "independent Python finite-field group and doubling-set enumeration"}
(HERE / "audit-v2.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(json.dumps(receipt, sort_keys=True))
