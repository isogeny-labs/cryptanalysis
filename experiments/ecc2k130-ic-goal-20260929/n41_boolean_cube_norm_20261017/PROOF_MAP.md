# Proof map

The symbolic selector norm works in the Boolean quotient ring
`F[x₀,…,x₈]/(xᵢ²−xᵢ)`, with `F=GF(2⁴¹)` in the measured instance. Write a
polynomial as `F₀+xᵢF₁`. At selector bit zero it evaluates to `F₀`; at bit
one it evaluates to `F₀+F₁`. Its one-bit norm is therefore
`F₀(F₀+F₁)=F₀²+F₀F₁`. Repeating this identity over all nine selector bits
gives the product of all 512 evaluations. Because `F` has no zero divisors,
that product is zero exactly when at least one assignment is a root.

[`CubeNorm.lean`](CubeNorm.lean) contains two faithful structural steps:

| Mathematical result | Lean declaration and assumptions | Status |
| --- | --- | --- |
| One-bit norm expansion | `CubeNorm.one_bit_norm`; arbitrary `F` with `add`, `mul` and left distributivity, under the explicit `evalBit` chart | Lean 4.34.1 build passed |
| Recursive product zero iff some leaf zero | `CubeNorm.norm_zero_iff`; arbitrary binary evaluation tree with `mul a b=zero ↔ a=zero ∨ b=zero` | Lean 4.34.1 build passed |

The pinned toolchain is in [`lean-toolchain`](lean-toolchain). The command
`lean CubeNorm.lean` exited zero; [`lean.stdout`](lean.stdout) records
`#print axioms` for both declarations, with only the standard Lean axiom
`propext`. No `sorry`, `admit`, claim-encoding axiom, or native evaluation
appears in the module. `lean4checker --fresh` was unavailable locally.

The bridge from the actual N41 coefficient tensor to the Boolean quotient
ring, the concrete `GF(2⁴¹)` operations and all 512 source-code evaluations
is a finite computation. [`run.py`](run.py) constructs each ANF directly
from the archived tensor, checks every evaluation against independent direct
Horner evaluation and the archived value grid, and checks the final norm
against a direct 512-value product. [`audit.py`](audit.py) separately reads
the frozen grids, performs its own Boolean Möbius transform and shift/XOR
field multiplication, and replays every norm stage. A kernel-checked theorem
for that specific 512-row field certificate and the elliptic-curve source
bridge is still open; the full instance formalization is partial at those
finite-data bridges.
