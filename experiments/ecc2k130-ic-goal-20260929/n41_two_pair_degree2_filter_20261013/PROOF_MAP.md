# Proof map: degree-two residual filter gate

| Result | Evidence | Assumptions and status |
| --- | --- | --- |
| `Tr(a²+a)=0` for an additive binary trace invariant under squaring | `TraceGate.trace_artin_schreier` in [TraceGate.lean](TraceGate.lean) | Abstract additive field and trace laws; Lean 4.34.1 checked with no axioms. |
| Every point in a double-surjective group has trace-zero `x` when doubling has `x(2P)=λ²+λ` | `TraceGate.subgroup_x_trace_zero` | Explicit double-surjectivity, curve doubling, and trace laws; Lean checked with no axioms. For the concrete odd-order N41 subgroup and Koblitz model, the mathematical bridge is written in [RESULT.md](RESULT.md); the full curve and field objects are not formalized in Lean. |
| In the frozen N41 polynomial basis, `Tr(x)` is the constant coefficient | [checked Sage audit](audit_result.json) | All 41 basis elements tested, with only basis index zero having trace one. Concrete field bridge remains outside Lean. |
| Degree-two functions on the trace-zero hyperplane have dimension 821 | `1 + 40 + binom(40,2) = 821` and squarefree ANF monomials | Elementary Boolean ANF argument in [RESULT.md](RESULT.md). Not formalized in Lean. |
| Two-pair output feature vectors span that entire 821-dimensional restriction space | 821 pivot [witnesses](witnesses.tsv), [independent Sage replay](audit_result.json), and [read-only verifier](verify.py) | Exact audited W8 source, fourfold projected pair sums, and four distinct folded columns per two-pair output. Native sample cap 20,000; all 821 selected rows verified. The finite rank certificate is checked computationally; a kernel-checked finite matrix proof remains open. |

Build with `lean TraceGate.lean` from this directory. The [toolchain](lean-toolchain), [runtime](lean_runtime.txt), and [axiom output](lean_check.txt) pin this conditional formalization. `lean4checker --fresh` was unavailable on this host. The fully concrete N41 theorem would require formal definitions and verified bridges for the field, curve, subgroup, and 821-row rank certificate.
