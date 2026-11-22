#!/usr/bin/env python3
"""Export exact kernel input for Tian-style Magma reconstruction.

The generated file verifies the torsion bases and kernels. It intentionally
does not pretend to implement the unavailable normal-Weil-set reconstruction.
"""

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
d = json.loads((ROOT / "artifacts" / "evidence.json").read_text())


def z(value):
    return str(int(value, 16))


p224 = d["curves"]["P-224"]
p256 = d["curves"]["P-256"]

p224_x0 = z(p224["basis"]["P"]["x"]["a"][0])
p224_x1 = z(p224["basis"]["Q"]["x"]["a"][0])
p224_s = z(p224["basis"]["Q"]["y"]["b"][0])
p224_r = z(p224["torsion_field"]["r0"])

g = [z(x) for x in p256["torsion_field"]["g_low_to_high"]]
r = [z(x) for x in p256["torsion_field"]["r_low_to_high"]]

text = f'''// Generated from artifacts/evidence.json.
// This file certifies the exact kernels. It does not implement Tian's
// normal-Weil-set/theta reconstruction of the plane quartic.

procedure CheckKernel(E, P, Q, p, label, rows)
    O := E!0;
    Frob := func< R | R eq O select O else E![R[1]^p,R[2]^p,1] >;
    assert 3*P eq O and 3*Q eq O;
    assert Q ne P and Q ne -P;
    gens := [
        < rows[i][1]*P + rows[i][2]*Q,
          rows[i][3]*P + rows[i][4]*Q,
          rows[i][5]*P + rows[i][6]*Q > : i in [1..3]
    ];
    elts := {{
        < &+[ c[i]*gens[i][1] : i in [1..3] ],
          &+[ c[i]*gens[i][2] : i in [1..3] ],
          &+[ c[i]*gens[i][3] : i in [1..3] ] >
        where c := [aa,bb,cc] : aa,bb,cc in [0..2]
    }};
    assert #elts eq 27;
    assert #{{ T : T in elts | T[2] eq O and T[3] eq O }} eq 1;
    assert #{{ T : T in elts | T[1] eq O and T[3] eq O }} eq 1;
    assert #{{ T : T in elts | T[1] eq O and T[2] eq O }} eq 1;
    for G in gens do
        FG := < Frob(G[1]), Frob(G[2]), Frob(G[3]) >;
        assert FG in elts;
    end for;
    print label, "kernel checks passed; cardinality", #elts;
end procedure;

// NIST P-224: full E[3] is defined over F_(p^2).
p224 := {int(p224['parameters']['p'],16)};
Fp224 := GF(p224);
R224<x224> := PolynomialRing(Fp224);
K224<u224> := ext<Fp224 | x224^2 - Fp224!({p224_r})>;
E224 := EllipticCurve([K224!({int(p224['parameters']['a'],16)}), K224!({int(p224['parameters']['b'],16)})]);
P224 := E224![K224!({p224_x0}), u224, 1];
Q224 := E224![K224!({p224_x1}), K224!({p224_s})*u224, 1];
assert E224![P224[1]^p224,P224[2]^p224,1] eq -P224;
assert E224![Q224[1]^p224,Q224[2]^p224,1] eq -Q224;
rowsShared := [[1,0,0,1,0,1],[0,1,0,2,1,0],[0,0,1,1,2,2]];
rowsP224ZeroIncidence := [[1,0,0,0,0,1],[0,1,0,1,1,0],[0,0,1,1,0,1]];
CheckKernel(E224,P224,Q224,p224,"P-224 shared kernel",rowsShared);
CheckKernel(E224,P224,Q224,p224,"P-224 zero-diagonal-incidence alternate",rowsP224ZeroIncidence);

// NIST P-256: use F_(p^3)[u]/(u^2-r), an absolute degree-six field.
p256 := {int(p256['parameters']['p'],16)};
Fp256 := GF(p256);
R256<z0> := PolynomialRing(Fp256);
g256 := z0^3 + Fp256!({g[2]})*z0^2 + Fp256!({g[1]})*z0 + Fp256!({g[0]});
K3<z256> := ext<Fp256 | g256>;
S256<u0> := PolynomialRing(K3);
r256 := K3!({r[0]}) + K3!({r[1]})*z256 + K3!({r[2]})*z256^2;
K6<u256> := ext<K3 | u0^2-r256>;
E256 := EllipticCurve([K6!({int(p256['parameters']['a'],16)}), K6!({int(p256['parameters']['b'],16)})]);
P256 := E256![K6!z256,u256,1];
Q256 := E256![P256[1]^p256,P256[2]^p256,1];
assert E256![Q256[1]^p256,Q256[2]^p256,1] eq Q256-P256;
CheckKernel(E256,P256,Q256,p256,"P-256",rowsShared);

// Next required call (not implemented here):
//   C, pi := Tian333Quotient(E, [gens...]);
// Acceptance gates: nonsingular plane quartic over F_p, ker(pi)=Lambda,
// homomorphism checks, and polarized dual composition pi^dagger*pi=[3].
'''

out = ROOT / "handoff" / "nist_333_kernel_input.m"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(text)
print(out)
