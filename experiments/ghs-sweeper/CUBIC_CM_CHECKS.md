# Fixed CM/polarization check, frozen 2026-10-25

This is a proof-oriented finite calculation. Its geometric bridge is a separate
obligation, not certified by enumerating integer triples. The source curves
are the b=59 F512 twist pair with traces +/-35 and discriminant -823.

Investigate a refined indecomposability test at ell=53. Conditional inputs:
the source restriction is simple over F8; Frobenius therefore permutes three
elliptic factors transitively in a hypothetical geometric polarized splitting;
degrees of geometric homomorphisms between distinct source conjugates are
represented by 8*x^2+3*x*y+26*y^2. Do not report the finite calculation as a
proof of those inputs.

In a splitting, component degrees a,b,c sum to 53. One-component support
contradicts transversality. Two-component support has a single nonzero term
in a polarized off-diagonal product and cannot be orthogonal. For three
components, pair products ab,ac,bc must be represented by that norm form,
and their square roots must be triangle side lengths. The exact integer
inequality is (ab)^2+(ac)^2+(bc)^2 <= 2*abc*(a+b+c).

Enumerate every sorted positive a<=b<=c with sum 53. Pair products are at
most 676. The identity 32*norm=(16*x+3*y)^2+823*y^2 bounds every possible
witness by |y|<=5 and |x|<=10; enumerate that rectangle completely. Retain
all degree-feasible triples and any surviving triangle test. Survivor count
is unknown before this check. The norm controls (0,1)->26, (-2,1)->52,
(5,4)->676 and the false triangle (1,26,26) prevent a vacuous rejection.

Independently record all eligible primes <=53, checking the source
discriminant modulo each. At 53 construct abstract weighted transverse
kernels for both Frobenius traces, check the action on the basis, its
isotropy and every 53^3 coefficient triple's coordinate intersections.
No actual E[53] point or quotient curve is supplied by these checks.

Also check that no integer u in the norm-eight Hasse interval [-5,5]
satisfies u^3-24*u=+/-35. The claimed implication to irreducibility of the
restriction polynomial needs its written CM/cubic-root argument.

Freeze code and contract before execution. Retain failures, source hashes,
exact commands, raw output and exit status. A zero finite survivor count
is an implication conditional on the geometric inputs, not an evaluated
attack, a publication-novelty result or a performance claim.
