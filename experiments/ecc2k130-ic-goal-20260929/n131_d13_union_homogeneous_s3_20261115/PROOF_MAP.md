# Homogeneous S3 proof map

| Result | Lean declaration or replay | Exact hypotheses | Status |
| --- | --- | --- | --- |
| Denominator-cleared S3 identity | `HomogeneousS3.cleared_identity` | Any commutative ring and three chart equations `d_i*z_i=n_i` | Lean 4.34.1 checked; standard axioms only |
| Equality of S3 zero sets | `HomogeneousS3.cleared_zero_iff` | Any field, the chart equations, and all three denominators nonzero | Lean checked; standard axioms only |
| Factored `z²+z` numerator | `HomogeneousS3.yNum_factored` | Any commutative ring | Lean checked; standard axioms only |
| Branch denominator nonzero | `HomogeneousS3.branch_denominator_nonzero` | Any field; assumes `1+phi²+phi != 0` for the image branch | Lean checked; N131 trace implication remains in the written proof and exact Sage census |
| Exact d13 branch/group interpretation | Earlier `BranchEquation.lean` and all-selector Sage replay | Exact N131 curve, valid d13 selector, adjacent-Frobenius map | Prior branch algebra checked; full Lean curve group and finite-field trace bridge remains open |
| Complete circuit assignment | `planted_control.py` and prior independent Sage group replay | Frozen ten-leaf synthetic target and all primary bits | All 332,220 clauses and 333,883 XOR rows checked; prior Sage verifies the points and sum |

For each leaf let `z=n/d`, `U=n²+nd`. Then `d²(z²+z)=U`.
For three chart pairs, multiplying
`(z₁²+z₁)(z₂²+z₂)(z₃²+z₃)+(z₁+z₂+z₃)²`
by `(d₁d₂d₃)²` gives
`U₁U₂U₃+(n₁d₂d₃+n₂d₁d₃+n₃d₁d₂)²`.
The Lean zero-set theorem uses nonzero denominators to remove the factor;
there is no change to the affine exceptional-case boundary.

Build with `lean HomogeneousS3.lean` in this directory. The pinned
toolchain is Lean 4.34.1; `lean.stdout` retains each `#print axioms`
result. `lean4checker --fresh` is unavailable on this host.
