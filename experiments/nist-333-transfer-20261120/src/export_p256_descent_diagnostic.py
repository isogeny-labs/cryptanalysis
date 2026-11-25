#!/usr/bin/env python3
"""Export a Magma diagnostic for Frobenius descent of the P-256 quartic."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("nist_333", ROOT / "src" / "nist_333.py")
nist = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["nist_333"] = nist
SPEC.loader.exec_module(nist)

theta = json.loads((ROOT / "artifacts" / "p256_finite_field_theta.json").read_text())
bundle = nist.build_p256()
curve = nist.CURVES["P-256"]


def ffe(value):
    coefficients = [int(item, 16) for item in value]
    return f"(K3!({coefficients[0]}) + K3!({coefficients[1]})*z + K3!({coefficients[2]})*z^2)"


def qe(value):
    return f"(K6!({ffe(value['a'])}) + K6!({ffe(value['b'])})*u)"


def monomial(exponents):
    variables = ["x", "y", "zz"]
    factors = []
    for variable, exponent in zip(variables, exponents):
        if exponent == 1:
            factors.append(variable)
        elif exponent > 1:
            factors.append(f"{variable}^{exponent}")
    return "*".join(factors) or "1"


terms = [
    f"({qe(row['coefficient'])})*{monomial(row['exponents_xyz'])}"
    for row in theta["quartic"]
]
quartic_expression = " +\n    ".join(terms)
p = curve["p"]
g = [int(value, 16) for value in bundle["torsion_field"]["g_low_to_high"]]
r = [int(value, 16) for value in bundle["torsion_field"]["r_low_to_high"]]

text = f'''// Generated from artifacts/p256_finite_field_theta.json.
// This diagnostic tests the moduli, Frobenius isomorphisms, and cocycle
// products before any claim that the candidate descends to F_p.

p := {p};
Fp := GF(p);
R3<t3> := PolynomialRing(Fp);
K3<z> := ext<Fp | t3^3 + Fp!({g[2]})*t3^2 + Fp!({g[1]})*t3 + Fp!({g[0]})>;
R6<t6> := PolynomialRing(K3);
r := K3!({r[0]}) + K3!({r[1]})*z + K3!({r[2]})*z^2;
K6<u> := ext<K3 | t6^2 - r>;
P3<x,y,zz> := PolynomialRing(K6,3);
F :=
    {quartic_expression};

C := Curve(ProjectiveSpace(K6,2), F);
assert IsNonsingular(C);
DO, weights := DixmierOhnoInvariants(F);
DOn := WPSNormalize(weights, DO);
DOp := WPSNormalize(weights, [ coefficient^p : coefficient in DO ]);
moduli_rational := DixmierOhnoInvariantsEqual(DO, [ coefficient^p : coefficient in DO ]);
print "P256_NONSINGULAR", true;
print "P256_MODULI_FROBENIUS_RATIONAL", moduli_rational;
print "P256_NORMALIZED_INVARIANTS_FROBENIUS_FIXED", [ coefficient^p eq coefficient : coefficient in DOn ];

mons := MonomialsOfDegree(P3, 4);
Fsigma := &+[ (MonomialCoefficient(F, monomial)^p)*monomial : monomial in mons ];
isomorphic, isomorphisms := IsIsomorphicTernaryQuartics(F, Fsigma);
print "P256_FROBENIUS_ISOMORPHIC", isomorphic;
print "P256_FROBENIUS_ISOMORPHISM_COUNT", #isomorphisms;
if isomorphic then
    I := IdentityMatrix(K6, 3);
    for index in [1..#isomorphisms] do
        M := isomorphisms[index];
        T := I;
        product := I;
        // The reconstructed coefficients lie in K3 (their u-components are
        // all zero), so the relevant descent cocycle has order three.
        for power in [0..2] do
            if power eq 0 then
                conjugate := M;
            else
                conjugate := Matrix(K6, 3, 3, [ coefficient^(p^power) : coefficient in Eltseq(M) ]);
            end if;
            product := conjugate*product;
        end for;
        scalar_cocycle := &and[ product[row,col] eq (row eq col select product[1,1] else 0) : row,col in [1..3] ];
        print "P256_ISOMORPHISM", index, "COCYCLE_SCALAR", scalar_cocycle, "COCYCLE_SCALAR_VALUE", product[1,1];
    end for;
end if;
'''

output = ROOT / "handoff" / "p256_descent_diagnostic.m"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(text)
print(output)
