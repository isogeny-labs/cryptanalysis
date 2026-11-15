# Actual q223 two-primary structure and the geometric splitting field

2026-11-13. Standing unsigned; formalization partial. Native510d03,
prospective formal plan573f88. [pcc:unverified]

The fixed source is E over K=F223[z]/(z³−3), ell=2773073,
#E(K)=11092292=4ell. Its three Frobenius-conjugate elliptic quotients are
the actual Ciani quartic's quotients described in V2_MAPS_01.md. With the
stated origin corrections, their pullback sum Phi and norm Norm have both
compositions [2]. They therefore give an F223-isogeny between Res(K/F223)E
and J=Jac(C). This written geometric bridge gives #J(F223)=#E(K)=4ell.
Native annihilator checks alone would not prove this order.
[pcc:unverified]

Native02 uses the original prime-field Picard arithmetic to project all224
actual rational C point classes by ell, adjoining the actual Phi(E(K)[2])
images. It closes this pool and finds four distinct classes, with exact
orders1,2,4,4, all16 sums and64 associative triples checked. The written
order bound makes this four-element subgroup the entire rational2-Sylow,
which is C4. The original independent elliptic engine instead gives all
three distinct roots of the source short Weierstrass cubic in K, so E(K)[2]
is C2×C2. The observed map tables have rational kernel size2 and image size2
in each direction and obey both [2] compositions. The odd-order generator
remains nonzero of exact prime orderell after Phi. [pcc:unverified]

Let F be q-Frobenius on the geometric2-torsion V=J[2](algebraic closure).
Because223 is odd and dim J=3, V has dimension6 over F2 and64 elements.
The Weil-restriction polynomial is

    P(T)=T^6−t*T^3+q^3=T^6+2724*T^3+11089567,
    t=q^3+1−11092292=−2724.

An isogeny preserves this Weil polynomial even though its degree is a power
of2. The same polynomial is the characteristic polynomial on the integral
2-adic Tate module; reducing it modulo2 gives the characteristic polynomial
T^6+1 on the actual V. This does not identify V with the elliptic quotient
two-torsion through a degree-even isogeny. Cayley-Hamilton now gives F^6=1.
[pcc:unverified]

The rational C4 group has exactly two elements killed by2. Thus F fixes
exactly2 of V's64 elements. If F^3=1, every remaining orbit has length3,
requiring64=2+3c for a nonnegative integerc. This is impossible. If F^2=1,
its minimal polynomial divides(T+1)^2 in characteristic2; all its geometric
eigenvalues are1, so its degree6 characteristic polynomial would have to be
(T+1)^6=T^6+T^4+T^2+1, different from T^6+1. The order of F divides6 and
divides neither2 nor3, hence equals6. Consequently all geometric J[2] points
are defined over F223^6, and this is the minimal extension containing them
all. They are not all defined over the original cubic fieldK. This is a
written derivation using the native rational-group observation and standard
geometric/Tate-module results, not a full Lean formalization.
[pcc:unverified]

The four named declarations in FrobeniusSix.lean formalize exact trace and
parity, the integer orbit obstruction, the faithful implication from the
actual annihilating polynomial on an arbitrary exponent-two module to the
sixth iterate identity, and the final divisor-of-six implication. They do
not define J, prove its Weil polynomial, supply Cayley-Hamilton or the orbit
decomposition, or establish the actual characteristic-polynomial and
splitting-field bridges. These full obligations remain open.
[pcc:unverified]

This finding rules out assuming that every geometric2-torsion point needed
by a further kernel construction is already K-rational. It does not rule
out F223-rational isogenies: a kernel can be Frobenius-stable without having
all its points individually rational. No actual geometric torsion basis,
Frobenius matrix, stable maximal-isotropic kernel census, second nondual
map, target-curve equation or computational advantage has been constructed.
In particular P modulo2 does not justify semisimple order-three Frobenius.
[pcc:unverified]
