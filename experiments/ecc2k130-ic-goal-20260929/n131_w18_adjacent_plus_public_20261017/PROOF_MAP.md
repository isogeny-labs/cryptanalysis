# Plus-only adjacent proof map

The source gate restricts the repeated edge to the same signed pair
point (P) in slots 0 and 1, with the second slot applying Frobenius
τ. The first internal point is therefore (P+τ P). For
(a=1/x(P)) and nonexceptional (P), the exact reciprocal-coordinate
equation is

\[
  w(1+a^2)=a,\qquad w=1/x(P+τ P).
\]

The [adjacent source proof](../n41_n131_adjacent_frob_leaf_20261017/PROOF_MAP.md)
derives (x(P+τ P)=x+1/x) by clearing the binary-curve addition
law and proves the central polynomial identity in Lean. The
[two-branch proof](../n131_w18_adjacent_public_20261017/PROOF_MAP.md)
formally verifies that setting its sign wire to zero gives precisely
the plus-only equation. The current [source gate](gate_result.json)
checks the independent N41 public relation's repeated edge and
matching sign bits, and binds the N131 66,382-output source count.

| Result | Lean declaration | Exact scope | Status |
| --- | --- | --- | --- |
| Cleared binary-curve identity modulo two | `Adjacent.adjacent_polynomial_identity`, `Adjacent.adjacent_parity` | Integer-polynomial identity and parity implication | Built in prior source package, Lean 4.34.1 |
| Plus-branch substitution | `AdjacentLeaf.plus_branch` | Integer-polynomial branch equation | Built in prior two-branch package, Lean 4.34.1 |
| N131 point-to-bit circuit bridge | No declaration yet | Actual GF(2^131) point law, source signs, full target selector | Partial formalization; independent Sage control and complete Boolean assignment checked |

Both referenced modules include `lean-toolchain`, build stdout, and
`#print axioms` transcripts. The gap to a full formal theorem is the
extension-field curve/group representation and the bit-circuit
semantics, not the polynomial branch substitution. Exact hypotheses,
including nonexceptional coordinates and matching source signs, are
retained here and in the frozen protocol.
