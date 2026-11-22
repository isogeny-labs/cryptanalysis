"""Fixed-target reciprocal S4 circuit sharing the ab*c product."""

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PRIOR = GOAL / "n41_n131_s4_target_gate_20261013"
spec = importlib.util.spec_from_file_location("prior_circuit", PRIOR / "circuit_compare.py")
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def s4(circuit, a, b, c, t):
    """S4=0 using five full variable-variable products for fixed t.

    p=ab, u=pc, v=c(a+b), e3=u+t(v+p), e4=tu.
    The last two products evaluate e1²e4 and e4(e1²+e3²+e1²e4).
    """
    p = circuit.mul(a, b)
    u = circuit.mul(p, c)
    v = circuit.mul(c, circuit.add(a, b))
    e1 = prior.add_many(circuit, (a, b, c, t))
    e3 = circuit.add(u, circuit.mul(t, circuit.add(v, p)))
    e4 = circuit.mul(t, u)
    x, y = circuit.square(e1), circuit.square(e3)
    xz = circuit.mul(x, e4)
    tail = circuit.mul(e4, prior.add_many(circuit, (x, y, xz)))
    equation = prior.add_many(circuit, (circuit.square(y), circuit.square(x), y, tail))
    circuit.require_zero(equation)


def build_core(n, low_terms, target, variant):
    circuit = prior.KaratsubaCircuit(n, low_terms)
    a, b, c = ([circuit.variable() for _ in range(n)] for _ in range(3))
    t = circuit.constant(target)
    if variant == "prior_s4":
        prior.s4(circuit, a, b, c, t)
    elif variant == "five_mul_s4":
        s4(circuit, a, b, c, t)
    elif variant == "two_s3_links":
        z = [circuit.variable() for _ in range(n)]
        prior.s3(circuit, a, b, z)
        prior.s3(circuit, z, c, t)
    else:
        raise ValueError(variant)
    return {"n": n, "variant": variant, "and_gates": circuit.and_count,
            "xor_rows": len(circuit.xors), "clauses": len(circuit.clauses),
            "variables": circuit.next_var-1,
            "free_intermediate_bits": n if variant == "two_s3_links" else 0}


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["status"] == "FROZEN"
    files = {"source": HERE / "optimized.py",
             "prior_circuit": PRIOR / "circuit_compare.py",
             "prior_audit": PRIOR / "audit_result.json"}
    assert protocol["sha256"] == {key: sha(path) for key, path in files.items()}
    audit = json.loads(files["prior_audit"].read_text())
    rows = []
    for field, n, terms in (("n41", 41, (0, 3)), ("n131", 131, (0, 1, 2, 13))):
        for variant in ("two_s3_links", "prior_s4", "five_mul_s4"):
            row = build_core(n, terms, audit[field]["target_reciprocal"], variant)
            row["field"] = field
            rows.append(row)
    result = {"status": "PASS_FIXED_TARGET_S4_CORE_COUNTS",
              "protocol_sha256": sha(HERE / "protocol.json"), "rows": rows,
              "candidate_id": None}
    (HERE / "core_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(rows, sort_keys=True))


if __name__ == "__main__":
    main()
