# Proof map for the prospective preparation gate

| Reported statement | Lean declaration | Exact scope | Verification |
| --- | --- | --- | --- |
| Four rows per productive query require at least 1,098 productive queries to reach 4,390 rows | `first_rank_check_needs_1098_productive_queries` | Closed Nat inequalities `4*1097<4390` and `4390≤4*1098` | `lean FutilityArithmetic.lean` passed under pinned Lean 4.35.0; `#print axioms` reported none |
| The zero-success likelihood at the minimum rate over 23 future queries is below 1/20 | `prospective_zero_tail_below_five_percent` | Closed Nat inequality `20*7094^23<8192^23`, equivalent by positive-denominator division | Same checked build and axiom audit |

The probability statement additionally assumes independent Bernoulli future
query outcomes with a common productive probability and uses the monotonicity
of `(1-p)^23` for `p≥1098/8192`. This statistical bridge is stated in the
result note and is not formalized as a theorem about the deterministic solver
run. The Lean module proves the exact arithmetic threshold; it does not
establish the sampling assumption. No `sorry`, `admit`, custom axiom, or
native-evaluation bypass appears in the module. `lean4checker --fresh` was
unavailable on this host.
