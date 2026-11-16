"""Deterministic CRT coefficient choice through every reduced point pair."""

import hashlib
import itertools
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ, ZZ, crt, matrix

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def centered(n, p):
    return n if n <= p // 2 else n - p


def cubic_discriminant(a2, a4, a6):
    return a2 * a2 * a4 * a4 - 4 * a4 ** 3 - 4 * a2 ** 3 * a6 - 27 * a6 * a6 + 18 * a2 * a4 * a6


def coefficients_mod_l(points, a2, l):
    (x1, y1), (x2, y2) = points
    if (x1 - x2) % l == 0:
        return None
    v1 = (y1 * y1 - x1 ** 3 - a2 * x1 * x1) % l
    v2 = (y2 * y2 - x2 ** 3 - a2 * x2 * x2) % l
    a4 = (v1 - v2) * pow((x1 - x2) % l, -1, l) % l
    a6 = (v1 - a4 * x1) % l
    return a4, a6


def curve_order_mod_l(a2, a4, a6, l, cache):
    key = (l, a2 % l, a4 % l, a6 % l)
    if key not in cache:
        square_counts = Counter(y * y % l for y in range(l))
        cache[key] = 1 + sum(square_counts[(x ** 3 + a2 * x * x + a4 * x + a6) % l]
                             for x in range(l))
    return cache[key]


def candidates_for_prime(points, l, orders, cache):
    candidates = {order: [] for order in orders}
    for a2 in range(l):
        other = coefficients_mod_l(points, a2, l)
        if other is None:
            continue
        a4, a6 = other
        if cubic_discriminant(a2, a4, a6) % l == 0:
            continue
        order = curve_order_mod_l(a2, a4, a6, l, cache)
        if order in candidates:
            candidates[order].append(a2)
    return candidates


def rational_coefficients(points, a2):
    (x1, y1), (x2, y2) = points
    v1 = QQ(y1 * y1 - x1 ** 3 - a2 * x1 * x1)
    v2 = QQ(y2 * y2 - x2 ** 3 - a2 * x2 * x2)
    a4 = (v1 - v2) / (x1 - x2)
    a6 = v1 - a4 * x1
    return a4, a6


