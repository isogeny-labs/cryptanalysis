"""Full monic-Weierstrass CRT choice on the frozen two-point census."""

import hashlib
import itertools
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ, crt, matrix

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def centered(n, p):
    n = int(n)
    return n if n <= p // 2 else n - p


def delta(a1, a2, a3, a4, a6):
    b2 = a1 * a1 + 4 * a2
    b4 = a1 * a3 + 2 * a4
    b6 = a3 * a3 + 4 * a6
    b8 = a1 * a1 * a6 + 4 * a2 * a6 - a1 * a3 * a4 + a2 * a3 * a3 - a4 * a4
    return -b2 * b2 * b8 - 8 * b4 ** 3 - 27 * b6 * b6 + 9 * b2 * b4 * b6


def solved(points, a1, a2, a3, modulus=None):
    (x1, y1), (x2, y2) = points
    v1 = y1 * y1 + a1 * x1 * y1 + a3 * y1 - x1 ** 3 - a2 * x1 * x1
    v2 = y2 * y2 + a1 * x2 * y2 + a3 * y2 - x2 ** 3 - a2 * x2 * x2
    if modulus is None:
        a4 = (QQ(v1) - QQ(v2)) / (x1 - x2)
        a6 = QQ(v1) - a4 * x1
    else:
        a4 = (v1 - v2) * pow((x1 - x2) % modulus, -1, modulus) % modulus
        a6 = (v1 - a4 * x1) % modulus
    return a4, a6


def order_mod_l(a1, a2, a3, a4, a6, l, character):
    return l + 1 + sum(character[((a1 * x + a3) ** 2 +
                                   4 * (x ** 3 + a2 * x * x + a4 * x + a6)) % l]
                       for x in range(l))


def coefficient_order(l):
    def key(residues):
        c = tuple(centered(n, l) for n in residues)
        return (sum(map(abs, c)), max(map(abs, c)), c)
    return sorted(itertools.product(range(l), repeat=3), key=key)


def first_candidate(points, l, wanted_order, residue_order, character):
    attempts = 0
    for a1, a2, a3 in residue_order:
        attempts += 1
        a4, a6 = solved(points, a1, a2, a3, l)
        if delta(a1, a2, a3, a4, a6) % l == 0:
            continue
        if order_mod_l(a1, a2, a3, a4, a6, l, character) == wanted_order:
            return (a1, a2, a3, a4, a6), attempts
    return None, attempts


def incidence_rank(points, l):
    F = GF(l)
    rows = []
    for x, y in points:
        x, y = F(x), F(y)
        rows.append([y * y, x * y, y, x ** 3, x ** 2, x, F(1)])
    return int(matrix(F, rows).rank())


