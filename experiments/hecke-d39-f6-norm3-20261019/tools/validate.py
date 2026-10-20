#!/usr/bin/env python3
"""Independent reduced-form and saved-matrix audit of the Hecke floor rule."""
import hashlib
import json
from fractions import Fraction
from math import gcd, isqrt
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCHIVE = Path("/Volumes/SSD990/ecdlp-hardness-work/prime-field-smallness/data")
CASES = [
    ("D7_f30", ARCHIVE / "exp11_class_walk_D7_f30.json", "e2fd9d4ff9d4f9362c25f34544c95931c944a472103213cd33ca9b18c6c5b17f", 30),
    ("D7_f210_restricted", ARCHIVE / "exp11_class_walk_D7_f210.json", "494d4400a8ff67e44e28df96dd6211d65c83a50997198afa46e8f6dd4a33822b", 30),
    ("D7_f420", ARCHIVE / "exp11_class_walk_D7_f420.json", "dbdd73da797d4fb7044ff4a687573783b0cf225755077c3c5a5026cb998b5205", 420),
    ("D7_f1260", ARCHIVE / "exp11_class_walk_D7_f1260.json", "36f8b632f92bab231e24cc4d5082e0445f5c46c5ffd97bbb0ded6d051b0f6fce", 1260),
    ("D8_f210", ARCHIVE / "exp11_class_walk_D8_f210.json", "0329084f1215f728a11a655125dbbbfa64ad39405235355212c68a551cefe17e", 210),
    ("D7_f42_holdout", HERE / "data/exp11_class_walk_D7_f42.json", "f4a8b964dad70fc8d697d1163f2fa8a963a44882731ae18518e1ace2951c311d", 42),
    ("D7_f60_holdout", HERE / "data/exp11_class_walk_D7_f60.json", "39faa7734979733b3035fb6c25c39b1c0a5e389bd4c54a6c65965da1d8cce434", 60),
    ("D7_f70_holdout", HERE / "data/exp11_class_walk_D7_f70.json", "efe387fe31c22001b9eeaabe72d920835f80a2300b1aaa4d151015b05d2357ef", 70),
    ("D7_f90_holdout", HERE / "data/exp11_class_walk_D7_f90.json", "4cb80fb8f8a10a138455dbf6be0c3fb229af6d6367f255000bf06ab9010f38b8", 90),
    ("D7_f150_holdout", HERE / "data/exp11_class_walk_D7_f150.json", "49e33851a0ed64e470f1693001664c6f76f58aea9e2e65b6974d1618dfa15e06", 150),
    ("D7_f210_holdout", HERE / "data/exp11_class_walk_D7_f210.json", "616c4583ac761e9eb965c9ce36b366e3a67b104b881d9eb8a8cee47f2799844e", 210),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def class_number_forms(discriminant):
    assert discriminant < -4 and discriminant % 4 in (0, 1)
    count = 0
    for a in range(1, isqrt((-discriminant) // 3) + 2):
        for b in range(-a, a + 1):
            numerator = b * b - discriminant
            if numerator % (4 * a):
                continue
            c = numerator // (4 * a)
            if a > c or (b < 0 and (abs(b) == a or a == c)):
                continue
            if gcd(gcd(a, abs(b)), c) == 1:
                count += 1
    return count


def prime_factors(n):
    factors = []
    d = 2
    while d * d <= n:
        if n % d == 0:
            factors.append(d)
            while n % d == 0:
                n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors


def kronecker_at_prime(discriminant, prime):
    if prime == 2:
        if discriminant % 2 == 0:
            return 0
        return 1 if discriminant % 8 == 1 else -1
    residue = discriminant % prime
    if residue == 0:
        return 0
    euler = pow(residue, (prime - 1) // 2, prime)
    return 1 if euler == 1 else -1


def class_number_formula(discriminant, conductor):
    assert discriminant in (-7, -8)
    base = class_number_forms(discriminant)
    assert base == 1
    value = Fraction(base * conductor)
    for prime in prime_factors(conductor):
        value *= Fraction(prime - kronecker_at_prime(discriminant, prime), prime)
    assert value.denominator == 1
    return value.numerator


def divisors(n):
    return [d for d in range(1, n + 1) if n % d == 0]


def sparse_rank(rows, modulus, columns):
    pivots = {}
    for row in rows:
        current = {int(k): int(v) % modulus for k, v in row.items() if int(v) % modulus}
        assert all(0 <= col < columns for col in current)
        while current:
            pivot = min(current)
            if pivot not in pivots:
                inverse = pow(current[pivot], -1, modulus)
                pivots[pivot] = {col: value * inverse % modulus for col, value in current.items()}
                break
            multiplier = current[pivot]
            for col, value in pivots[pivot].items():
                updated = (current.get(col, 0) - multiplier * value) % modulus
                if updated:
                    current[col] = updated
                else:
                    current.pop(col, None)
    return len(pivots)


def main():
    rows = []
    for name, path, expected_hash, reached_f in CASES:
        assert sha(path) == expected_hash, name
        data = json.loads(path.read_text())
        assert data["DK"] in (-7, -8)
        class_numbers = {}
        for conductor in divisors(reached_f):
            forms = class_number_forms(data["DK"] * conductor * conductor)
            formula = class_number_formula(data["DK"], conductor)
            assert forms == formula, (name, conductor, forms, formula)
            class_numbers[str(conductor)] = forms
        floor = class_numbers[str(reached_f)]
        predicted_class = 2 * sum(class_numbers.values())
        predicted_rank = predicted_class - 2 * floor
        predicted_deficiency = 2 * floor - 1
        predicted_al_deficiency = floor - 1
        assert data["class_size"] == predicted_class, name
        assert data["rank"] == predicted_rank, name
        assert data["deficiency"] == predicted_deficiency, name
        assert data["atkin_lehner"]["deficiency_with"] == predicted_al_deficiency, name
        if name == "D7_f210_restricted":
            assert data["f"] == 210 and data["hecke_primes"] == [2, 3, 5]
        else:
            assert data["f"] == reached_f
        row = {
            "case": name, "DK": data["DK"], "declared_f": data["f"],
            "reached_f": reached_f, "p": data["p"], "hecke_primes": data["hecke_primes"],
            "class_numbers": class_numbers, "floor_class_number": floor,
            "class_size": data["class_size"], "rank": data["rank"],
            "deficiency": data["deficiency"],
            "atkin_lehner_deficiency": data["atkin_lehner"]["deficiency_with"],
            "floor_fraction": Fraction(2 * floor, predicted_class).__str__(),
            "matrix_replayed": False, "source_sha256": expected_hash,
        }
        if name.endswith("_holdout"):
            assert len(data["column_points"]) == data["class_size"]
            assert len(data["relation_rows"]) == data["relations"]
            assert len(data["atkin_lehner_rows"]) == data["atkin_lehner"]["relations"]
            for modulus in (23, 1_000_000_007, 2_147_483_647):
                assert sparse_rank(data["relation_rows"], modulus, data["class_size"]) == predicted_rank
                assert sparse_rank(data["relation_rows"] + data["atkin_lehner_rows"], modulus,
                                   data["class_size"]) == data["atkin_lehner"]["rank_with"]
            row["matrix_replayed"] = True
            row["independent_rank_moduli"] = [23, 1_000_000_007, 2_147_483_647]
        rows.append(row)
    output = {"status": "verified", "cases": rows,
              "holdout_prediction_met": True,
              "retrospective_cases_matching": sum(not row["matrix_replayed"] for row in rows),
              "holdout_cases_replayed": sum(row["matrix_replayed"] for row in rows),
              "producer_launch_sha256": {"f42": sha(HERE / "launch42.json"),
                                         "f60": sha(HERE / "launch.json"),
                                         "f70": sha(HERE / "launch70.json"),
                                         "f90": sha(HERE / "launch90.json"),
                                         "f150": sha(HERE / "launch150.json"),
                                         "f210": sha(HERE / "launch210.json")}}
    (HERE / "validation.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": output["status"], "cases": len(rows),
                      "holdout_prediction_met": True}))


if __name__ == "__main__":
    main()
