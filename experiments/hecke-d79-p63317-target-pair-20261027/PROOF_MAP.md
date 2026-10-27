# Proof map

| Result | Lean declaration | Exact scope and status |
| --- | --- | --- |
| 40 distinct nonzero projected class logs, closed under negation | `FiniteCoverage.log_count`, `logs_distinct`, `logs_nonzero`, `negation_closed` | Checks the pinned 40-entry list modulo 2531; kernel checked |
| 820 unordered sum patterns and 689 distinct outcomes | `FiniteCoverage.unordered_pattern_count`, `distinct_coverage` | Computes all `i≤j` sums from the exact log list; kernel checked |
| Frozen fixture scalar 973 absent from the unordered sumset | `FiniteCoverage.frozen_target_absent` | Checks membership from the same generated sum list; kernel checked |

The written proof that the signed distinct-source index equals the unordered sumset uses `−S=S` and `0∉S`. Every signed term is in `S`, giving signed-index coverage contained in `S+S`. For any `s+t∈S+S` with distinct source indices, signs `+,+` yield it. If the same source represents both terms, then `s=t`; its distinct negative partner exists because the 40 values are distinct, negation closed and nonzero in odd characteristic, and the signed pair `s−(−s)` yields `2s`. Thus coverage is exactly `S+S`, with at most 820 unordered index pairs.

The Lean module proves the finite log-list properties, exact sum count and frozen-target absence. Full formalization remains **partial**: the abstract signed-index/sumset equivalence and the concrete elliptic-curve-to-log mapping are not yet Lean declarations. They are established by the readable argument and independently checked in `sumset_audit.py` and `audit_sage.py`. The finite Lean proofs contain no `sorry`, `admit`, `sorryAx`, custom research axioms or native-evaluation bypasses.

The toolchain is pinned to `leanprover/lean4:v4.35.0-rc4` with no external dependencies. Run `cd formal && lake build`. The build output records `#print axioms` for each theorem. `lean4checker --fresh` was unavailable on this host.
