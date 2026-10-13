"""Independent Sage check of the shared-product S4 identity and field controls."""

import hashlib
import json
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "n41_n131_s4_target_gate_20261013"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode(field, number, n):
    return sum((field.gen() ** i for i in range(n) if number >> i & 1), field.zero())


def s4(a, b, c, t, optimized):
    p = a*b
    if optimized:
        u = p*c
        v = c*(a+b)
        e3 = u+t*(v+p)
        e4 = t*u
    else:
        e3 = p*(c+t)+c*t*(a+b)
        e4 = p*c*t
    e1 = a+b+c+t
    x, y, z = e1**2, e3**2, e4
    return y**2+x**2+y+z*(x+y+x*z)


def main():
    protocol = json.loads((HERE / "sage_protocol.json").read_text())
    files = {"script": HERE / "symbolic_sage.py",
             "runtime": HERE / "sage_runtime_info.json",
             "prior_audit": PRIOR / "audit_result.json",
             "prior_resultant": PRIOR / "resultant.json"}
    assert protocol["status"] == "FROZEN"
    assert protocol["sha256"] == {key: sha(path) for key, path in files.items()}
    R = PolynomialRing(GF(2), ["a", "b", "c", "t"])
    a, b, c, t = R.gens()
    prior, optimized = s4(a, b, c, t, False), s4(a, b, c, t, True)
    assert prior == optimized
    terms = json.loads(files["prior_resultant"].read_text())["terms"]
    listed = sum((a**i*b**j*c**k*t**l for i,j,k,l in terms), R.zero())
    assert optimized == listed
    binary = PolynomialRing(GF(2), "T")
    T = binary.gen()
    audit = json.loads(files["prior_audit"].read_text())
    cases = {}
    for label, n, modulus in (("n41", 41, T**41+T**3+1),
                              ("n131", 131, T**131+T**13+T**2+T+1)):
        field = GF(2**n, "T", modulus=modulus)
        values = [decode(field, number, n) for number in audit[label]["input_reciprocals"]]
        roots = audit[label]["field_roots"]
        for number in roots:
            target = decode(field, number, n)
            assert s4(*values, target, True) == 0
        cases[label] = {"checked_signed_roots": len(roots),
                        "curve_id": protocol["curve_ids"][label]}
    result = {"status": "PASS_SYMBOLIC_AND_FIELD_S4_REFACTOR",
              "protocol_sha256": sha(HERE / "sage_protocol.json"),
              "monomial_count": len(terms), "cases": cases}
    (HERE / "sage_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
