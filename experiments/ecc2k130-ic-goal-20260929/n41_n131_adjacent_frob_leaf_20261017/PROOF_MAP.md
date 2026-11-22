# Proof map

## Adjacent Frobenius x-coordinate

Let (E/ℚ_{2^n}) have equation (y^2+xy=x^3+1), let
τ(x,y)=(x^2,y^2), and assume (x\notin\{0,1\}). Put
(d=x+x^2\ne0), (q=y+y^2), and (s=q/d). The usual binary-curve
addition law gives (x(P+τ P)=s^2+s+x+x^2). Clearing denominators
from (x(P+τ P)=x+1/x) gives

\[
  xq^2+xqd+x^3d^2+d^2=0.
\]

For (C=y^2+xy+x^3+1) and
(Q=xy^2+x^2y+x^4+x^2), exact integer-polynomial expansion gives

\[
 xq^2+xqd+x^3d^2+d^2
 = CQ+2(x^6-x^5y-x^4y^2+x^3-x^2y^3+xy^3).
\]

Thus the cleared equation holds on (E) in characteristic two. Since
(-τ P) has the same x-coordinate as τ P, (P-τ P) has the
other binary-curve output x-coordinate. Writing (f(z)=z+1/z), the
binary addition law yields (x(P-τ P)=f(f(x))). For reciprocal
(a=1/x), the plus and minus reciprocals are exactly
(b=a/(1+a^2)) and (c=b/(1+b^2)). Here (d\ne0) and (f(x)\ne0),
so both denominators are invertible. The excluded x values and point
at infinity are handled as exceptions rather than fed to this map.

## Lean declarations and bridge

| Result | Declaration | Exact scope | Status |
| --- | --- | --- | --- |
| Cleared polynomial identity | `Adjacent.adjacent_polynomial_identity` | All integer x,y; exact quotient and twice-remainder | Built |
| Characteristic-two parity consequence | `Adjacent.adjacent_parity` | All integer x,y,h with `curvePoly x y = 2*h` | Built |
| Map on actual extension-field curve points | No declaration yet | Arbitrary GF(2^n), nonexceptional P, group-law bridge | Partial formalization; 140 N41 signed states and 512 N131 sampled point-sign cases checked in Sage |

Lean 4.34.1 (commit `5045d0056413266e57c625dcd7c365b10e377c52`)
built `Adjacent.lean` with `lean Adjacent.lean`; `lean.stdout` retains
`#print axioms` output. Each theorem uses only `propext`,
`Classical.choice`, and `Quot.sound`. No `lean4checker` executable was
available. A complete formal bridge needs a characteristic-two field,
the binary Weierstrass group law, and the map from integer-polynomial
identities to that field. The Sage replay checks this bridge for the
recorded instances, while the mathematical proof above covers all
nonexceptional curve points.
