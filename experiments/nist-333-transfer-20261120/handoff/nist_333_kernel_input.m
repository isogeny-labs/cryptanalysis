// Generated from artifacts/evidence.json.
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
    elts := {
        < &+[ c[i]*gens[i][1] : i in [1..3] ],
          &+[ c[i]*gens[i][2] : i in [1..3] ],
          &+[ c[i]*gens[i][3] : i in [1..3] ] >
        where c := [aa,bb,cc] : aa,bb,cc in [0..2]
    };
    assert #elts eq 27;
    assert #{ T : T in elts | T[2] eq O and T[3] eq O } eq 1;
    assert #{ T : T in elts | T[1] eq O and T[3] eq O } eq 1;
    assert #{ T : T in elts | T[1] eq O and T[2] eq O } eq 1;
    for G in gens do
        FG := < Frob(G[1]), Frob(G[2]), Frob(G[3]) >;
        assert FG in elts;
    end for;
    print label, "kernel checks passed; cardinality", #elts;
end procedure;

// NIST P-224: full E[3] is defined over F_(p^2).
p224 := 26959946667150639794667015087019630673557916260026308143510066298881;
Fp224 := GF(p224);
R224<x224> := PolynomialRing(Fp224);
K224<u224> := ext<Fp224 | x224^2 - Fp224!(23262824917328850619534927041737880296449585999787473673423898970443)>;
E224 := EllipticCurve([K224!(26959946667150639794667015087019630673557916260026308143510066298878), K224!(18958286285566608000408668544493926415504680968679321075787234672564)]);
P224 := E224![K224!(1758687569991944859802895851707374763474393614424456162194549815776), u224, 1];
Q224 := E224![K224!(2516625373531097568017099632483268812866273582284876867818364892596), K224!(6969612036372497466310154386515536115724700258833715421213679970229)*u224, 1];
assert E224![P224[1]^p224,P224[2]^p224,1] eq -P224;
assert E224![Q224[1]^p224,Q224[2]^p224,1] eq -Q224;
rowsShared := [[1,0,0,1,0,1],[0,1,0,2,1,0],[0,0,1,1,2,2]];
rowsP224ZeroIncidence := [[1,0,0,0,0,1],[0,1,0,1,1,0],[0,0,1,1,0,1]];
CheckKernel(E224,P224,Q224,p224,"P-224 shared kernel",rowsShared);
CheckKernel(E224,P224,Q224,p224,"P-224 zero-diagonal-incidence alternate",rowsP224ZeroIncidence);

// NIST P-256: use F_(p^3)[u]/(u^2-r), an absolute degree-six field.
p256 := 115792089210356248762697446949407573530086143415290314195533631308867097853951;
Fp256 := GF(p256);
R256<z0> := PolynomialRing(Fp256);
g256 := z0^3 + Fp256!(108494815539227526261591756460669585469668810667962802221946703900438636945563)*z0^2 + Fp256!(74867602368915039844168376876958405755946998779831779147091645395356062379288)*z0 + Fp256!(98981205002779180685735253426272285913324849967138220070825936345958777801850);
K3<z256> := ext<Fp256 | g256>;
S256<u0> := PolynomialRing(K3);
r256 := K3!(57869247932729210206288323303182556025875734464145819679542951276947787453392) + K3!(40924486841441208918529070072449167774139144635458535048441985913511035474660)*z256 + K3!(7297273671128722501105690488737988060417332747327511973586927408428460908388)*z256^2;
K6<u256> := ext<K3 | u0^2-r256>;
E256 := EllipticCurve([K6!(115792089210356248762697446949407573530086143415290314195533631308867097853948), K6!(41058363725152142129326129780047268409114441015993725554835256314039467401291)]);
P256 := E256![K6!z256,u256,1];
Q256 := E256![P256[1]^p256,P256[2]^p256,1];
assert E256![Q256[1]^p256,Q256[2]^p256,1] eq Q256-P256;
CheckKernel(E256,P256,Q256,p256,"P-256",rowsShared);

// Next required call (not implemented here):
//   C, pi := Tian333Quotient(E, [gens...]);
// Acceptance gates: nonsingular plane quartic over F_p, ker(pi)=Lambda,
// homomorphism checks, and polarized dual composition pi^dagger*pi=[3].
