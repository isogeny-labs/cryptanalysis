# Proof map for code-parametric sign duals

For each of the 35 frozen lower-root charts, the seven-point determinant is a
Boolean polynomial in six sign bits,

`D_c(s) = a_c + Σ_{M≠∅} b_{c,M} s^M`, with coefficients in `GF(2^41)`.

The proposed code-dependent linear functional is an eight-code-bit Boolean
polynomial of degree at most `d` with field-bit masks as coefficients:

`L_d(c) = ⊕_{|A|≤d} c^A ℓ_A`.

It excludes every sign assignment in a chart when the bit dot product
`⟨L_d(c),a_c⟩=1` and `⟨L_d(c),b_{c,M}⟩=0` for every nonempty `M`.
Linearity then gives `⟨L_d(c),D_c(s)⟩=1`, so every determinant in that chart
is nonzero. This implication is also checked in the preceding
`n41_n131_parametric_rr_dual_20261016/DualCertificate.lean` under its
explicit linearity hypothesis.

For degree two, each required dot-product equation is a row in a binary
linear system with `37×41` formal unknown bits. The 235 labeled equations
in [`result.json`](result.json) XOR to zero on every unknown bit, while
their required right-hand sides XOR to one. Any map `L₂` would therefore
give `0=1`. The [independent replay](audit_result.json) reconstructs the
rows by a different coefficient-block loop and checks both parities.
Degree zero and one have separately saved contradictions. The degree-three
solution is checked against all 2,240 coefficient equations and all 2,240
sign evaluations.

[`ParametricDual.lean`](ParametricDual.lean) formalizes the structural
contradiction for any Boolean-linear score and an odd dependency of
equation rows. Its declarations `map_xorRows` and
`odd_dependency_excludes_dual` compiled with pinned Lean 4.34.1;
[`lean.stdout`](lean.stdout) reports only standard `propext` and
`Quot.sound`. The finite 235-row certificate and concrete `GF(2^41)`
coefficient-to-curve bridge are checked computationally and remain open as
kernel-level formalizations. There are no `sorry`, `admit`, custom axioms,
or native evaluation in this module. `lean4checker --fresh` is unavailable
on this host.

The panel fixes five pair states and selects only the lower x root for the
free first pair code. The archived public relation uses an upper-root
chart, so the certificate is not a complete-code exclusion; the upper-root
branch remains in the source domain.
The terminal verifier reads the prior full-root census and checks its
mask-6, upper-root, sign-15 zero chart.
