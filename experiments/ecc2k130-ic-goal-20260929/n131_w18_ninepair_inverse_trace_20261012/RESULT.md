# Exact inverse-trace gates shrink the nine-pair N131 orbit circuit

Replacing the nine W18 source-support BDDs with nonzero inverse witnesses and
zero-trace tests preserves the **33,191 canonical pair codes per slot** while
reducing the balanced target circuit by **282,744 variables, 67,959 AND gates,
217,143 native-XOR rows, and 8,941,045 XCNF bytes**. The constructed
nine-pair assignment satisfies all 605,973 clauses and 69,550 XOR rows.
Independent checked Sage verifies inverse and trace identities for all 18
source endpoints and 18 distinct folded columns. The ordinary frozen-point
query entered active search and ended `BOUNDED_UNKNOWN` at its 600-second
parent cap.

## Source, target, and exact substitution

The curve is `EC1N131Ckb1heb5f1998f20b` over
`GF(2)[t]/(t^131+t^13+t²+t+1)` on `y²+xy=x³+1`, subgroup order
`680564733841876926932320129493409985129`, cofactor four. The frozen
workload `cc09e7eb202a` supplies one public point
`Q=(1052727368764798954359115163823647684025,
2071227447786120917960296877345506689833)`. Nine W18 seed-212 pair
slots remain free at rotations `0,16,...,128`; the formula selects one of
four raw preimages and 131 Frobenius conjugates. The full signed-Frobenius
factor-base closure has 34,339,816 usable points before folding and 131,068
folded columns under the preceding geometry audit. All nine slots obey the
exact 18-distinct-column shield.

For each candidate source endpoint `w`, the new gate requires an inverse
`v` with `wv=1` and `Tr(v)=0`. The prior
[rationality audit](../n131_w16_w18_sixpair_width_gate_20261010/native_audit_result.json)
checks the source table against every nonzero mask at widths 15 through 18,
and the exhaustive [gate census](../n131_w18_inverse_trace_terminal_20261011/gate_equivalence.json)
compares its canonical source set with the BDD set on all 17-bit codes.
The [constructed-control Sage check](control_gate_sage.json) independently
replays all 18 selected inverse witnesses and trace values. The earlier
[nine-pair fixture replay](../n131_fixed_seed_ninepair_cubic_20261011/sage_fixture_result.json)
checks the corresponding group sum and cofactor-four projection. The
[proof map](PROOF_MAP.md) connects exact gate substitution to a checked Lean
theorem and records the remaining concrete-field formalization bridge.

| Frozen formula measure | Balanced BDD | Inverse-trace | Difference |
| --- | ---: | ---: | ---: |
| Variables | 510,634 | 227,890 | −282,744 |
| AND gates | 221,160 | 153,201 | −67,959 |
| CNF clauses | 807,483 | 605,973 | −201,510 |
| Native-XOR rows | 286,693 | 69,550 | −217,143 |
| Ordinary XCNF bytes | 25,190,942 | 16,249,897 | −8,941,045 |

## Frozen ordinary-point query

The [protocol](protocol.json) binds the source and solver hashes, same-point
workload, 524 target choices, one worker, 4-GiB combined RSS cap, and
600-second total target-dependent cap before the constructed control and
ordinary query. The previous [balanced run](../n131_w18_ninepair_balanced_20261012/query_result.json)
uses the same source law, target, worker and resource envelope. Both solver
statuses are `BOUNDED_UNKNOWN`; their local CPU wall times cannot rank search
success on this contended host.

| Exclusive target-dependent phase | Inverse-trace query |
| --- | ---: |
| Target orbit and raw fibers | 0.106243 s |
| Formula construction, including source-domain loading | 3.421312 s |
| XCNF serialization | 0.013848 s |
| Solver search and stop | 596.494277 s |
| Terminal parse | 0.000773 s |
| **Total attempt wall** | **600.036453 s** |
| Sampled peak parent-plus-solver RSS | 582,975,488 B |
| Actual solver restart rows / terminal status lines | 1,950 / 0 |

The [query receipt](query_result.json) preserves every charged phase and the
`TOTAL_QUERY_TIMEOUT` stop. The [independent audit](audit_result.json)
rebuilds the ordinary XCNF byte for byte, confirms exact phase summation,
source and baseline hashes, active solver restarts, and empty stderr. The
[archive receipt](archive_receipt.json) binds deterministic gzip copies of
both formulas to their original SHA-256 hashes and byte counts; the archive
replay passes, as does `python3 -B verify.py` from this directory. The checked
[Sage runtime](sage_runtime_info.json) was saved
before the independent source-gate control. Lean 4.34.1 checks
`GateReplacement.exact_gate_substitution`; `#print axioms` reports no axioms.

This is an exact encoding and solver-stage result with `candidate_id: null`.
The next test should give this frozen formula an auditable exclusive CPU
partition under the same one-worker, 600-second wall and 4-GiB envelope,
then compare solver progress with the BDD formula under paired run order.
If both remain capped, the next algorithm change must add a target-derived
constraint on at least two unresolved partial sums and show whole-family
rejection on the existing unpinned N41 public-point control before another
N131 ordinary query. A model must pass signed-point, inverse-Frobenius,
folded-row-rank, and scalar replay before promotion to the full pipeline.
