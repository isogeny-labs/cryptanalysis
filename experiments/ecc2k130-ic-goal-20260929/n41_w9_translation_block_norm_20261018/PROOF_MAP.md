# Proof map: target-translated quadratic norm block gate

| Mathematical result | Lean declaration | Exact hypotheses and checked status | Concrete bridge |
| --- | --- | --- | --- |
| The product of the two possible y-branch evaluations equals the quadratic norm `a²+abx+b²z` | `TranslationBlockNorm.conjugate_product` | Arbitrary field, characteristic two, and curve equation `y²+xy=z`; checked with Lean 4.34.1 | The Sage quotient algebra uses `Y²=XY+X³+1`; the independent integer-field audit evaluates both signs for each tested x-root. |
| A nonzero norm excludes both y branches | `TranslationBlockNorm.norm_nonzero_excludes_branches` | Same field/curve hypotheses plus nonzero norm; checked | For every tested block root, the independent audit compares this sign-product zero condition with direct group subtraction and source-product membership. |
| A Bézout certificate evaluated at a source x-root excludes both signs | `TranslationBlockNorm.bezout_rejects_both_branches` | Same field/curve hypotheses, `f(x)=0`, and the evaluated identity `u f+v N=1`; checked | Sage computes `gcd(f,N)=1`, which yields the polynomial Bézout identity. The integer-field auditor confirms the resulting zero set for all 18 tested blocks. |

The readable proof uses the identities

`(a+bY)(a+b(Y+X)) = a²+abX+b²(Y²+XY)`

and, for `gcd(f,N)=1`, a Bézout relation `U f+V N=1`. At a source root of
`f`, the latter makes `N` nonzero. The first identity then makes both
possible signed evaluations nonzero. Because every genuine second source
product lies in the rotated product subspace and vanishes under its
linearized annihilator, rejecting a block at gcd one preserves every
genuine decomposition. Denominator or zero-output exceptional roots
require direct fallback; the tested blocks encountered neither case.

`lean-toolchain` pins `leanprover/lean4:v4.34.1`; `lean QuadraticNorm.lean`
built the actual module. `lean.stdout` records `#print axioms` for all three
declarations: only standard `propext`, `Classical.choice`, and `Quot.sound`.
No `sorry`, `admit`, custom research axiom, or unchecked native evaluation
appears in the final module. `lean4checker --fresh` was unavailable on
this host. `QuadraticNorm_v1.lean` and `lean_v1.stdout` preserve the first
failed proof attempt.

The complete concrete theorem connecting the compiled Sage quotient-ring
operations, the elliptic translation formula, and polynomial GCD to all
N41 source blocks is not formalized in Lean. The 18 finite instances are
independently replayed by `audit_integer.py` with separate field and group
arithmetic. The remaining formal bridge would define the quotient
coordinate algebra and prove evaluation commutes with its arithmetic and
the specialization of `gcd(f,N)=1` to a Bézout certificate.
