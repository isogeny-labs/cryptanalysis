"""Independent Sage audit of the shared-quadratic exceptional-code claim."""
import hashlib
import json
from pathlib import Path

from sage.all import GF, PolynomialRing, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
result = json.loads((HERE / "result.json").read_text())
assert result["status"] == "COMPLETE_SHARED_QUADRATIC_AUDIT"
for path, digest in result["sources_sha256"].items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest

rows = []
for row in result["rows"]:
    n = row["field_degree"]
    R = PolynomialRing(GF(2), "u")
    u = R.gen()
    modulus = u**41 + u**3 + 1 if n == 41 else \
        u**131 + u**13 + u**2 + u + 1
    F = GF(2**n, name="a", modulus=modulus)
    assert F.modulus().list() == modulus.list()
    def elem(value):
        return F(R([(value >> i) & 1 for i in range(n)]))
    seed_mask = 898618
    seed = 112 if n == 41 else seed_mask << 1
    positions = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10] if n == 41 else \
        [i for i in range(33) if i != seed_mask.bit_length() - 1]
    rotation = 12 if n == 41 else 0
    basis = []
    for bit in positions:
        a = elem(1 << (bit + 1))
        basis.append((a*a + elem(seed)*a) ** (2**rotation))
    root = elem(row["other_root"])
    c13, c33 = elem(row["c13"]), elem(row["c33"])
    assert c13 and c33
    assert root*root == c13/c33 and root != 0
    bits = lambda x: [int(x.polynomial()[j]) for j in range(n)]
    M = matrix(GF(2), [bits(b) for b in basis]).transpose()
    rank = M.rank()
    membership = matrix(GF(2), M.nrows(), M.ncols()+1,
                        lambda i, j: M[i,j] if j < M.ncols() else bits(root)[i]).rank() == rank
    assert rank == len(basis) == row["p_rank"]
    assert membership == row["other_root_in_source_span"]
    if n == 41:
        exceptional = []
        for code in range(1 << len(basis)):
            p = sum((basis[i] for i in range(len(basis)) if code >> i & 1), F.zero())
            if c13*p + c33*p**3 == 0:
                exceptional.append(code)
        assert exceptional == row["exhaustive_n41_exception_codes"]
    rows.append({"field_degree": n, "target_index": row["target_index"],
                 "source_span_rank": rank, "other_root_in_source_span": membership,
                 "exception_count": row["exception_count"]})

out = {"status": "INDEPENDENT_SAGE_AUDIT_PASS", "rows": rows,
       "producer_sha256": hashlib.sha256((HERE / "result.json").read_bytes()).hexdigest()}
(HERE / "audit_result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(json.dumps(out, sort_keys=True))
