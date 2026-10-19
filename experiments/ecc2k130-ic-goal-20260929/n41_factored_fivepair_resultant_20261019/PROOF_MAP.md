# Proof map

| Result | Formal or computational evidence | Exact scope |
| --- | --- | --- |
| A linear relation `Lz+M=0` and `Cz²+pz+H=0` force `CM²+pLM+HL²=0` | `FactoredElimination.linear_quadratic_elimination` | Any field of characteristic two, including `C=0`. |
| Reduction of a quartic modulo the first quadratic | `FactoredElimination.quartic_reduction` | Exact denominator-free coefficients `Lnum,Mnum` with powers of `C`. |
| First pair quadratic plus eliminated quartic force the final condition | `FactoredElimination.quartic_quadratic_elimination` | Structural composition, without a nonzero-leading-coefficient hypothesis. |
| Second pair quadratic plus S3 force the `K0..K4` quartic | `FactoredElimination.second_pair_s3_elimination` | Exact characteristic-two S3 and pair law. |
| Both pair quadratics plus S3 force the final factored condition | `FactoredElimination.two_pair_factored_necessary` | Full generic algebraic necessary theorem; no curve-specific reciprocal-coordinate bridge is assumed in its statement. |
| The denominator-free expression matches the N41 37-term frozen resultant, including its `C³` scale | Checked-Sage `factor_identity_retry.py`, `factor_retry_result.json` | Exact polynomial identity over the declared `GF(2^41)` representation; the first missing-scale failure remains in `factor_first_attempt_failure.json`. |
| The five-pair circuit admits the archived ordinary relation | `build_fivepair.py`, `build_result.json` | All emitted CNF and XOR rows plus independent Sage point-sum control on the frozen oriented raw target. |

The toolchain is pinned in [`lean-toolchain`](lean-toolchain). Running
`lean FactoredElimination.lean` builds the actual module; [`lean.stdout`](lean.stdout)
records `#print axioms` for all five declarations. Each lists only the
standard `propext`, `Classical.choice`, and `Quot.sound` foundations. The
source contains no `sorry`, `admit`, custom research axiom, or native
evaluation bypass. `lean4checker --fresh` was unavailable on this host.

The remaining formalization bridge is the interpretation of the concrete
binary-curve reciprocal x coordinates and fixed-seed pair products as the
generic theorem's `z₁,z₂,p,q,t`. The checked-Sage witness construction and
the earlier two-pair exhaustive N41 code census test that bridge for the
frozen instances; a full Lean curve/field model is still open.
