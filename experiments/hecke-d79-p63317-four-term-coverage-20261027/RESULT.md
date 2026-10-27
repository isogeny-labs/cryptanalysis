# One fixed fourth source closes the p63317 triple residual set

For the 40 projected class points in the p63317 subgroup of order 2531, the signed three-distinct-source family covers 2503 subgroup elements. The other 28 all have a signed four-distinct-source representation. Under the frozen source and sign order, every residual is found on its first probe: subtracting `−B₀` leaves a three-source relation using indices other than 0. Thus the union of the triple family and its fixed translate by `−B₀`, with the distinct-index rule checked, covers all 2531 subgroup elements.

## Frozen enumeration and independent replay

The producer enumerated `C(40,3)·2³ = 79,040` signed triples, retaining every witness by scalar. It reconstructed the 28 residual scalars in ascending order, then applied at most 80 fixed-order fourth-source probes to each. All 28 rows have status `FOUND`, with `probes=1`. Independently, it enumerated `C(40,4)·2⁴ = 1,462,240` signed four-source patterns and found 2531 distinct subgroup scalars.

The checked-Sage audit rebuilt the 40 projected curve points, verified every anchored log against the order-2531 generator, derived the triple residual set from actual group points, and replayed each of the 28 four-source equations and scalar certificates. Its independent signed four-source scalar enumeration also covered all 2531 values. The exact point/curve input hashes, protocol, producer hash, post-run receipt, runtime identity and row-level witnesses are retained beside this report.

This is a finite relation-family coverage result for the recorded `p=63317` curve, subgroup, and class-point set. It is separate from the same-public-target pair/triple progression: the residual values are exhaustive coverage inputs, not substituted public targets. The local search timings are stage diagnostics, with `candidate_id` and `target_online_ms` null.

## Proof status and next step

The Lean module proves generic four-term transport under an additive map and kernel-checks all 28 residual modular witness equations. `PROOF_MAP.md` lists the exact conditional bridge to the Sage curve points and the remaining Lean work for the complete 2531-element coverage theorem. The next experiment should test how a deterministic one-index translate changes relation yield and preparation cost on a separate, frozen unseen-target workload, retaining a complete candidate and same-point rho gate for any online comparison.
