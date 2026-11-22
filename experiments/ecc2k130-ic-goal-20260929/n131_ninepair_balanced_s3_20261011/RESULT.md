# Balanced S3 links preserve the exact nine-pair N131 control

A balanced eight-link S3 tree for the fixed-seed W18 nine-pair construction passes a full challenge-field assignment check and an independent checked-Sage curve replay. It keeps the nine pair-output equations, source BDDs, public target, solver, and resource cap fixed. The ordinary public-point query reached the 195-second parent cap with `BOUNDED_UNKNOWN`, so link topology alone did not clear the first N131 decomposition gate in this experiment.

The exact field is `GF(2)[t]/(t^131+t^13+t²+t+1)` and the curve is `y²+xy=x³+1`, with curve ID `EC1N131Ckb1heb5f1998f20b` and subgroup order `680564733841876926932320129493409985129`. The source uses W18, seed mask 212, 33,191 supported distinct-column unordered pair codes per slot, and nine rotations `0,16,...,128`. The workload is the same previously frozen public point `cc09e7eb202a` and raw preimage index zero used by the [serial nine-pair run](../n131_fixed_seed_ninepair_cubic_20261011/RESULT.md). The scalar sidecar is not read by either solver.

## Exact change and controls

The serial graph adds pair outputs in order. The balanced graph first combines `(0,1)`, `(2,3)`, `(4,5)`, and `(6,7)`, combines the resulting two pairs of sums, combines those two sums, then adds pair 8 to the fixed target. Every internal coordinate remains an independent 131-bit variable; each link has the same halftrace-cubic S3 equation, trace condition, nonzero-coordinate rule, and branch bit as the serial source. The [frozen protocol](protocol.json) hashes the executed source, dependency code, pair support, control fixture, solver binary, and public input before the control and ordinary query.

The [constructed control](control_result.json) satisfies all 648,289 CNF clauses and 282,138 native-XOR rows. Its group signs were reconstructed from the archived curve fixture. The [independent Sage audit](sage_audit_result.json), run after saving the [checked runtime receipt](sage_runtime_info.json), recomputes all nine rational pair outputs and seven intermediate group sums, checks all eight branch bits, and verifies the cofactor-four subgroup point. Both exact formulas are retained as deterministic gzip archives, with decompressed SHA-256 checks in the [archive receipt](archive_receipt.json).

## Paired public-point diagnostic

| Measure | Serial archived run | Balanced run |
| --- | ---: | ---: |
| Exact source and public point | W18 seed 212, `cc09e7eb202a` | same |
| Variables / AND gates | 499,736 / 215,343 | 499,736 / 215,343 |
| Clauses / native-XOR rows | 648,289 / 282,136 | 648,289 / 282,136 |
| Formula construction, local diagnostic | 4.387 s | 118.786 s |
| Solver parent wall, one worker | 195.050 s | 195.040 s |
| Last recorded restart / conflicts | 493 / about 169,000 | 44 / 10,397 |
| Free variables after simplification in last restart row | 496,193 | 497,492 |
| Sampled combined peak RSS | 683,196,416 B | 429,260,800 B |
| Query status | `BOUNDED_UNKNOWN` | `BOUNDED_UNKNOWN` |

The serial run is an archived comparator, not a same-session isolated CPU timing pair. Construction time changed sharply under host contention, and CryptoMiniSat selected different branch modes. The conflict and restart counts are therefore search diagnostics, not a controlled speedup ratio. Neither trace has a terminal SAT or UNSAT line; both stderr files are empty. The [balanced query receipt](query_result.json) preserves the source-bound formula counts, solver flags, parent cap, worker count, wall, memory, exit code, and hashes of both traces. It emitted no model for group replay. The result remains `candidate_id: null` because factor-log preparation, final relation linear algebra, target recovery, and matched rho have not been specified or measured for this proposal.

The equal AND count shows the balanced tree did not remove the pair-product or S3 multiplication work, while its solver simplification left 1,299 more free variables at the last recorded restart. The next N131 method should propose pair outputs from the fixed public point before opening the 17-bit source selector families. The existing 61-column adjacent-window output inverse can check such proposals, but a target-conditioned upper-chain generator and a frozen source-bound cost estimate are needed before another ordinary query.
