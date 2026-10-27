# Proof map

| Result | Lean declaration | Exact scope | Status |
| --- | --- | --- | --- |
| Four-term group relation transports through a map preserving addition | `FourTermCoverage.four_transport` | Arbitrary types `G,H`, binary operations, map `φ`, universal addition preservation, and an explicit four-term relation | Kernel checked; no axioms |
| Each of the 28 enumerated triple residual scalars has the reported signed four-log sum modulo 2531 | `FourTermCoverage.residual_0` through `residual_27` | Concrete integer logs and scalar in each frozen row, exact modulus 2531 | Kernel checked; no axioms |
| Every subgroup scalar has a signed four-distinct-source representation | None yet | Exact 40 class logs, all 2531 scalars, and distinct indices | Finite producer and independent Sage audit pass; Lean theorem open |
| Curve-group interpretation of all 28 witnesses | None yet | `E/F_63317: y²+y=x³−x²−10x−20`, order-2531 subgroup, projected class points and log equalities | Independently checked in Sage; Lean curve definitions and bridge open |

The module uses Lean 4 `v4.35.0-rc4`, pinned in `formal/lean-toolchain`, with `Init` only. `cd formal && lake build` succeeded; `formal/build-output.txt` retains `#print axioms` output for the transport theorem and every residual certificate. `lean4checker --fresh` was unavailable in this environment. No `sorry`, `admit`, custom axioms or native evaluation occur in the module.
