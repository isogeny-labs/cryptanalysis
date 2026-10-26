# An exact degree-12 resolvent for the level-432 x-coordinate

The [integer polynomial](relative_resolvent.json)
\(H(x_C,y_C,X)\in\mathbf Z[x_C,y_C,X]\) has 278 nonzero terms,
weighted degree 90, and degree 12 in \(X\). On
\(C=X_0(27):y_C^2+y_C=x_C^3-7\), it satisfies the exact identity

\[
H(x_C,y_C,x_E)=0,
\qquad E:y_E^2=x_E^3+432,
\]

for the normalized level-432 map to \(E\). Together with the
[terminal involution and degree proof](../hecke-432-terminal-involution-20261025/RESULT.md),
this makes \(H\), up to its leading coefficient in \(\mathbf Q(C)\),
the minimal polynomial of \(x_E\) over \(\mathbf Q(C)\). It is an
explicit equation for the degree-12 intermediate field
\(\mathbf Q(X_0(216))=\mathbf Q(C)(x_E)\). The remaining degree-two
step is \(y_E^2=x_E^3+432\).

## Construction and checks

The [frozen initial protocol](protocol.json) screened monomials
\(x_C^a y_C^b x_E^c\) with \(b\in\{0,1\}\), \(c\leq12\), and
\(2a+3b+2c\leq D\). Both \(\mathbf F_{997}\) and
\(\mathbf F_{1009}\) had full column rank through \(D=80\).
The [frozen extension](extension_protocol.json) increased precision
and found nullities 6, 22, 38, and 54 at weights 96, 112, 128, and
144 in both fields. Restricting the weight-96 kernels gave zero
relations at weights 81 through 89 and a unique relation at weight
90 in both fields. These are finite-field ranks on the specified
Laurent-coefficient matrices; the exact identity below supplies the
characteristic-zero existence certificate.

The [lift](lift_result.json) recomputed the restricted relation in
28 additional primes, using coefficients \(q^{-90}\) through
\(q^{1100}\) and a separate \(q^{1101}\)–\(q^{1200}\) holdout in
each. The first 29 primes reconstructed every rational coefficient;
the 30th prime, 1201, was held out and matched all 1,014 coordinates.
The [reconstruction receipt](reconstruction.json) retains the dense
coefficient vector, exact rational pairs, prime list, CRT modulus,
and holdout comparison. Multiplying by the least common denominator
\(600378541187996484\) yields the primitive integer polynomial.

The [exact verification](exact_verification.json) computes the
characteristic-zero normalized modular \(q\)-maps through source
precision 3500 and checks every coefficient of \(H\) from
\(q^{-90}\) through \(q^{3312}\) is zero. The minimum precision
of the input powers is 3410, so this interval is defined.

This finite coefficient check proves the function-field identity.
The degree-24 forgetful map to \(C\) makes \(x_C\) and \(y_C\)
functions of degrees 48 and 72 on \(X_0(432)\). The normalized map
to the optimal curve \(B:y^2=x^3-16\) has degree 24; composing its
degree-three isogeny to \(E\) makes \(x_E\) a function of degree 144.
Each monomial therefore has pole divisor degree at most
\(48a+72b+144c\leq3312\). A nonzero rational function on a complete
curve cannot have a zero of order at least 3313 at one point while
its entire pole divisor has degree at most 3312. Thus \(H=0\)
identically. The prior [Sturm-certified map identity](../hecke-432-map-identity-20261025/RESULT.md)
identifies the normalized \(B\)-to-\(E\) composition with the geometric
level-432 evaluator.

The [independent fiber check](fiber_verification.json) specializes
\(C=(639,232)\) over \(\mathbf F_{997}\) and obtains a degree-12
polynomial with leading coefficient 300. It equals that coefficient
times the product over all 12 distinct \(x_E\) values in the
[complete geometric fiber](../hecke-432-geometric-fiber-20261025/evaluation.json)
over \(\mathbf F_{997^4}\); all 12 direct evaluations vanish.
Consequently the degree-12 coefficient of \(H\) is a nonzero
function on \(C\). The earlier generic-degree result then makes
this exact relation minimal over \(\mathbf Q(C)\).

| Result | Formalization status |
| --- | --- |
| Weight and map-degree arithmetic \(48a+72b+144c\leq3312\) | `RelativePoleBound.monomial_pole_bound` and `q_order_exceeds_monomial_poles` build in pinned Lean 4; axiom audit uses only standard foundations. |
| Exact coefficient identity | Checked Sage over \(\mathbf Q\), with the executable coefficient receipt above. Encoding the 278-term polynomial and modular \(q\)-maps in Lean remains open. |
| Pole-divisor argument and minimality over \(\mathbf Q(C)\) | Written proof above using modular-curve morphism degrees and the prior degree-12 theorem; faithful Lean modular-curve function-field and divisor definitions remain open. |

The Lean command, output, dependency revision, and `#print axioms`
are in [formal](formal/). `lean4checker --fresh` is unavailable on
this host. The checked Sage [runtime receipt](sage-runtime-info.txt)
pins the accepted local build.

Replay from the repository root:

```sh
python3 experiments/hecke-432-relative-resolvent-20261025/verify.py
./sage --runtime-info
./sage -python experiments/hecke-432-relative-resolvent-20261025/generate_extended_sage.py
./sage -python experiments/hecke-432-relative-resolvent-20261025/screen_extended_sage.py
./sage -python experiments/hecke-432-relative-resolvent-20261025/extract_minimal_sage.py
./sage -python experiments/hecke-432-relative-resolvent-20261025/lift_sage.py 1013 1019 1021 1031 1033 1039 1049 1051 1061 1063 1069 1087 1091 1093 1097 1103 1109 1117 1123 1129 1151 1153 1163 1171 1181 1187 1193 1201
./sage -python experiments/hecke-432-relative-resolvent-20261025/reconstruct_sage.py
./sage -python experiments/hecke-432-relative-resolvent-20261025/verify_exact_sage.py
./sage -python experiments/hecke-432-relative-resolvent-20261025/verify_fiber_sage.py
python3 experiments/hecke-432-relative-resolvent-20261025/export_resolvent.py
```

For the next constructive step, solve for the optimal \(B\) coordinates
inside the quadratic \(y_E\) extension and use the existing
kernel-chain moduli evaluator to check the inverse map on complete
geometric fibers. The degree-12 resolvent provides the exact algebraic
input for that calculation.
