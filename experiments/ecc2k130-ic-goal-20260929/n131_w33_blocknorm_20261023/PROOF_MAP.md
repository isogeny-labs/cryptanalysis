# Proof map: target-conditioned block norm

The new work applies the existing finite-product theorem to a block of specialized resultants. The theorem is [JointNorm.product_zero_iff](../n41_joint_fourpair_resultant_20261012/JointNorm.lean), checked again with the pinned Lean toolchain by `lean JointNorm.lean`; this archive saves the `#print axioms` output in `lean_joint_norm.stdout`.

| Mathematical step | Formal/evidence status | Exact scope |
| --- | --- | --- |
| A finite product of field values is zero exactly when one listed factor is zero | `JointNorm.product_zero_iff`, checked; axioms `propext`, `Quot.sound` | Any list and any multiplication with no zero divisors and `1≠0` |
| `N_{T,B}(q)=0` exactly when some `p∈B` has `F_T(p,q)=0` | Direct instance of the checked theorem | Every finite block, including duplicate codes; exceptional zero quartics explicitly retained |
| Positive-degree `gcd(N_{T,B},A)` or `gcd(N_{T,B},L_V)` exactly when a permitted right root exists | Written field-polynomial proof below; concrete Sage GCD and N131 basis bridge checked against independent controls | N41 281-code right set, N131 32-dimensional right product subspace |
| Specialization and field representation | Frozen source hashes, N41 direct right-code enumeration, 32 archived N131 per-code decisions, and 128 independent native scaling decisions | Exact field moduli, source seed, rotations, target coefficient rows, and raw prefix codes in the protocols |

For the polynomial step, let `R` be either right-source vanisher. Over a field, `gcd(N,R)` has positive degree exactly when the two polynomials share a root over an algebraic closure. Here every root of `R` is in the declared right source: for N41, `R` is the product of the 281 distinct linear factors `Z+q`; for N131, the basis-adjunction recurrence constructs a monic linearized polynomial whose roots are exactly the 32-dimensional binary span of the verified independent rotated products. Hence a positive-degree GCD implies a permitted `q` with `N(q)=0`; the checked finite-product theorem then gives a first product in the block. The reverse implication follows because a common right root divides both polynomials. Reducing `R` modulo `N` leaves the GCD unchanged. If a specialized quartic is the zero polynomial, the block is retained before GCD reduction.

The concrete Sage polynomial-GCD and linearized-basis bridge is computationally checked, not fully formalized in Lean. This is the same open bridge identified in the earlier global-norm proof map; this experiment adds a bounded implementation and paired measurements rather than a new algebraic theorem. The Lean module has no `sorry`, `admit`, custom claim axiom, or native proof shortcut. `lean4checker --fresh` was unavailable on this host.
