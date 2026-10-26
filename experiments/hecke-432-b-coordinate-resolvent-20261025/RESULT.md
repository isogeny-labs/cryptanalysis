# An explicit rational branch from the paired level-27 and level-432 coordinates

The [branch formula](branch_formula.json) gives the optimal
\(B=432a1:y_B^2=x_B^3-16\) coordinate as

\[
x_B=\frac{N(x_C,y_C,x_E)}{D(x_C,y_C,x_E)},
\qquad
y_B=\frac{y_E x_B^3}{x_B^3+128},
\]

on the generic image of \(X_0(432)\to X_0(27)\times E\), where
\(C=X_0(27):y_C^2+y_C=x_C^3-7\) and
\(E:y_E^2=x_E^3+432\). The numerator has 167 terms and the
denominator 180 terms, with integer coefficients and \(y_C\)-degree
at most one. The [degree-12 polynomial](relative_b_resolvent.json)
for \(x_B\) has just 89 nonzero terms and weighted degree 44.
These equations construct the rational branch of the degree-three
\(B\to E\) isogeny selected by the level-27 coordinate.

## Exact degree-12 equation

The [frozen screen](protocol.json) used monomials
\(x_C^a y_C^b x_B^c\), \(b\in\{0,1\}\), \(c\leq12\), and
\(2a+3b+2c\leq D\). Both \(\mathbf F_{997}\) and
\(\mathbf F_{1009}\) had full column rank at \(D=24\) (157 columns)
and \(D=40\) (364 columns). At \(D=56\), both had 572 columns,
rank 560, and nullity 12. Restricting those kernels by weight gave
dimension zero through 43 and dimension one at weight 44, in both
fields. The [screen receipt](screen_result.json) and
[minimal extraction](minimal_result.json) retain the matrices'
monomial orders, ranks, kernels, and status for every frozen cell.

The [fresh-prime lift](lift_result.json) found the same restricted
relation in 18 further primes, with training coefficients
\(q^{-44}\) through \(q^{900}\) and held-out coefficients through
\(q^{1000}\). The first 19 primes reconstructed every rational
coefficient; prime 1117 matched all 416 basis coordinates without
entering the reconstruction. The least common denominator is 972;
the resulting integer polynomial \(P_B(x_C,y_C,T)\) has coefficient
gcd one.

The [exact verification](exact_verification.json) checks every
characteristic-zero coefficient of
\(P_B(x_C(q),y_C(q),x_B(q))\) from \(q^{-44}\) through
\(q^{1056}\); all vanish. The source precision is 1250 and the
minimum input-power precision is 1206. The level-27 forgetful map
and optimal level-432 modular map each have degree 24, giving
coordinate degrees 48 for \(x_C\), 72 for \(y_C\), and 48 for
\(x_B\) on \(X_0(432)\). Thus every weight-44 monomial has pole
divisor degree at most \(48a+72b+48c\leq1056\). A nonzero rational
function cannot have a zero of order at least 1057 at infinity while
its entire pole divisor has degree at most 1056. This proves the
identity \(P_B(x_C,y_C,x_B)=0\) in characteristic zero.

The preceding [\(x_E\) resolvent](../hecke-432-relative-resolvent-20261025/RESULT.md)
proves \([\mathbf Q(C)(x_E):\mathbf Q(C)]=12\). Since
\(x_E=(x_B^3-64)/x_B^2\) and \(P_B\) has degree 12 in \(x_B\),
the two degree bounds meet:
\[
\mathbf Q(C)(x_B)=\mathbf Q(C)(x_E),\qquad
[\mathbf Q(C)(x_B):\mathbf Q(C)]=12.
\]
The specialized leading coefficient and complete fiber below also
verify that \(P_B\) retains degree 12 at the selected good-reduction
point.

## Constructing the rational branch