def main():
    protocol = json.loads((HERE / "protocol-v2.json").read_text())
    p = protocol["base_curve"]["field_prime"]
    l7 = protocol["auxiliary_gates"]["first"]["prime"]
    l11 = protocol["auxiliary_gates"]["second"]["prime"]
    order7 = protocol["auxiliary_gates"]["first"]["required_order"]
    strict11 = protocol["auxiliary_gates"]["second"]["strict_order"]
    weak11 = protocol["auxiliary_gates"]["second"]["weak_epsilon_1_order"]
    modulus = protocol["coefficient_policy"]["crt_modulus"]
    assert modulus == p * l7 * l11
    Fp = GF(p)
    Ebase = EllipticCurve(Fp, protocol["base_curve"]["weierstrass_coefficients"])
    assert int(Ebase.cardinality()) == protocol["base_curve"]["expected_group_order"]
    base_points = sorted((P for P in Ebase.points() if not P.is_zero()),
                         key=lambda P: (int(P[0]), int(P[1])))
    order_lists = {l: coefficient_order(l) for l in (l7, l11)}
    characters = {}
    for l in (l7, l11):
        squares = {y * y % l for y in range(1, l)}
        characters[l] = [0 if z == 0 else 1 if z in squares else -1 for z in range(l)]

    statuses = Counter()
    total = reduced_hits = accepted = accepted_reduced = accepted_rational = 0
    strict_accepted = weak_accepted = 0
    attempts7 = attempts11_strict = attempts11_weak = 0
    raw_path = HERE / "rows-v2.jsonl"
    with raw_path.open("w") as raw:
        for P1, P2 in itertools.permutations(base_points, 2):
            total += 1
            reduced_event = (P1 + 2 * P2).is_zero()
            reduced_hits += int(reduced_event)
            points = [(centered(P1[0], p), centered(P1[1], p)),
                      (centered(P2[0], p), centered(P2[1], p))]
            rec = {"reduced_points": [[int(P1[0]), int(P1[1])], [int(P2[0]), int(P2[1])]],
                   "lifted_points": points, "reduced_relation": bool(reduced_event),
                   "rational_relation": False, "accepted": False}
            dx = points[0][0] - points[1][0]
            if dx == 0:
                rec["status"] = "same_x_47"
            elif dx % l7 == 0:
                rec["status"] = "same_x_7"
            elif dx % l11 == 0:
                rec["status"] = "same_x_11"
            else:
                c7, count7 = first_candidate(points, l7, order7,
                                             order_lists[l7], characters[l7])
                attempts7 += count7
                rec["attempts_7"] = count7
                if c7 is None:
                    rec["status"] = "no_order_4_at_7"
                else:
                    c11, count11 = first_candidate(points, l11, strict11,
                                                   order_lists[l11], characters[l11])
                    attempts11_strict += count11
                    rec["attempts_11_strict"] = count11
                    arm = "strict"
                    if c11 is None:
                        c11, count11weak = first_candidate(points, l11, weak11,
                                                            order_lists[l11], characters[l11])
                        attempts11_weak += count11weak
                        rec["attempts_11_weak"] = count11weak
                        arm = "weak"
                    if c11 is None:
                        rec["status"] = "no_order_6_or_7_at_11"
                    else:
                        free = []
                        for i in range(3):
                            n = int(crt([0, c7[i], c11[i]], [p, l7, l11]))
                            free.append(n if n <= modulus // 2 else n - modulus)
                        a1, a2, a3 = free
                        a4, a6 = solved(points, a1, a2, a3)
                        rec.update({"arm": arm, "a1": a1, "a2": a2, "a3": a3,
                                    "a4": str(a4), "a6": str(a6),
                                    "chosen_residues_7": list(c7),
                                    "chosen_residues_11": list(c11)})
                        if delta(QQ(a1), QQ(a2), QQ(a3), a4, a6) == 0:
                            rec["status"] = "singular_rational_curve"
                        else:
                            E = EllipticCurve(QQ, [a1, a2, a3, a4, a6])
                            Q1, Q2 = [E([x, y]) for x, y in points]
                            for l, wanted, chosen in ((p, 43, [0, 0, 0, p - 1, p - 2]),
                                                      (l7, order7, c7),
                                                      (l11, strict11 if arm == "strict" else weak11, c11)):
                                assert a4.denominator() % l and a6.denominator() % l
                                assert incidence_rank(points, l) == 2
                                coeffs = [int(GF(l)(c)) for c in (a1, a2, a3, a4, a6)]
                                assert coeffs == list(chosen)
                                assert int(E.change_ring(GF(l)).cardinality()) == wanted
                            rational_event = (Q1 + 2 * Q2).is_zero() if reduced_event else False
                            rec.update({"status": "accepted", "accepted": True,
                                        "rational_relation": bool(rational_event)})
                            accepted += 1
                            accepted_reduced += int(reduced_event)
                            accepted_rational += int(rational_event)
                            strict_accepted += int(arm == "strict")
                            weak_accepted += int(arm == "weak")
            statuses[rec["status"]] += 1
            raw.write(json.dumps(rec, sort_keys=True) + "\n")

    assert total == protocol["frozen_predictions"]["full_ordered_pairs"]
    assert reduced_hits == protocol["frozen_predictions"]["full_reduced_relation_pairs"]
    assert sum(statuses.values()) == total
    print(json.dumps({
        "schema": "xedni-crt-curve-choice-result-v2", "status": "PASS",
        "protocol_sha256": sha(HERE / "protocol-v2.json"),
        "source_sha256": sha(HERE / "run_v2.py"),
        "sage_runtime_sha256": sha(HERE / "sage-runtime-info-v2.json"),
        "rows_sha256": sha(raw_path),
        "total_ordered_pairs": total, "full_reduced_relation_pairs": reduced_hits,
        "accepted_pairs": accepted, "accepted_reduced_relation_pairs": accepted_reduced,
        "accepted_rational_relation_pairs": accepted_rational,
        "strict_accepted_pairs": strict_accepted, "weak_accepted_pairs": weak_accepted,
        "status_counts": dict(statuses),
        "coefficient_search_attempts": {"at_7": attempts7, "at_11_strict": attempts11_strict,
                                        "at_11_weak": attempts11_weak},
        "full_reduced_event_rate": str(Fraction(reduced_hits, total)),
        "accepted_reduced_event_rate": str(Fraction(accepted_reduced, accepted)) if accepted else None,
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
