# One-root norm elimination on the frozen N131 public point

The one-root norm eliminates one right-pair reciprocal root from the W29
five-pair circuit while keeping the other root explicit. Its characteristic-two
identity is checked in Lean 4.34.1, and independent Sage evaluation agrees
with the two-root S3 product in all 78,670 usable N41 root cases. The N131
constructed control satisfies the circuit and the independent group replay.
The frozen ordinary public query reached `BOUNDED_UNKNOWN` at its 600-second
wall cap with one solver worker and a 4 GiB sampled RSS stop.

## Equation and proof map

For normalized split pair quadratics
`z²+αz+β=0` and `w²+γw+β=0`, and specified right partial-sum reciprocal `t`,
put `A=t²αγ+t`, `B=α(1+t²β)`, `D=γ(1+t²β)`, `E=t²(β²+1)`,
`M=Az+D`, and `N=Bz+E`. The new constraint is

`N²+γNM+βM²=0`.

The [Lean module](OneRootNorm.lean) proves
`norm_eq_two_f3`: this norm equals `F(z,w,t)F(z,w+γ,t)` under the two
quadratic equations in any characteristic-two field. It proves
`norm_zero_iff_one_f3`: zero is equivalent to one of those two S3 equations.
The result covers repeated roots and `M=0`; no root-dependent division is
used. The module imports the pinned copy of
[PairResultant.lean](PairResultant.lean), which proves the S3 bilinear
reduction. The actual theorem modules built with `LEAN_PATH=. lean -o
PairResultant.olean PairResultant.lean` and `LEAN_PATH=. lean -o
OneRootNorm.olean OneRootNorm.lean`; [lean.stdout](lean.stdout) reports only
`propext`, `Classical.choice`, and `Quot.sound` for both new declarations.
`lean4checker --fresh` was unavailable on this host. The bridge from the
fixed-seed quadratic and S3 equations to the curve group law remains the
independent Sage group replay in the source control evidence.

The [independent Sage audit](audit_result.json) compared full field values
of the norm and the two S3 factors for both first-pair roots across all
39,335 usable N41 code pairs. Its sole accepted code pair is `(425,527)`,
with the accepted first root encoded as `55981718712`. It also checked the
Frobenius-rotated N131 right-pair quadratics, the constructed residual group
sum, and norm zero. The first audit attempt completed the N41 arithmetic
but stopped at a Python list/hash summary error before the N131 check;
[its failure receipt](audit_first_attempt_failure.json) and v1 protocol are
retained beside the corrected v2 audit.

## Measured circuit and ordinary query

| Frozen N131 public-point circuit | Original triple-plus-pair | Two-root resultant | One-root norm |
| --- | ---: | ---: | ---: |
| Clauses | 266,665 | 439,353 | 345,459 |
| Native XOR rows | 41,826 | 75,456 | 58,438 |
| Formula bytes | 18,008,905 | 23,053,626 | 20,417,726 |
| Constructed control | passed | passed | passed |
| Ordinary-query status | `BOUNDED_UNKNOWN` | `BOUNDED_UNKNOWN` | `BOUNDED_UNKNOWN` |
| Parent query wall | 600.051 s | 600.018 s | 600.035 s |
| Sampled peak combined RSS | 645,496,832 B | 619,347,968 B | 529,399,808 B |
| Last reported conflicts | 4.716 M | 4.606 M | 3.836 M |

The one-root circuit removes 93,894 clauses and 17,018 XOR rows relative
to the full resultant, while adding 78,794 clauses and 16,612 XOR rows
relative to the original. All three public queries remain wall-capped, so
conflict counts and memory are diagnostics rather than a solved-time
ranking. The eliminated root's trace is existential; the former ten-output
trace parity row is absent. Any SAT model needs full group-law decoding and
verification before it is accepted as a relation.

The [constructed build](build_result.json), [public build](public_build_result.json),
[frozen query](query_protocol.json), and [terminal query](query_result.json)
bind source hashes, point, solver, limits, formula digest, and output digest.
The [terminal audit](terminal_audit.json) rechecks both variants' source
pins, circuit hashes, solver-output hashes, cap receipts, independent field
audit, and proof outputs.
The first constructed build had a generic resultant status string; its v1
protocol and result are preserved. The v2 run uses the specific one-root
status. `candidate_id` is `null` while ordinary relation recovery and the
rest of the IC pipeline remain open.

The next experiment should change relation search rather than add a larger
global field equation: use the N41 ordinary control to measure how many
Frobenius-quotiented partial-sum families an exact target-conditioned join
rejects before materializing combinations, then freeze an N131 attempt only
if the measured pruning and memory envelope justify it. Include all source
and target-index construction in the charged stage record.
