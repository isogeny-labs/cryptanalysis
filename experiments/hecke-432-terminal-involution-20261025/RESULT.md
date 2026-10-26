# The terminal degree-two involution negates the E projection

Let \(\iota\) be the nontrivial deck transformation of the
degree-two forgetful map \(X_0(432)\to X_0(216)\). For the normalized
level-432 projection \(g:X_0(432)\to E\),
\(E:y^2=x^3+432\), the exact characteristic-zero identity is
\[
g\circ\iota=-g.
\]
Consequently \(x_E\) factors through \(X_0(216)\), while
\(y_E\circ\iota=-y_E\). Combined with the complete p=997 geometric
fiber, this identifies the intermediate function field:
\[
\mathbf Q(X_0(216))=\mathbf Q(X_0(27))(x_E),\qquad
\mathbf Q(X_0(432))=\mathbf Q(X_0(216))(y_E),\quad
y_E^2=x_E^3+432.
\]
The first extension has degree 12 and the second degree 2. This
gives a structured route to the inverse map: reconstruct a relative
degree-12 x-coordinate resolvent, then use the sign of y to choose the
terminal edge.

## Complete finite-field pairing

The [frozen protocol](protocol.json) groups source records by exact
curve, indexed 27-chain, and the first three 2-isogeny kernel roots.
The [independent audit](audit.py) finds **900 groups of two** among all
1,800 p=997 rational source records. Each pair has different terminal
2-kernels, equal \(x_E\), and \(y_E\)-values summing to zero. In the
selected complete geometric fiber over \(C=(639,232)\), all 24
records form **12 such pairs** over \(\mathbf F_{997^4}\), again with
equal \(x_E\) and opposite \(y_E\). Every pair is retained in the
[audit receipt](audit.json), along with source hashes and zero mismatch
counts. The earlier geometric audit independently checks the E
equations and Frobenius equivariance.

The checked-Sage [subgroup receipt](subgroup_result.json) gives
\([\mathrm{SL}_2(\mathbf Z):\Gamma_0(27)]=36\), the corresponding
indices 432 at level 216 and 864 at level 432, and exact conductor
432 for both B and E. Thus the forgetful degrees are 12 and 2.
The matrix
\(\gamma=\left(\begin{smallmatrix}1&0\\216&1\end{smallmatrix}\right)\)
lies in \(\Gamma_0(216)\setminus\Gamma_0(432)\), and
\(\gamma^2=\left(\begin{smallmatrix}1&0\\432&1\end{smallmatrix}\right)\).
The two explicit matrix implications are checked by
`DeckArithmetic.gamma_square` and `gamma_exact_lower_level` in Lean.

## Characteristic-zero proof

The index-two subgroup \(\Gamma_0(432)\) is normal in
\(\Gamma_0(216)\), and \(\gamma\) represents its nontrivial coset.
It induces \(\iota\) on the modular curve, fixes the level-27
forgetful coordinate, and swaps the two terminal 2-isogeny choices
above a generic cyclic-8 subgroup.

Let \(f_B\) be the weight-two newform pulled back by the normalized
map to \(B:y^2=x^3-16\). Its exact level is 432, as checked by
the elliptic-curve conductor and the prior
[Sturm-certified map identity](../hecke-432-map-identity-20261025/RESULT.md).
The trace from level 432 to level 216 is \(f_B+f_B|_2\gamma\).
It belongs to the level-216 cusp-form space. Since trace is adjoint
to inclusion under the Petersson product and a newform is orthogonal
to the lower-level oldspace, this trace is zero. Hence
\(f_B|_2\gamma=-f_B\). The new/old orthogonality used here is
described in [Diamond and Im's modular-forms notes](https://wstein.org/msri06/stein/Diamond-Im-Modular_forms_and_modular_curves.pdf).

The invariant differential of \(g\circ\iota+g\) therefore vanishes.
In characteristic zero this sum is a constant E point. The normalized
map sends \(\infty\) to the identity; \(\gamma\infty=1/216\) is a
cusp, and the earlier [cusp torsion control](../hecke-432-cusp-image-20261025/RESULT.md)
and normalized map identity send it to the identity as well. The
constant is zero, proving \(g\circ\iota=-g\). Negation on E sends
\((x,y)\) to \((x,-y)\), giving the stated coordinate action.

At p=997, the complete geometric fiber of
\(X_0(216)\to X_0(27)\) consists of the 12 recorded three-edge
prefixes. Their \(x_E\) values are all distinct. The good-reduction
collision argument from the preceding
[generic-degree proof](../hecke-432-generic-degree-20261025/RESULT.md)
therefore makes \((C,x_E)\) generically injective on \(X_0(216)\).
It follows that \(x_E\) generates its degree-12 function field over
\(\mathbf Q(X_0(27))\). The anti-invariant \(y_E\) generates the
remaining quadratic extension and satisfies the displayed E equation.

| Result | Evidence and formalization |
| --- | --- |
| Deck representative and index-two arithmetic | Checked Sage subgroup receipt and `DeckArithmetic.gamma_square`, `gamma_exact_lower_level` in Lean. |
| 900 rational and 12 geometric sign pairs | Complete source-census replay in `audit.py`, bound to the prior independent finite-field audit. |
| Newform anti-invariance and normalized E-map negation | Written trace/oldspace and cusp-normalization proof above; modular-form and modular-curve definitions are not yet in the pinned Lean project. |
| Degree-12 intermediate field and quadratic sign extension | Written quotient and good-reduction proof using the 12 distinct specialized x values; full function-field formalization remains open in Lean. |

The Lean build and `#print axioms` output are in
[formal/build-output.txt](formal/build-output.txt), with pinned
toolchain and Mathlib revision in
[formal/DEPENDENCIES.json](formal/DEPENDENCIES.json). The checked
arithmetic lemmas use only standard foundations. Replay with

```sh
python3 experiments/hecke-432-terminal-involution-20261025/audit.py
./sage --runtime-info
./sage -python experiments/hecke-432-terminal-involution-20261025/check_sage.py
```

The next constructive experiment is to compute the relative
degree-12 polynomial of \(x_E\) over \(\mathbf Q(X_0(27))\) from
modular norms or trace data, then recover the desired B coordinate
in the resulting degree-24 y-basis. The specialized degree-12
polynomial from the [y-coordinate experiment](../hecke-432-y-primitive-20261025/RESULT.md)
is a finite-field checkpoint for that calculation.
