# Composed split-root polynomials do not lower the measured certificate degree

Complete multiplicative cosets make the split root polynomial sparse.  If
\(H\subset\mathbb F_p^*\) has order \(f\), a union of \(H\)-cosets has

\[
 U_0(X)=P(X^f),
\]

and adjoining the fixed root zero gives \(U_0(X)=XP(X^f)\).  This is stronger
structure than an orbit segment or an arbitrary arithmetic progression.

The exact genus-two control over \(\mathbb F_{101}\) compares these composed
root sets with deterministic random split-fiber panels:

| Variables | Slots | Root form | Composed panels | Composed degree | Random panels | Random degree |
| ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 4 | 6 | \(P(X^2)\) | 32 | 4 | 32 | 4 |
| 5 | 7 | \(XP(X^2)\) | 32 | 4 | 32 | 4 |
| 6 | 8 | \(P(X^4)\) | 3 | 5 | 3 | 5 |
| 7 | 9 | \(XP(X^4)\) | 3 | 5 | 3 | 5 |

There are 13 all-split order-two cosets, giving 286 possible three-coset
sets; the fixture samples 32.  There are three all-split order-four cosets,
so the two-coset panels are a complete three-combination census.  Every
coefficient-support check verifies the claimed composed form.

The result is negative for ordinary static elimination: the sparse right-hand
side does not change the certificate degree.  The reason is visible in the
norm equation

\[
 wB^2-2vBC-uC^2=U_0.
\]

Although \(U_0\) is invariant under \(X\mapsto\zeta X\), the generic target
polynomials \(u,v,w\) and the curve are not.  Thus the equation does not split
into independent residue classes modulo \(f\), and sparsity on the right does
not supply a symmetry of the full inversion problem.

This finite experiment does not rule out a displacement or FFT-like solver
that uses the composed root polynomial without requiring the curve to share
the symmetry.  It does rule out the simplest prediction that sparse
\(U_0\) automatically creates an early Macaulay rank surplus.

[Implementation](composed_abscissa_search.py) ·
[Frozen result](composed_abscissa_search.json)

```sh
python3 composed_abscissa_search.py | cmp - composed_abscissa_search.json
```
