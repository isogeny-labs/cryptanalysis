# Proof map: cubic residual-output filter class

| Result | Evidence | Status and missing bridge |
| --- | --- | --- |
| Every (x)-coordinate in the odd-order N41 subgroup has zero absolute trace | `TraceGate.subgroup_x_trace_zero` in the [preceding checked Lean module](../n41_two_pair_degree2_filter_20261013/TraceGate.lean), and its [proof map](../n41_two_pair_degree2_filter_20261013/PROOF_MAP.md) | Lean proves the conditional doubling/trace implication with no axioms. Concrete curve and field bridges remain outside Lean; checked Sage validates the 41 basis traces and 128 subgroup multiples here. |
| The trace-zero hyperplane has 40 free coordinate bits and its squarefree ANF monomials of degree at most three number `1+40+780+9880=10701` | Written counting argument in [RESULT.md](RESULT.md) | Elementary ANF dimension. Not yet formalized in Lean. |
| The legitimate two-pair output sample spans all 10,701 cubic evaluation coordinates on that hyperplane | [pivot certificate](witnesses.tsv), [independent checked-Sage rank and group replay](audit_result.json), [read-only receipt check](verify.py) | All 10,701 pivot outputs are reconstructed from 15,405 audited source states. Finite rank is computationally checked; a kernel-checked 10,701-row matrix certificate remains open. |
| Every cubic (x)-only polynomial accepting all legitimate two-pair outputs accepts all subgroup residuals | Full-rank linear algebra and subgroup trace property | Written proof in [RESULT.md](RESULT.md). Its faithful Lean formalization requires the concrete rank and field/curve bridges above; the complete theorem remains open in Lean. |

The [Sage runtime receipt](sage_runtime_info.json) pins the checked repository launcher. The independent audit protocol was frozen before execution. The prior Lean module pins Lean 4.34.1 and includes `#print axioms`; `lean4checker --fresh` was unavailable on this host.
