# Proof map

For the exact valid second-code set `Q`, partition it into ordered blocks
`Q_b`. Each block norm is `N_b(X)=∏_{q∈Q_b}F_T(X,q)`. The inherited
checked theorem `JointNorm.product_zero_iff` establishes, under field
no-zero-divisor assumptions, that `N_b(p)=0` iff some factor in the
block vanishes at `p`. The new declaration
`BlockUnion.zero_iff_some_block_zero` in [`BlockUnion.lean`](BlockUnion.lean)
proves that a source factor zero is equivalent to a zero in some block
norm whenever the blocks cover exactly the source. The theorem is
checked with Lean 4.34.1 and `#print axioms` reports none.

The readable polynomial argument adds the first-code vanisher
`A(X)=∏_{p∈P}(X+p)`. Because source products are distinct, the roots of
`gcd(A,N_b)` are precisely the valid first products with a resultant
zero in block `b`. The implementation independently localizes each GCD
root to the exact source code and re-evaluates the corresponding quartics.

The bridge from NTL `GF2EX` operations to the concrete polynomial
identities and the exhaustive W20 source-code table remains
computational. The frozen 4,096-code block results agree with both the
single dense NTL norm and an independent complete pair scan. The
full-source constructed row has 33 recorded block completions. The
full-source public row has only capped partial coverage; its unvisited
blocks retain unknown status.

Pinned toolchain: `leanprover/lean4:v4.34.1` in `lean-toolchain`.
Build command: `lean BlockUnion.lean > lean_check.log 2>&1` from this
directory. `lean4checker --fresh` was unavailable locally.
