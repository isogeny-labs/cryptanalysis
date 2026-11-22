# Quadratic feature span proof map

Let \(\phi(x)\) contain the constant bit, the 131 coordinate bits of \(x\),
and all \(x_i x_j\) for \(i<j\), in the order fixed by `protocol.json`.
The feature dimension is \(1+131+\binom{131}{2}=8647\). Every Boolean
polynomial of algebraic degree at most two in the output coordinate bits has
the form \(c\cdot\phi(x)\) over \(\mathbb F_2\), because \(x_i^2=x_i\).

For any collection of feature rows spanning \(\mathbb F_2^{8647}\), a
linear functional that vanishes on every row vanishes on every basis vector;
its coefficient vector is therefore zero. The same implication applies to
the translated rows \(\phi(x(T_j-S))\) for each fixed public-point lift
\(T_j\). A full-rank **subset** suffices: every sampled sum \(S\) belongs to
the exact signed Q1358 pair domain.

| Mathematical step | Lean declaration | Status and hypotheses |
| --- | --- | --- |
| Feature count | `QuadraticSpan.feature_dimension` | Checked, exact 131-bit degree-2 count. |
| A linear functional zero on generators is zero on their XOR span | `QuadraticSpan.annihilator_zero_on_span` | Checked; assumes XOR additivity, zero preservation, and zero on the supplied rows. |
| A full 8647-bit span excludes a nonzero annihilator | `QuadraticSpan.full_quadratic_rank_excludes_annihilator` | Checked; assumes every 8647-bit vector lies in the row XOR span. |
| Q1358 pair sums and four target-translated rank certificates | `run_sage.py`, `audit_sage.py`, `translated_extend_sage.py`, `translated_audit_sage.py` | External exact arithmetic and two opposite-pivot replays, not encoded as a Lean term. |

The Lean theorem formalizes the structural implication. The concrete
8647-row rank certificate and its connection to the field/curve coordinates
remain external replay evidence; thus formalization of the full instance
specific statement is partial. The remaining bridge is to import the
8647-by-8647 Boolean matrices, prove each row equals its field/curve feature
encoding, and kernel-check their elimination or inverse certificates in Lean.

Build command from this directory: `lean QuadraticSpan.lean > lean_check.log 2>&1`.
The pinned toolchain is Lean 4.34.1. `#print axioms` reports no axioms for
the dimension identity and only standard `propext` and `Quot.sound` for the
two span theorems. No `sorry`, `admit`, custom claim axiom, or native evaluation
is used. `lean4checker --fresh` was unavailable on this host.
