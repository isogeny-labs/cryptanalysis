# Proof map

The pinned Lean toolchain is `leanprover/lean4:v4.34.1` in
[lean-toolchain](lean-toolchain). `lean SharedQuadratic.lean` completed;
the [log](lean_check.log) records `#print axioms` for every declaration.
The only reported foundations are `propext`, `Classical.choice`, and
`Quot.sound`; no `sorry`, `admit`, or custom research axiom occurs.
`lean4checker --fresh` was unavailable in this environment.

| Mathematical statement | Lean declaration | Exact hypotheses | Status |
| --- | --- | --- | --- |
| `p(c13+c33*p^2)=c13*p+c33*p^3` | `SharedQuadratic.leading_expansion` | Arbitrary commutative ring | Kernel checked |
| Multiplication by a reciprocal preserves all zeroes | `SharedQuadratic.normalized_zero_iff` | Arbitrary commutative ring; supplied `a*reciprocal=1` | Kernel checked |
| Normalized pair coefficient equals the shared `B_ij` | `SharedQuadratic.shared_quadratic_coefficient` | Same unit hypothesis; arbitrary coefficient `b` | Kernel checked |
| Exceptional source values obey the two-factor disjunction | `SharedQuadratic.exceptional_factorization` | Arbitrary commutative ring with explicit no-zero-divisors hypothesis | Kernel checked |
| Sixteen branch entries per ordered pair | `SharedQuadratic.branch_enumeration_length` | Arbitrary lists and output mapping `A -> B -> Fin 16 -> P` | Kernel checked |
| Frozen resultant has only `(1,3)` and `(3,3)` terms with second exponent three | `probe.py` exact support assertion; independent source export | Exact hash-pinned N41/N131 coefficient tables | Computational bridge |
| Unique nonzero `A` root and its exclusion from the source span | `probe.py` finite-field root/span computation and independent `audit_sage.py` | Exact binary fields, masks, rotations, source bases and target coefficients | Computational bridge; not a Lean finite-field theorem |
| At most two y-branches per source x and at most sixteen assignments per ordered code pair | Written degree-two argument; `branch_enumeration_length` for the resulting branch index | Curve `y^2+xy=x^3+1`, two endpoints per code | Curve-to-enumeration Lean bridge open |

The normalization proof preserves every zero when `A(p)` is invertible.
Code zero is handled separately; it cannot be silently divided by `A`.
The finite-field and curve bridges are stated as their own obligations
rather than folded into the generic algebra theorem.
