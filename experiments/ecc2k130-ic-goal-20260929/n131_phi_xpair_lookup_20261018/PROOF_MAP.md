# Negation-quotiented pair lookup proof map

The central structural result is checked in [XPairLookup.lean](XPairLookup.lean)
under the pinned Lean 4.34.1 toolchain (commit
`5045d0056413266e57c625dcd7c365b10e377c52`). It imports only the bundled
`Std` and Lean `Init.Grind.Ring.Basic` modules.

| Result | Lean declaration | Exact hypotheses | Verification |
| --- | --- | --- | --- |
| When a key identifies a group point up to sign, an indexed pair with that key yields the target either directly or by negating both pair inputs. | `XPairLookup.lift_sign` | Any additive commutative group `G`; a key function whose equal-key fibers are `{u,-u}`; exact pair sum and target key equality. | `lean XPairLookup.lean` passed; `#print axioms` reports only standard `propext`. |

The actual command output is in [lean_check.log](lean_check.log).
`lean4checker --fresh` was unavailable. The full theorem is conditional on
the key-fiber hypothesis; a Lean bridge from the archived binary curve's
coordinate law to that hypothesis is not present. For this finite Q1358
domain, [audit_sage.py](audit_sage.py) independently enumerates all
1,132,096 signed sums and checks the 566,048-key image. The producer
reconstructs and checks every returned positive witness by exact group
arithmetic. This is the concrete audit boundary for the measured index.
