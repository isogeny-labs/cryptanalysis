#!/usr/bin/env python3
"""Export the reconstructed P-224 quartic to Magma's quartic package."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
theta = json.loads((ROOT / "artifacts" / "p224_finite_field_theta.json").read_text())
evidence = json.loads((ROOT / "artifacts" / "evidence.json").read_text())
curve = evidence["curves"]["P-224"]


def integer(value):
    return int(value, 16)


def base_coefficient(value):
    # A P-224 FFE has one coefficient; QE is a+b*u.
    a = integer(value["a"][0])
    b = integer(value["b"][0])
    return f"(K2!({a}) + K2!({b})*u)"


def cubic_coefficient(value):
    terms = [base_coefficient(coefficient) for coefficient in value]
    return f"({terms[0]} + ({terms[1]})*w + ({terms[2]})*w^2)"


def monomial(exponents):
    variables = ["x", "y", "z"]
    factors = []
    for variable, exponent in zip(variables, exponents):
        if exponent == 1:
            factors.append(variable)
        elif exponent > 1:
            factors.append(f"{variable}^{exponent}")
    return "*".join(factors) or "1"


terms = [
    f"({cubic_coefficient(row['coefficient'])})*{monomial(row['exponents_xyz'])}"
    for row in theta["quartic"]
]
quartic_expression = " +\n    ".join(terms)

p = integer(curve["parameters"]["p"])
a = integer(curve["parameters"]["a"])
b = integer(curve["parameters"]["b"])
r0 = integer(curve["torsion_field"]["r0"])

text = f'''// Generated from artifacts/p224_finite_field_theta.json.
// The Python stage has already certified the 28/36 theta-null pattern,
// Riemann-system consistency, and seven Aronhold bitangents.
// This script performs the remaining invariant/descent checks in the
// maintained JRSijsling/quartic package (bundled with Magma >= 2.26).

// For older Magma versions, uncomment and adjust this path:
// AttachSpec("/workspace/scratch/quartic/magma/spec");

p := {p};
Fp := GF(p);
R2<t2> := PolynomialRing(Fp);
K2<u> := ext<Fp | t2^2 - Fp!({r0})>;
R6<t6> := PolynomialRing(K2);
K6<w> := ext<K2 | t6^3 + K2!({a})*t6 + K2!({b})>;
P3<x,y,z> := PolynomialRing(K6,3);
F :=
    {quartic_expression};

C := Curve(ProjectiveSpace(K6,2), F);
assert IsNonsingular(C);
DO, weights := DixmierOhnoInvariants(F);
DOn := WPSNormalize(weights, DO);
DOp := WPSNormalize(weights, [ c^p : c in DO ]);
moduli_rational := DixmierOhnoInvariantsEqual(DO, [ c^p : c in DO ]);
print "P-224 extension quartic is nonsingular";
print "Dixmier-Ohno moduli point Frobenius-rational:", moduli_rational;
print "WPSNormalize representatives equal:", DOn eq DOp;
print "Normalized invariants individually F_p-rational:", [ c^p eq c : c in DOn ];

if moduli_rational and &and[ c^p eq c : c in DOn ] then
    // The corrected candidate is already defined over the cubic subfield of
    // K6.  Descend it directly with its unique Frobenius isomorphism.  This
    // avoids the much heavier invariant-to-quartic reconstruction.
    assert &and[ c^(p^3) eq c : c in Coefficients(F) ];
    mons := MonomialsOfDegree(P3, 4);
    Fsigma := &+[ (MonomialCoefficient(F, monomial)^p)*monomial : monomial in mons ];
    isomorphic, isomorphisms := IsIsomorphicTernaryQuartics(F, Fsigma);
    assert isomorphic and #isomorphisms eq 1;
    M := isomorphisms[1];
    Msigma := Matrix(K6, 3, 3, [ c^p : c in Eltseq(M) ]);
    Msigma2 := Matrix(K6, 3, 3, [ c^(p^2) : c in Eltseq(M) ]);
    assert Msigma2*Msigma*M eq IdentityMatrix(K6, 3);

    // Matrix Hilbert 90: B^sigma*M=B.  The deterministic trace choice is
    // invertible for this candidate.
    B := IdentityMatrix(K6, 3) + M + Msigma*M;
    assert Determinant(B) ne 0;
    Bsigma := Matrix(K6, 3, 3, [ c^p : c in Eltseq(B) ]);
    assert Bsigma*M eq B;
    A := B^-1;
    variables := [x, y, z];
    substitutions := [
        &+[ A[i,j]*variables[j] : j in [1..3] ]
        : i in [1..3]
    ];
    descended := Evaluate(F, substitutions);
    descended_coefficients := [ MonomialCoefficient(descended, monomial) : monomial in mons ];
    first_nonzero := Min([ i : i in [1..#descended_coefficients] | descended_coefficients[i] ne 0 ]);
    descended /:= descended_coefficients[first_nonzero];
    assert &and[ c^p eq c : c in Coefficients(descended) ];
    Pfp<X,Y,Z> := PolynomialRing(Fp, 3);
    CFp := Pfp!descended;
    assert IsNonsingular(Curve(ProjectiveSpace(Fp,2), CFp));
    DOCheck, checkWeights := DixmierOhnoInvariants(CFp);
    assert DixmierOhnoInvariantsEqual([ K6!c : c in DOCheck ], DO);
    print "FROBENIUS_ISOMORPHISM_UNIQUE", true;
    print "HILBERT_90_COCYCLE_VALID", true;
    print "DESCENDED_QUARTIC", CFp;
else
    print "MODULI_VALIDATION_FAILED_OR_REPRESENTATIVE_NOT_RATIONAL";
end if;
'''

output = ROOT / "handoff" / "p224_quartic_descent.m"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(text)
print(output)
