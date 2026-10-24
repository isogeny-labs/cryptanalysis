# Proof map

## Generic certificate implication

`MacaulayBlockSound.constant_one_block_certificate_sound` in
`MacaulayBlockSound.lean` states: for any commutative ring with `1 ≠ 0`,
any assignment space, any family of original equations, and any list of
equation times monomial rows, an identity in which those rows sum to one
rules out every common zero of the original equations. The monomial
may have any degree and may be any assignment-dependent multiplier.
The proof does not assume any property of the concrete curve or field.

Pinned toolchain: `leanprover/lean4:v4.34.1` in `lean-toolchain`.
Build command in this directory: `lean MacaulayBlockSound.lean`.
`lean_check.txt` records the `#print axioms` output. It lists only
`propext`, `Classical.choice`, and `Quot.sound`. The module contains no
`sorry`, `admit`, `sorryAx`, custom research axiom, or native proof
evaluation. `lean4checker --fresh` was unavailable on this host.

## Concrete N41 bridge

The field is `GF(2)[u]/(u^41+u^3+1)` and the curve ID is
`EC1N41Ckb1h7d5e80d3c4d0`. Source products for the two remaining
pair families are binary-linear in ten canonical bits per family and
use Frobenius rotations 12 and 24. The 13-term resultant coefficients
and complete source-valid code census are frozen in the prior N41
resultant experiment. The present producer expands that polynomial
into its Boolean algebraic normal form, restricts first-code bits to
the frozen blocks, and constructs degree-bounded Macaulay matrices.

For each public residual block that yielded a constant-one row
combination, `audit_blocks.py` independently evaluates the **original
13-term field resultant** and the saved row combination on every raw
code assignment in the block. It checks that the identity equals one
pointwise, including source-invalid assignments. In the width-four
block this is all 16,384 raw assignments. This establishes the concrete
field-polynomial identity and its no-root consequence without trusting
the producer's Boolean expansion or row-reduction implementation.

The computational bridge is exhaustive for the declared finite blocks,
but it is not itself a kernel-checked Lean theorem about the concrete
field implementation, curve points, or all 25 residuals. The source
field embedding, point-sum witness, and source-valid code count come
from the independently archived N41 source/resultant audits. A full
concrete Lean bit-vector formalization remains open.

## Absence of a low-degree certificate

`run.py` recorded full row rank and no constant-one combination for
both unrestricted 20-bit product families at degrees 4, 5, and 6.
This is a measured finite-matrix outcome, not a theorem that the
public system has a field root or that higher-degree certificates do
not exist. The frozen prior census independently finds no
source-valid code-pair root on the public residual.