Set \(F(T)=T^3-x_E T^2-64\), the numerator of the exact isogeny
relation, and divide \(P_B(T)\) by this monic cubic. Write its
remainder as \(R(T)=aT^2+bT+c\), with
\(a,b,c\in\mathbf Z[x_C,y_C,x_E]\). Direct polynomial arithmetic
gives
\[
D=b(a x_E+b)-ac,\qquad
N=64a^2-c(a x_E+b),
\]
and the exact Bézout identity
\[
DT-N=a\bigl(aF-TR\bigr)+(a x_E+b)R.
\]
`derive_branch_sage.py` checks this identity over the integer
polynomial ring, then reduces \(y_C^2\) using the C equation and
exports the canonical numerator and denominator. At the normalized
modular point, \(F(x_B)=P_B(x_B)=R(x_B)=0\), so \(D x_B=N\).
The [complete-fiber branch audit](branch_fiber_verification.json)
finds \(D\ne0\) at all 24 geometric points over the selected
\(C=(639,232)\) fiber. Hence \(D\) is a nonzero function, and the
displayed quotient is an equality of rational functions. The same
fiber makes \(x_B^3+128\ne0\), giving the generic \(y_B\) formula.

The [fiber reconstruction](fiber_verification.json) independently
specializes \(P_B\) at \(C=(639,232)\) over \(\mathbf F_{997}\).
Its resultant with \(T^3-XT^2-64\) is a nonzero scalar times the
earlier \(x_E\) resolvent. For each of the 12 distinct geometric
\(x_E\) values, the specialized gcd is linear and selects one
\(x_B\). The two signs of \(y_E\) recover the corresponding two
\(B\) points; all 24 satisfy the B equation and replay through the
isogeny. Evaluating the exported \(N/D\) returns every selected
\(x_B\).

The independently frozen [rational-census audit](census_protocol.json)
replayed the formula against all **1,800** \(\mathbf F_{997}\)
source records from the earlier paired-map census. Every denominator
was defined, every recovered point lay on B, and each matched one of
the independently enumerated degree-three isogeny preimages. The
[receipt](census_verification.json) preserves the zero-failure count
and the selected-preimage index histogram \((672,432,696)\).

| Result | Formalization status |
| --- | --- |
| Weight-44 pole bound | Pinned Lean theorem `BPoleBound.monomial_pole_bound`, with `#print axioms`. |
| Generic cubic elimination and branch implication | Pinned Lean theorems `BranchElimination.elimination_identity` and `branch_equation`, with no claim-specific axiom. |
| Concrete 89-term identity and 347-term rational formula | Exact Sage polynomial and \(\mathbf Q\)-series checks plus independent finite-field audits. Encoding the concrete coefficients in Lean remains open. |
| Modular-curve pole divisor and function-field equality | Written proof above; the corresponding modular-curve and divisor definitions are not yet in the pinned Lean project. |

The Lean [dependency pin and build receipts](formal/) record the
toolchain, Mathlib revision, commands, outputs, and axiom audits;
`lean4checker --fresh` is unavailable on this host. The checked Sage
[runtime receipt](sage-runtime-info.txt) records the accepted local
build. The checksum [seal](SEAL.sha256) covers this experiment.

Replay from the repository root with the checked Sage launcher:

```sh
./sage --runtime-info
./sage -python experiments/hecke-432-b-coordinate-resolvent-20261025/screen_sage.py
./sage -python experiments/hecke-432-b-coordinate-resolvent-20261025/extract_minimal_sage.py
./sage -python experiments/hecke-432-b-coordinate-resolvent-20261025/lift_sage.py 1013 1019 1021 1031 1033 1039 1049 1051 1061 1063 1069 1087 1091 1093 1097 1103 1109 1117
./sage -python experiments/hecke-432-b-coordinate-resolvent-20261025/reconstruct_sage.py
./sage -python experiments/hecke-432-b-coordinate-resolvent-20261025/verify_exact_sage.py
./sage -python experiments/hecke-432-b-coordinate-resolvent-20261025/verify_fiber_sage.py
python3 experiments/hecke-432-b-coordinate-resolvent-20261025/export_resolvent.py
./sage -python experiments/hecke-432-b-coordinate-resolvent-20261025/derive_branch_sage.py
./sage -python experiments/hecke-432-b-coordinate-resolvent-20261025/verify_branch_fiber_sage.py
python3 experiments/hecke-432-b-coordinate-resolvent-20261025/audit_census.py
```

The next constructive step is to apply this B-coordinate branch to
independently selected \((C,E)\) inputs and recover or reject their
underlying level-432 kernel-chain records using the moduli evaluator.
