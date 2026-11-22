# Proof map: constant-one family rejection

| Mathematical result | Lean declaration | Exact assumptions and status |
| --- | --- | --- |
| A constant-one combination of original and bit-multiplied equations rejects every simultaneous zero | `MacaulaySound.constant_one_certificate_sound` in [MacaulaySound.lean](MacaulaySound.lean) | Arbitrary type of assignments, equation indices and multiplier indices; arbitrary commutative ring with `1 ≠ 0`; a pointwise sum-of-rows identity equal to `1`. Kernel-checked under Lean 4.34.1. |
| The finite-field eliminant restricted to a linear right-product code is Boolean quadratic | Concrete expansion in [macaulay.py](macaulay.py), replayed by [audit_n41_full_sage.py](audit_n41_full_sage.py) and [audit_n131_sage_v2.py](audit_n131_sage_v2.py) | Characteristic two, the exact N41/N131 field polynomials, pinned 13-term coefficients, `q(b)=Σbᵢvᵢ`, and Boolean `bᵢ²=bᵢ`. Exact finite-instance Sage checks pass; this algebra-to-concrete-curve bridge has not been encoded as a Lean theorem. |
| Every saved certificate is a constant-one Boolean polynomial identity | 7,024 N41 and 11 N131 independent Sage replays | Applies only to the frozen rows and exact source hashes. The certificate identities are checked computationally, not imported as Lean terms; formalized finite-instance certificate checking remains open. |

## Readable proof

For any right-code assignment `b`, let `E_i(b)` be bit `i` of the field element `H_p(q(b))`. If `H_p(q(b))=0`, then `E_i(b)=0` for every `i`. A row is `E_i` or `b_j E_i`, so every row is zero at `b`. The certificate expresses the constant Boolean polynomial `1` as an XOR of selected rows. Evaluating that identity at `b` gives `1=0` in `GF(2)`, contradiction. This argument does not assume that `b` denotes a valid factor-base point; it excludes the larger Boolean cube and therefore every valid code inside it.

The quadratic expansion follows from `q=Σbᵢvᵢ`, Frobenius linearity of `q²` and `q⁴`, and `q³=q q²`; diagonal products reduce with `bᵢ²=bᵢ`. Multiplication of a quadratic coordinate equation by one bit yields degree at most three in the Boolean quotient. Row reduction acts on the exact squarefree monomial basis, so selecting source rows that XOR to constant one is an identity, not a statistical test.

## Verification boundary

`lean MacaulaySound.lean` passed with toolchain `leanprover/lean4:v4.34.1`; [lean_check.json](lean_check.json) records module and output hashes. `#print axioms MacaulaySound.constant_one_certificate_sound` reported `propext`, `Classical.choice`, and `Quot.sound`. The theorem does not assume the desired rejection conclusion. Its certificate hypothesis is the exact polynomial identity independently replayed in the finite instances. A full Lean development would define the two field representations, the source-code maps, and the 13-term eliminant, then import or verify each finite certificate as a Boolean polynomial identity. Those definitions and instance proofs remain open. `lean4checker --fresh` was unavailable on this host.
