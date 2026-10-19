# secp256k1 sparse Eisenstein radix point-correctness bridge

- **Status:** `open`
- **Kind:** proof gap (digit-selector/limb refinement and curve group-law bridge)
- **Affected work:** [sparse radix family](../experiments/prime-j0-eisenstein-residue-20261015/SPARSE_RADIX_FAMILY.md), [sparse radix report](../experiments/prime-j0-eisenstein-residue-20261015/SPARSE_RADIX_FAMILY_REPORT_2026-10-19.md), [sparse `127+128τ` path](../experiments/prime-j0-eisenstein-residue-20261015/SPARSE_TAU_RADIX.md), [scalar-local synthesis](../experiments/prime-j0-eisenstein-residue-20261015/ON_DEMAND_DIGITS.md), [projective synthesis report](../experiments/prime-j0-eisenstein-residue-20261015/PROJECTIVE_DIGITS_REPORT_2026-10-19.md), and dependent checkpoint/projective digit paths
- **Next action owner:** scalar-arithmetic proof implementer (unassigned)
- **Last updated:** 2026-10-19

## Problem

The finite secp256k1 panels verify selected radix outputs, but an all-scalar correctness claim for the `k=5,6,7` sparse Eisenstein recoders is blocked by the missing uniform selector/quotient-to-Lean refinement and concrete curve group-law bridge.

The instance is SEC 2 secp256k1, `y²=x³+7` over `p=2²⁵⁶−2³²−977`, with prime subgroup order `n=FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141`. The tested radices are `πₖ=(2ᵏ−1)+2ᵏτ`, `τ²=3τ−3`, for `k=5,6,7`. Existing conditional terminal results target norm below 5,000 after 20, 17, and 15 steps respectively. The affected evidence requires exact outputs for the frozen fixtures and honest separation from universal correctness.

## Evidence and uncertainty

- **Observed:** [sparse-radix-family-screen.json](../experiments/prime-j0-eisenstein-residue-20261015/sparse-radix-family-screen.json) checks integer-pair reconstruction for 12,288 frozen scalars. Its `native_point_replay` field remains `pending` for all three rows. Separate hash-pinned native pilots and the four [Tier 1 audit receipts](../experiments/prime-j0-eisenstein-residue-20261015/SPARSE_RADIX_FAMILY.md) verify outputs on their stated one-scalar or 12,288-point workloads; those are finite checks. The `k=7` [Lean module](../experiments/prime-j0-eisenstein-residue-20261015/SparseTauRadix.lean) and [family module](../experiments/prime-j0-eisenstein-residue-20261015/SparseRadixFamily.lean) are pinned and their committed receipts show successful builds and axiom audits.
- **Observed:** the projective `31+32τ` path's independent full-fixture replay checks 12,288 outputs in each of two identical candidate arms (job `3cddff74cf9349bdaec7b6910c4884a0`); the corrected one-scalar and 128-point Tier 1 panels independently replay their measured outputs (jobs `508270ee2b714b2db002f9c37b906f38` and `47fb3c09560f494eb27769d25135e7e4`). These results extend finite implementation evidence only. They do not prove the scalar selector or native point formulas for all subgroup inputs.
- **Derived or proved:** the Lean modules prove pair multiplication, radix norm, quotient-root identities, norm scaling, exact trace reconstruction, and point-Horner evaluation under explicit abstract `map_add` and `map_radix` hypotheses. The `k=5` and `k=6` terminal norm theorems assume per-step recurrences and digit caps; the current native selector is not proved to satisfy those hypotheses for every reduced scalar.
- **Suspected explanation:** no counterexample is known. The missing results are formal links, not evidence of a mathematical obstruction.
- **Missing capability:** a proof that the bounded residue-lift search and fixed-width quotient code implement the mathematical digit rule for every subgroup scalar; uniform digit-norm and terminal bounds; and a theorem refining the actual `U256` point/endomorphism routines to secp256k1 group addition and the concrete `τ` action. The local review worktree had no `lean` executable, so the committed pinned proof receipts were checked by source digest rather than rebuilt here.
- **What this evidence does not establish:** fixture replay does not establish correctness for all subgroup scalars, selector optimality, a universal memory bound, or a curve-wide group-law refinement. The existing prime-j0 hex terminal chooser problem concerns a different radix and does not discharge this obligation.

## What would unblock it

- [ ] Prove for every scalar `0≤s<n` that each exact fixed-width selector and quotient implementation for radix `k=5,6,7` produces the stated residue, digit, and integral next pair; prove the required uniform digit-norm cap and compose each initial lattice bound with its full-step terminal theorem.
- [ ] Prove the concrete secp256k1 point map for `τ` and each radix from the implemented field/point formulas, including exceptional cases, and connect it to elliptic-curve group addition; prove the native operation implements that map for all valid subgroup points.
- [ ] Build the pinned Lean modules and all additions with no `sorry`, `admit`, or custom claim axioms; audit `#print axioms`; add source-synchronized checks connecting the Rust routines to the checked definitions. Preserve existing finite panels and report their exact scope separately.

Meeting these conditions would establish mathematical and implementation correctness of the sparse recoding paths for every scalar in the specified subgroup. It would not establish timing or memory claims beyond the existing workload-specific panels, prove selector optimality unless separately shown, or resolve any unrelated radix, table, or rho obligation.

## Next discriminating step

- **Action or proof obligation:** start with a theorem connecting the exact `k=6` fixed-width digit-step routine to the `familyPair` quotient and the explicit uniform digit cap, then compose it with `radix64_terminal_from_norm_step`.
- **Inputs and controls:** the exact native overlay and source hashes in the `k=6` cold/prepared manifests, `SparseRadixFamily.lean`, `screen_sparse_radix_family.py`, and the existing frozen fixture. Keep the present finite screen and native panels as regression controls.
- **Execution limits and stop condition:** quantify over every reduced scalar and preserve the existing 17-step terminal bound; a bounded sample or an unproved native evaluation does not close the obligation. If the selector violates a required cap, preserve a counterexample and update the algorithm and its downstream frozen evidence under the normal review process.
- **Outcomes and next actions:** a checked selector/quotient bridge advances to composing the point-map proof; a counterexample requires a corrected selector plus new frozen correctness evidence; an unavailable Lean dependency remains a tool limitation and leaves the proof open.
- **Recheck trigger:** change to a radix, selector, quotient implementation, terminal bound, curve point/endomorphism formula, or proof dependency.

## Resolution and history

- 2026-10-19: opened while documenting the finite `k=5,6,7` family and re-auditing four existing Tier 1 panels. The panels and committed proof receipts are positive scoped evidence; no all-scalar selector/curve refinement was attempted or claimed. Unresolved.
