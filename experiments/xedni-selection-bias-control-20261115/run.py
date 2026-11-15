"""Exact selected and uniform relation-event counts for a rational lift panel."""

import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ, ZZ

HERE = Path(__file__).resolve().parent


def sha(name):
    return hashlib.sha256((HERE / name).read_bytes()).hexdigest()


def main():
    spec = json.loads((HERE / "protocol.json").read_text())
    curve = spec["curve"]
    sample = spec["sample"]
    predicted = spec["frozen_predictions"]
    E = EllipticCurve(QQ, curve["weierstrass_a_invariants"])
    P = E(curve["generator"])
    p = curve["reduction_prime"]
    assert ZZ(E.discriminant()) % p != 0
    Ered = E.change_ring(GF(p))
    Pred = Ered([GF(p)(P[0]), GF(p)(P[1])])
    q = int(Pred.order())
    assert q == curve["expected_reduced_generator_order"]
    assert q == int(Ered.cardinality())

    multipliers = sample["selected_lift_multipliers"]
    assert len(set(multipliers)) == len(multipliers)
    rational_points = {m: m * P for m in multipliers}
    reduced_points = {m: m * Pred for m in multipliers}
    assert all(not point.is_zero() for point in rational_points.values())
    assert all(Ered([GF(p)(point[0]), GF(p)(point[1])]) == reduced_points[m]
               for m, point in rational_points.items())
    assert len(set(reduced_points.values())) == len(multipliers)

    relation = sample["relation_vector"]
    s = sample["xedni_sample_map_s"]
    w = sample["xedni_sample_map_w"]
    selected_total = 0
    selected_event = 0
    mapped_samples = set()
    for m in itertools.permutations(multipliers, sample["r"]):
        lifted = [rational_points[x] for x in m]
        reduced = [reduced_points[x] for x in m]
        event_lifted = sum((a * point for a, point in zip(relation, lifted)), E(0)).is_zero()
        event_reduced = sum((a * point for a, point in zip(relation, reduced)), Ered(0)).is_zero()
        assert event_lifted == event_reduced
        t = tuple((si * w - mi) % q for si, mi in zip(s, m))
        assert tuple((si * w - ti) % q for si, ti in zip(s, t)) == tuple(mi % q for mi in m)
        mapped_samples.add(t)
        selected_total += 1
        selected_event += int(event_lifted)
    assert len(mapped_samples) == selected_total

    # Exhaust the full ordered, distinct, nonidentity subgroup law.
    uniform_total = 0
    uniform_event = 0
    for x in range(1, q):
        for y in range(1, q):
            if y == x:
                continue
            for z in range(1, q):
                if z == x or z == y:
                    continue
                uniform_total += 1
                uniform_event += int((x + y - z) % q == 0)
    assert uniform_total == (q - 1) * (q - 2) * (q - 3)
    assert uniform_event == (q - 1) * (q - 3)

    selected_fraction = Fraction(selected_event, selected_total)
    uniform_fraction = Fraction(uniform_event, uniform_total)
    enrichment = selected_fraction / uniform_fraction
    assert selected_total == predicted["selected_total"]
    assert selected_event == predicted["selected_relation_count"]
    assert uniform_total == predicted["uniform_total"]
    assert uniform_event == predicted["uniform_relation_count"]
    assert str(selected_fraction) == predicted["selected_fraction"]
    assert str(uniform_fraction) == predicted["uniform_fraction"]

    print(json.dumps({
        "schema": "xedni-selection-bias-control-result-v1",
        "status": "PASS",
        "protocol_sha256": sha("protocol.json"),
        "source_sha256": sha("run.py"),
        "sage_runtime_sha256": sha("sage-runtime-info.json"),
        "reduction_prime": p,
        "reduced_curve_order": int(Ered.cardinality()),
        "reduced_generator_order": q,
        "selected_total": selected_total,
        "selected_relation_count": selected_event,
        "selected_fraction": str(selected_fraction),
        "uniform_total": uniform_total,
        "uniform_relation_count": uniform_event,
        "uniform_fraction": str(uniform_fraction),
        "event_enrichment_factor": str(enrichment),
        "selected_map_preimages": len(mapped_samples),
        "selected_point_count": len(multipliers),
        "relation_vector": relation,
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
