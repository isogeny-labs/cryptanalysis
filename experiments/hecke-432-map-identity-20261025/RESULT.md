# Sturm-certified quarter-shift map identity at level 432

The quarter-shift construction on \(X_0(432)\), followed by the twist to
\(E:y^2=x^3+432\), equals the normalized modular parametrization to
\(B:y^2=x^3-16\) followed by its rational degree-three isogeny
\(\widehat\pi:B\to E\). Its invariant-differential q-series agree through
\(q^{207}\), beyond the exact weight-two level-432 Sturm bound **144**;
both maps send the infinity cusp to the identity. The map difference is
therefore constant and zero. The [LMFDB record for 432a1](https://www.lmfdb.org/EllipticCurve/Q/432a1/)
independently records modular degree **24**, matching the 24 distinct
rational source points in each of the 36 previously measured noncuspidal
fibers.

For \(C=X_0(27):y^2+y=x^3-7\), let \(P_\pm(\tau)\) be its normalized
modular-parametrization points at \(\tau\pm1/4\), and put
\(D=P_+-P_-\). The [quarter-shift moduli construction](../hecke-432-moduli-shift-evaluator-20261025/RESULT.md)
gives these as genuine maps from level 432. With \(i^2=-1\), the algebraic
twist sends \(D=(x,y)\) to
\[
H=(-4x,-8i(y+1/2))\in E.
\]
`compare_qseries_sage.py` evaluates the two C-coordinate Laurent series
at \(iq\) and \(-iq\), performs the C group subtraction, and constructs
\(H\). It independently computes the normalized B q-map, then applies
\[
\widehat\pi(X,Y)=\left(\frac{X^3-64}{X^2},
              \frac{Y(X^3+128)}{X^3}\right).
\]
The script verifies this isogeny formula as a rational identity using
\(Y^2=X^3-16\). The x-series agree through exponent 204 and the y-series
through exponent 203 at the requested precision 210. The pullbacks of
\(dx/(2y)\), expressed as \(q x'(q)/(2y(q))\), agree through exponent
**207**. Sage computes \([\mathrm{SL}_2(\mathbf Z):\Gamma_0(432)]=864\)
and `Gamma0(432).sturm_bound(2)=144`. The [Sturm theorem](https://perso.ens-lyon.fr/francois.brunault/recherche/Sturm-bound-general.pdf)
then proves equality of the two weight-two pullback forms. A morphism from
a connected complete curve to an elliptic curve with zero pullback
differential is constant in characteristic zero; both x/y series have pole
orders 2/3 at infinity, so that constant is the identity.

The finite-field [kernel-chain evaluator](../hecke-432-kernel-transport-20261025/RESULT.md)
constructs the reduction of this map at \(p=883\). An analytic sign change
in the quarter-shift convention can negate the B output uniformly; it
preserves every image and cusp count. Over \(\mathbf F_{883}\), the
degree-three isogeny on B points is bijective: both B and E have 931 points
and a direct enumeration gives 931 distinct images and one preimage of the
identity. Thus the E image determines each B output uniquely.

The [cusp-field control](../hecke-432-cusp-image-20261025/RESULT.md)
places all 24 rational cusps over \(\mathbf Q(\sqrt{-3})\), where B has
trivial torsion. By Manin–Drinfeld, each normalized cusp image is the
identity. The identity is absent from the 36-point noncuspidal image, so
the **entire rational image has 37 points** and **894 of the 931 B points**
have no \(\mathbf F_{883}\)-rational level-432 preimage. The 36
noncuspidal image fibers contain 24 distinct rational points apiece,
consistent with the independently tabulated modular degree 24.

| Claim | Evidence and formalization |
| --- | --- |
| Quarter-shift differential equals that of \(\widehat\pi\circ\phi_B\) | Exact Laurent-series arithmetic through \(q^{207}\), verified Sturm bound 144, and the written modular-morphism argument above. Lean modular-curve and Sturm formalization remains open. |
| Both maps send infinity to the identity | x/y Laurent pole orders 2/3 and the explicit normalized modular q-map. |
| B-image count 37 and gap 894 | 864-row source census, 36-image audit, 24-cusp field/torsion control, and the checked finite-set implication `MapImageGap.exactly_894_missing`. |

The exact source and target series, agreement bounds, Sage runtime receipt,
Lean axiom audit, and checksum seal are retained here. The Lean theorem
formalizes the final finite-set implication conditional on the enumerated
image size; a faithful Lean definition of the modular morphism and its
Sturm-bound proof remains an explicit open formalization bridge.

Replay from the repository root with
`./sage -python experiments/hecke-432-map-identity-20261025/compare_qseries_sage.py`.
The checked launcher verifies the accepted Sage build. The equality is an
exact characteristic-zero certificate; no IC candidate or wall-time
comparison is assigned to it.
