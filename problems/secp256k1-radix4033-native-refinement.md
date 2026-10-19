# Norm-4033 secp256k1 native selector and point-map refinement

- **Status:** `open`
- **Kind:** proof gap (executed-selector refinement and concrete curve group-law bridge)
- **Affected work:** [norm-4033 selector and measurements](../experiments/prime-j0-eisenstein-residue-20261015/RADIX4033.md), [source-linked report](../experiments/prime-j0-eisenstein-residue-20261015/RADIX4033_REPORT_2026-10-19.md), and the fixed-table norm-4033 path in the same experiment
- **Next action owner:** scalar-arithmetic proof implementer (unassigned)
- **Last updated:** 2026-10-19

## Problem

All-scalar correctness of the executed norm-4033 secp256k1 path is not established because the finite selector proof is not refined to the Rust signed-limb/tie-order implementation, and the abstract `ω`/radix maps are not proved to be the concrete curve group operations.

The instance is SEC 2 secp256k1, `E:y²=x³+7` over `p=2²⁵⁶−2³²−977`, with prime subgroup order `n=FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141`. The radix is `π=64+ω=65−τ`, with norm 4033. The native selector enumerates nearby residue lifts and a five-by-five window, uses deterministic tie breakers, computes the exact quotient in fixed-width signed limbs, and applies 22 Horner steps. Finite fixture and residue checks are not an all-scalar implementation proof.

## Evidence and uncertainty

- **Observed:** [Radix4033.lean](../experiments/prime-j0-eisenstein-residue-20261015/Radix4033.lean), [Radix4033Bounds.lean](../experiments/prime-j0-eisenstein-residue-20261015/Radix4033Bounds.lean), and [Radix4033Selector.lean](../experiments/prime-j0-eisenstein-residue-20261015/Radix4033Selector.lean) were rebuilt with pinned Lean 4.34.1; dated receipts are in [lean-checks-2026-10-19](../experiments/prime-j0-eisenstein-residue-20261015/lean-checks-2026-10-19/). The mathematical model proves the finite search's digit bound and exact quotient for every integer-pair state, and a conditional 22-step terminal table bound.
- **Observed:** [audit_radix4033_selector.py](../experiments/prime-j0-eisenstein-residue-20261015/audit_radix4033_selector.py) matches Rust tie choices to an independent exhaustive minimum on 2,017 nonnegative residues; negation covers all 4,033 classes. The audit reports maximum digit norm 1,323 and maximum absolute coordinates 63 and 42. Hash-pinned Tier 1 panels independently replay measured outputs; serial candidate A/A replays verify all 12,288 outputs per arm.
- **Derived or proved:** the Lean selector theorem uses mathematical integer pairs and an abstract pair action. The theorem proves a 22-step table bound only under its explicit initial lattice, exact quotient, and selector hypotheses. The native output replays establish equality only on their frozen finite fixtures.
- **Suspected explanation:** no counterexample is known. The open items are implementation and curve-map refinement obligations; no mathematical obstruction has been proved.
- **Missing capability:** a checked correspondence from the Rust candidate enumeration, `i32`/`i16` arithmetic, lexicographic ties, residue normalization, and quotient divisions to the Lean selector/quotient definitions, plus a proof that the implemented `ω` rotation and projective addition realize the endomorphism and group law for all valid subgroup inputs. `lean4checker --fresh` was unavailable for the recorded rebuild.
- **What this evidence does not establish:** the finite audit and fixture replay do not prove the selector's implementation for all scalars, universal point multiplication correctness, constant-time behavior, or a performance guarantee outside the stated Tier 1 allocation and workload.

## What would unblock it

- [ ] Prove, for every subgroup scalar `0≤s<n`, that the exact native signed-limb selector and fixed-width quotient implement the stated norm-4033 digit step, including overflow bounds, residue normalization, and the Rust tie order; compose with the 22-step terminal theorem.
- [ ] Prove that the concrete secp256k1 `ω` x rotation and projective addition implement the abstract point endomorphism and group law for all valid subgroup points, including exceptional cases, and link the source-level field formulas to those definitions.
- [ ] Rebuild the additions with pinned Lean 4.34.1, retain `#print axioms`, and add source-synchronized checks for the executed Rust formulas. Preserve the finite controls and receipts separately.

These conditions would establish mathematical and implementation correctness of the specified norm-4033 path for every subgroup scalar and point. They would not convert the failed fixed-table A/A comparisons into performance claims, or extend the measured timings to other hosts or input distributions.

## Next discriminating step

- **Action or proof obligation:** formalize the exact native `(i32,i16)` residue/lift/tie-order selector as a refinement of the Lean finite search, then connect the quotient matrix in `native_sparse_radix4033_overlay.py` to `Radix4033Selector.total_selected_step`.
- **Inputs and controls:** `native_sparse_radix4033_overlay.py`, the selector/quotient code in `radix4033-native-provenance.tar.gz`, `Radix4033Selector.lean`, `Radix4033Bounds.lean`, and the residue audit's 4,033 signed classes. Keep the committed fixture replay as a regression control.
- **Execution limits and stop condition:** quantify over every reduced subgroup scalar and preserve the exact 22-step bound and tie semantics. A bounded sample alone does not close the obligation. If a source branch violates the model, retain a counterexample and update the algorithm and downstream evidence under the normal review process.
- **Outcomes and next actions:** a checked selector refinement advances to the concrete curve point-map proof; a counterexample requires correcting the selector and regenerating only the affected frozen evidence; an unavailable proof dependency leaves the result open.
- **Recheck trigger:** changes to the selector, quotient arithmetic, step count, curve formulas, signed-limb representation, or Lean dependencies.

## Resolution and history

- 2026-10-19: opened while documenting the finite selector proof and native norm-4033 panels. The fresh Lean builds, residue audit, and finite point replays are positive scoped evidence, not all-scalar native refinement. Unresolved.
