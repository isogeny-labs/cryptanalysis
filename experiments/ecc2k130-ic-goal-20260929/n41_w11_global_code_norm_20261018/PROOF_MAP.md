# Proof map

The new implementation applies a previously checked finite-product identity
to the frozen W11 two-code source. For a target residual `T`, define the
13-term resultant `F_T(p,q)`, the exact valid product sets `P,Q`, and
`N_T(X)=∏_{q∈Q}F_T(X,q)`. The existing declaration
`JointNorm.product_zero_iff` in
[`JointNorm.lean`](../n41_joint_fourpair_resultant_20261012/JointNorm.lean)
proves, under `one ≠ zero` and multiplication-zero iff either factor is
zero, that this product vanishes at `p` exactly when one listed `q`
factor vanishes. Its pinned Lean check is in the preceding directory.

The written polynomial proof completes the exact source intersection:
`A(X)=∏_{p∈P}(X+p)` splits into distinct linear factors because the
archived product map is injective. Over a field, a source value `p` is a
root of `gcd(A,N_T)` iff it is a root of both polynomials. Consequently
the GCD's roots are exactly the first source products that admit a valid
second product satisfying the resultant. Each returned pair is then
checked against the original resultant and the prior curve-sum replay.

Lean formalization of the concrete Sage polynomial-GCD operation and the
archived code-to-product map is open. The [verifier](verify.py) binds the
25 computed root sets to the independent native all-code resultant census.
The existing `JointNorm` proof checks the finite-product bridge; this
experiment adds an implementation and exact finite-domain measurements,
not a new algebraic theorem.
