# Functional S3 proof map

## Mathematical statement

In a field of characteristic two, write an S3 link with fixed nonzero
`B = ab`, `A = B² + 1`, and `D = (a+b)²` as

`A z² + B z + D = 0`.

Let `v` satisfy `Bv = 1`, and let `h` satisfy
`h² + h = A D v²`. Every S3 root satisfies one of the two branch equations
`Az = Bh` and `Az = B(h+1)`. This includes `A=0`; no inverse of `A` is
used in the branch equation.

The proof sets `u=Azv`, reduces the S3 equation to
`u²+u=ADv²`, and observes that `(u+h)²+(u+h)=0`. Thus
`(u+h)(u+h+1)=0`; the field has no zero divisors, giving the two branches.

## Lean declaration and build

`FunctionalS3.functional_branch_exists` in [FunctionalS3.lean](FunctionalS3.lean)
has precisely the characteristic-two, reciprocal, S3, and halftrace-root
hypotheses above. Its conclusion is the two branch equations. The pinned
toolchain is `leanprover/lean4:v4.34.1` in [lean-toolchain](lean-toolchain).

Run `lean FunctionalS3.lean` in this directory. The checked run exited 0;
[#print axioms output](lean.stdout) lists only `propext`,
`Classical.choice`, and `Quot.sound`. `lean4checker --fresh` was unavailable
on this host. There are no admitted proof obligations in the module.

## Implementation bridge

For the odd-degree field `GF(2^41)`, the circuit computes
`q=ADv²`, enforces `Tr(q)=0`, and applies coefficientwise
`L(y)=halftrace(y+Tr(y))`. Linearity gives `L(q)=halftrace(q)` when
`Tr(q)=0`, hence `L(q)²+L(q)=q`. It adds one Boolean branch bit per S3
link and retains the original S3 polynomial, which also covers any
exceptional path at the circuit level. The [build result](n41_build_result.json)
checks the archived complete witness against all 129,763 CNF clauses and
5,272 native XOR rows. That finite check validates this witness and the
generated formula; the generic bit-level implementation bridge is not a
separate Lean theorem.
