"""Checked-Sage replay of qualified rational curves and all positive relations."""
import json
from pathlib import Path
from sage.all import EllipticCurve, GF, QQ

HERE = Path(__file__).resolve().parent
selection = json.loads((HERE / "selection.json").read_text())["selected"]
screen = json.loads((HERE / "result.json").read_text())
generators = json.loads((HERE / "generators.json").read_text())
result = json.loads((HERE / "relation-result.json").read_text())

base = EllipticCurve(QQ, [-1, -2])
base_point = base(2, 2)
assert int(base.rank(proof=True)) == 1 and int(base.torsion_subgroup().order()) == 1
base_gens = list(base.gens(proof=True))
assert len(base_gens) == 1 and (base_point == base_gens[0] or base_point == -base_gens[0])
screened = {(r["field_prime"], r["u"]): r["candidate"] for r in screen["rows"] if "candidate" in r}
qualified = {}
for row in generators["rows"]:
    assert row["status"] == "completed"
    g = row["generator"]
    assert g["generator_status"] == "proved" and g["point_is_signed_generator"]
    p, u = row["field_prime"], row["u"]
    c = screened[p, u]
    x, y = c["centered_point"]
    E = EllipticCurve(QQ, [-1, c["curve_B"]])
    P = E(x, y)
    assert int(E.rank(proof=True)) == 1
    assert int(E.torsion_subgroup().order()) == 1
    gens = list(E.gens(proof=True))
    assert len(gens) == 1 and (P == gens[0] or P == -gens[0])
    assert E.j_invariant() != base.j_invariant()
    qualified[p, u] = (E, P)
assert len(qualified) == 3

relations = direct_replays = 0
for (p, q), field in zip(selection, result["fields"]):
    F = GF(p)
    E0 = EllipticCurve(F, [-1, -2])
    assert int(E0.cardinality()) == q
    G = E0(2, 2)
    assert int(G.order()) == q
    Q = 17 * G
    direct = field["first_direct"]
    t1, t2 = direct["t"]
    R1, R2 = Q-t1*G, Q-t2*G
    assert not R1.is_zero() and not R2.is_zero() and R1 != R2
    assert (R1+2*R2).is_zero()
    assert direct["recovered_scalar"] * G == Q
    direct_replays += 1
    for model in field["models"]:
        u = model["u"]
        E, P = (base, base_point) if u == 1 else qualified[p, u]
        assert model["curve_B"] == int(E.a6())
        assert int(E.discriminant()) % p != 0
        assert E.change_ring(F).a_invariants() == E0.a_invariants()
        x, y = map(int, P.xy())
        assert E0(x, y) == u * G
        for hit in model["hits"]:
            a, b = hit["k"]
            t1, t2 = hit["t"]
            U, V = a * P, b * P
            assert (U + 2*V).is_zero()
            assert E0(F(U[0]), F(U[1])) == Q-t1*G
            assert E0(F(V[0]), F(V[1])) == Q-t2*G
            assert hit["recovered_scalar"] * G == Q
            relations += 1
assert relations == 44 and direct_replays == 8
print(json.dumps({"schema": "xedni-nonisomorphic-holdout-sage-audit-v1",
                  "status": "PASS", "qualified_nonbase_curves": 3,
                  "rational_relations": relations, "direct_scalar_replays": direct_replays},
                 sort_keys=True, indent=2))
