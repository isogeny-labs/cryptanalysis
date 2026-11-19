#!/usr/bin/env python3
"""Generate Lean curve-equation and local-point proofs for frozen paths."""

import argparse
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

import run


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "xedni-known-relation-lifts-20261118" / "run-result.json"
PROTOCOL = HERE / "protocol.json"
OUTPUT = HERE / "CurveEquationCertificates.lean"


def rat_term(value):
    return f"(({value.numerator} : ℚ) / ({value.denominator} : ℚ))"


def generate():
    source_bytes = SOURCE.read_bytes()
    source_hash = sha256(source_bytes).hexdigest()
    protocol = json.loads(PROTOCOL.read_text())
    assert source_hash == protocol["source_sha256"]
    source = json.loads(source_bytes)
    assert source["schema"] == "xedni-known-relation-lifts-result-v1"
    rows = [row for row in source["rows"] if row["status"] == "exact_relation"]
    assert len(rows) == 13
    primes = sorted({row["hit"]["p"] for row in rows})
    lines = [
        "import RationalCurveBridge",
        "import CoordinateCertificates",
        "import Mathlib.Tactic",
        "",
        "/-!",
        "Rational curve equations and prime-local curve points for every point on",
        "the thirteen recorded addition paths. Generated from source SHA-256",
        f"`{source_hash}` by `generate_curve_equation_certificates.py`.",
        "-/",
        "",
        "namespace XedniCurveEquationCertificates",
        "",
        "open XedniLocalZModReduction XedniRationalLocalWitness",
        "open XedniRationalCurveBridge XedniRegularChainReduction",
        "open XedniCoordinateCertificates",
        "",
    ]
    for p in primes:
        lines.append(f"local instance : Fact (Nat.Prime {p}) := ⟨by norm_num⟩")
    lines.append("")
    points = 0
    for row in rows:
        hit = row["hit"]
        p, a, b = hit["p"], hit["a"], hit["b"]
        A, B = row["model"]["A"], row["model"]["B"]
        T = tuple(Fraction(z) for z in row["model"]["T"])
        assert run.on_curve(T, A, B)
        assert run.reduce_point(T, p) == row["R"]
        P = T
        max_multiple = max(abs(a), abs(b))
        for multiple in range(1, max_multiple + 1):
            assert P is not None and run.on_curve(P, A, B)
            x, y = P
            assert x.denominator % p and y.denominator % p
            stem = f"row{row['hit_index']}_m{multiple}"
            local_type = f"localIntegers {p}"
            lines.extend([
                f"/-- Row {row['hit_index']}, rational curve equation for {multiple}T. -/",
                f"theorem {stem}_curve :",
                f"    {rat_term(y)} ^ 2 =",
                f"      {rat_term(x)} ^ 3 + ({A} : ℚ) * {rat_term(x)} + ({B} : ℚ) := by",
                "  norm_num",
                "",
                f"/-- Row {row['hit_index']}, prime-local curve point {multiple}T. -/",
                f"noncomputable def {stem}_localPoint :",
                f"    CurvePoint ({local_type})",
                f"      ((algebraMap ℤ ({local_type})) ({A}))",
                f"      ((algebraMap ℤ ({local_type})) ({B})) :=",
                f"  localCurvePoint {p} ({A}) ({B})",
                f"    {rat_term(x)} {rat_term(y)}",
                f"    {stem}_x {stem}_y {stem}_curve",
                "",
                f"#print axioms {stem}_curve",
                f"#print axioms {stem}_localPoint",
                "",
            ])
            points += 1
            if multiple < max_multiple:
                P, branch, _ = run.add_rat(P, T, A)
                assert branch in ("tangent", "chord")
    assert points == 67
    lines.extend(["end XedniCurveEquationCertificates", ""])
    return "\n".join(lines).encode(), source_hash, points, primes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data, source_hash, points, primes = generate()
    if args.check:
        assert OUTPUT.read_bytes() == data, "generated Lean file differs"
    else:
        OUTPUT.write_bytes(data)
    print(json.dumps({"check": args.check, "points": points, "primes": primes,
                      "source_sha256": source_hash}, sort_keys=True))


if __name__ == "__main__":
    main()
