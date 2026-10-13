# Direct linked-pair addition gate on N131

**The direct characteristic-two addition gate reduces the frozen N131 ten-pair circuit from 1,998,046 to 609,681 clauses while preserving a complete constructed witness.** It replaces the 33,191-code signature lookup with five field products and linear Frobenius/halftrace maps. The same W18 seed-212 source, ten-pair tree, 18 folded-column requirement, and 524-choice target fiber remain in the circuit. The [stage](stage_result.json) and [full control](direct_control_result.json) are frozen under separate protocols.

## Algebra and circuit

Write the first pair output as `a=1/x`, let `X=x^(2^16)`, and take `h=HT(x+a²)`, `y=xh`, `Y=y^(2^16)`. The circuit enforces `ax=1` and `h²+h=x+a²`; the latter is the binary-curve lift condition for `y²+xy=x³+1`. Put `d=x+X` and `s=y+Y`. For `d≠0`, the binary-curve addition law gives

`x(P+τ^16P) = (d³+s²+sd)/d²`.

If `u` is the first subtotal reciprocal, the gate requires `u(d³+s²+sd)=d²` and `d≠0`. This selects the linked plus sum directly. Simultaneous negation of `P` and `τ^16P` leaves its x-coordinate unchanged, so the halftrace choice of `y` does not restrict that sum. The checked [Lean lemma](ClearedAddition.lean) establishes the reciprocal implication from the cleared equation and field inverse law; [PROOF_MAP.md](PROOF_MAP.md) gives its exact scope and the open concrete curve formalization.

The preceding [all-root Sage audit](../n131_w18_linked_signature_prefix_20261012/fast_audit_result.json) replayed both signs and both addition outcomes for all 66,382 pair-output roots of this exact source. The direct gate's [complete constructed assignment](direct_control_result.json) satisfies every CNF clause and native-XOR row, including the new inverse witness and addition equation.

## Frozen stage comparison

| Circuit on the same constructed N131 target | Variables | AND gates | Clauses | Native XOR rows |
| --- | ---: | ---: | ---: | ---: |
| 14-bit source-table signature | 438,380 | 352,551 | 1,998,046 | 80,810 |
| Direct linked addition | 304,057 | 199,414 | 609,681 | 99,493 |

The direct gate has 69.5% fewer clauses, 43.4% fewer AND gates, and 23.1% more native XOR rows. These are exact construction counts; build wall times on this shared host are exploratory. The current experiment has `candidate_id: null` because the complete IC pipeline and final target recovery are not specified by this gate alone.

## Public query and next falsifier

The [public protocol](public_protocol.json) froze one worker, point `[1052727368764798954359115163823647684025, 2071227447786120917960296877345506689833]`, workload `cc09e7eb202a`, a 600-second target-dependent cap, and a 4-GiB combined RSS cap. The public formula had 304,072 variables, 609,693 clauses, 99,504 native XOR rows, and 18,387,022 bytes. The [query receipt](query_result.json) records `BOUNDED_UNKNOWN` at `600.062751625` seconds, `TOTAL_QUERY_TIMEOUT`, solver exit `-9`, no terminal SAT/UNSAT line, and peak sampled combined RSS of `343490560` bytes. The [independent terminal audit](query_audit_result.json) rebuilt the formula byte for byte. Both XCNFs are exactly recoverable from the [compressed archive receipt](archive_result.json); the [read-only verifier](verify.py) checks their hashes, protocols, logs, and proof output.

| Exclusive target-dependent phase | Nanoseconds |
| --- | ---: |
| Target orbit and fibers | 1,613,010,250 |
| Formula construction | 57,233,062,667 |
| Formula serialization | 22,697,833 |
| Solver search to cap | 541,192,432,083 |
| Terminal parsing | 1,548,792 |

The circuit reduction reached the solver but the single public search remained bounded at this cap. Its wall times are exploratory on a contended host. The next cheapest falsifier is a frozen paired N41 run of the same direct equation against the prior signature gate, with an unpinned ordinary query and complete signed group replay; if it yields a verified rank-increasing row, test whether target-conditioned constraints can force earlier propagation on the N131 tree before another capped run.