def incidence_rank(points, l):
    F = GF(l)
    rows = []
    for x, y in points:
        x, y = F(x), F(y)
        rows.append([y * y, x * y, y, x ** 3, x ** 2, x, F(1)])
    return int(matrix(F, rows).rank())


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    p = protocol["base_curve"]["field_prime"]
    l7 = protocol["auxiliary_gates"]["first"]["prime"]
    l11 = protocol["auxiliary_gates"]["second"]["prime"]
    order7 = protocol["auxiliary_gates"]["first"]["required_order"]
    strict11 = protocol["auxiliary_gates"]["second"]["strict_order"]
    weak11 = protocol["auxiliary_gates"]["second"]["weak_epsilon_1_order"]
    modulus = protocol["coefficient_policy"]["crt_modulus"]
    assert modulus == p * l7 * l11
    Ebase = EllipticCurve(GF(p), [-1, -2])
    assert int(Ebase.cardinality()) == protocol["base_curve"]["expected_group_order"]
    base_points = sorted((P for P in Ebase.points() if not P.is_zero()),
                         key=lambda P: (int(P[0]), int(P[1])))
    assert len(base_points) == 42

    order_cache = {}
    statuses = Counter()
    total = reduced_hits = accepted = accepted_reduced = accepted_rational = 0
    strict_accepted = weak_accepted = 0
    candidate7_total = candidate11_strict_total = candidate11_weak_total = 0
    raw_path = HERE / "rows.jsonl"
    with raw_path.open("w") as raw:
        for P1, P2 in itertools.permutations(base_points, 2):
            total += 1
            reduced_event = (P1 + 2 * P2).is_zero()
            reduced_hits += int(reduced_event)
            points = [(centered(P1[0], p), centered(P1[1], p)),
                      (centered(P2[0], p), centered(P2[1], p))]
            rec = {"reduced_points": [[int(P1[0]), int(P1[1])],
                                      [int(P2[0]), int(P2[1])]],
                   "lifted_points": points,
                   "reduced_relation": bool(reduced_event),
                   "rational_relation": False,
                   "accepted": False}
            if points[0][0] == points[1][0]:
                rec["status"] = "same_x_47"
            elif (points[0][0] - points[1][0]) % l7 == 0:
                rec["status"] = "same_x_7"
            elif (points[0][0] - points[1][0]) % l11 == 0:
                rec["status"] = "same_x_11"
            else:
                c7 = candidates_for_prime(points, l7, [order7], order_cache)
                c11 = candidates_for_prime(points, l11, [strict11, weak11], order_cache)
                rec["candidate_residues_7"] = c7[order7]
                rec["candidate_residues_11_strict"] = c11[strict11]
                rec["candidate_residues_11_weak"] = c11[weak11]
                candidate7_total += len(c7[order7])
                candidate11_strict_total += len(c11[strict11])
                candidate11_weak_total += len(c11[weak11])
                if not c7[order7]:
                    rec["status"] = "no_order_4_at_7"
                elif not c11[strict11] and not c11[weak11]:
                    rec["status"] = "no_order_6_or_7_at_11"
                else:
                    choices = []
                    for arm, residues11 in (("strict", c11[strict11]), ("weak", c11[weak11])):
                        for residue7, residue11 in itertools.product(c7[order7], residues11):
                            n = int(crt([0, residue7, residue11], [p, l7, l11]))
                            if n > modulus // 2:
                                n -= modulus
                            choices.append((0 if arm == "strict" else 1, abs(n), n,
                                            arm, residue7, residue11))
                    choices.sort()
                    rec["crt_candidate_count"] = len(choices)
                    rec["status"] = "all_crt_candidates_singular"
                    for _, _, a2, arm, residue7, residue11 in choices:
                        a4, a6 = rational_coefficients(points, a2)
                        if cubic_discriminant(QQ(a2), a4, a6) == 0:
                            continue
                        E = EllipticCurve(QQ, [0, QQ(a2), 0, a4, a6])
                        Q1, Q2 = [E([x, y]) for x, y in points]
                        for l, wanted in ((p, Ebase.cardinality()),
                                          (l7, order7),
                                          (l11, strict11 if arm == "strict" else weak11)):
                            assert a4.denominator() % l and a6.denominator() % l
                            assert incidence_rank(points, l) == 2
                            if l == p:
                                assert (a2 % p, int(GF(p)(a4)), int(GF(p)(a6))) == (0, p - 1, p - 2)
                            assert int(E.change_ring(GF(l)).cardinality()) == int(wanted)
                        rational_event = (Q1 + 2 * Q2).is_zero() if reduced_event else False
                        rec.update({"status": "accepted", "accepted": True,
                                    "arm": arm, "a2": a2, "a4": str(a4), "a6": str(a6),
                                    "a2_mod_7": residue7, "a2_mod_11": residue11,
                                    "rational_relation": bool(rational_event)})
                        accepted += 1
                        accepted_reduced += int(reduced_event)
                        accepted_rational += int(rational_event)
                        strict_accepted += int(arm == "strict")
                        weak_accepted += int(arm == "weak")
                        break
            statuses[rec["status"]] += 1
            raw.write(json.dumps(rec, sort_keys=True) + "\n")

    assert total == protocol["frozen_predictions"]["full_ordered_pairs"]
    assert reduced_hits == protocol["frozen_predictions"]["full_reduced_relation_pairs"]
    assert sum(statuses.values()) == total
    print(json.dumps({
        "schema": "xedni-crt-curve-choice-result-v1", "status": "PASS",
        "protocol_sha256": sha(HERE / "protocol.json"),
        "source_sha256": sha(HERE / "run.py"),
        "sage_runtime_sha256": sha(HERE / "sage-runtime-info.json"),
        "rows_sha256": sha(raw_path),
        "total_ordered_pairs": total, "full_reduced_relation_pairs": reduced_hits,
        "accepted_pairs": accepted, "accepted_reduced_relation_pairs": accepted_reduced,
        "accepted_rational_relation_pairs": accepted_rational,
        "strict_accepted_pairs": strict_accepted, "weak_accepted_pairs": weak_accepted,
        "status_counts": dict(statuses),
        "candidate_residue_counts": {"order_4_at_7": candidate7_total,
                                     "order_6_at_11": candidate11_strict_total,
                                     "order_7_at_11": candidate11_weak_total},
        "full_reduced_event_rate": str(Fraction(reduced_hits, total)),
        "accepted_reduced_event_rate": str(Fraction(accepted_reduced, accepted)) if accepted else None,
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
