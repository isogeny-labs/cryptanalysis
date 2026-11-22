# Exact distinct-column constraints for the nine-pair N131 orbit search

The N131 nine-pair SAT source now enforces the **same 18-distinct-column
condition used in its exact source census**. Every pair of the nine slots
must choose different source codes; the frozen W18 table has only 65 pairs
of different codes whose edges still share a folded column, and both slot
orders of each conflict are forbidden. The constructed nine-pair witness
continues to satisfy the complete XCNF. An ordinary query on the same
previously published public point entered CryptoMiniSat search and ended
`BOUNDED_UNKNOWN` at the 600-second target-dependent wall cap.

The exact field is `GF(2)[t]/(t^131+t^13+t²+t+1)` on
`y²+xy=x³+1`, curve `EC1N131Ckb1heb5f1998f20b`, subgroup order
`680564733841876926932320129493409985129`, cofactor four. The public
workload `cc09e7eb202a` and all 524 raw-fiber/Frobenius target choices are
identical to the [unshielded baseline](../n131_w18_ninepair_orbit_20261012/RESULT.md).
All nine W18 seed-212 pair selectors remain free. The [proof map](PROOF_MAP.md)
ties this finite conflict rule to the generic Lean-checked matching theorem;
the [source audit](shield_audit_result.json) reconstructs the 33,191 code
edges from the frozen support table, checks the 65 conflicts against the
degree-two matching coefficient, and checks the XCNF deltas.

| Exact formula measure | Unshielded | Distinct-column shield | Change |
| --- | ---: | ---: | ---: |
| Variables | 510,022 | 510,634 | +612 |
| AND gates | 221,160 | 221,160 | 0 |
| CNF clauses | 802,767 | 807,483 | +4,716 |
| Native-XOR rows | 286,081 | 286,693 | +612 |
| Ordinary XCNF bytes | 24,300,760 | 25,209,604 | +908,844 |

The 36 slot pairs each add one 17-bit inequality clause and two orientation
clauses for each of 65 cross-code column conflicts: `36×(1+2×65)=4,716`
new clauses. The 17 bit differences per slot pair add `36×17=612` XOR rows.
The shield adds no nonlinear multiplication. Its constructed assignment
passes all 807,483 clauses and 286,693 native-XOR rows, with 18 distinct
folded columns. The checked-Sage audit of all 524 target choices is bound
to the same source and target in the baseline receipt. The constructed
nine-pair group sum was independently replayed in the prior nine-pair
experiment; this control reuses its frozen fixture. The shield changes
only the selector restrictions.

| Frozen ordinary-query measure | Result |
| --- | ---: |
| Target orbit/fibers / formula build / write | 0.091 / 3.265 / 0.028 s |
| Solver search/stop / terminal parse | 596.659 / 0.0004 s |
| **All target-dependent attempt wall** | **600.043 s** |
| Sampled peak parent-plus-solver RSS | 566,247,424 B |
| Actual solver restart rows / terminal status lines | 2,342 / 0 |
| Exit classification | `BOUNDED_UNKNOWN`, `TOTAL_QUERY_TIMEOUT` |
| Ordinary formula SHA-256 | `a7ec05ca02e70021bec0fd4ef79a719f8276fb3f0219dd833d03936e03138140` |

The [protocol](protocol.json) freezes the same one-worker 600-second/4-GiB
resource envelope, target, source, solver, and flags as the baseline, plus
the shield source hash. The [receipt](query_result.json) preserves exclusive
phase costs. The [terminal audit](audit_result.json) rebuilds the ordinary
formula byte for byte and confirms an active search with empty stderr. The
frozen runner field `restart_rows` counts 1,550 bracketed diagnostic lines;
the audit records the 2,342 actual `c rst` rows. Both ordinary outcomes are
censored, and shared-host contention differs between runs, so these wall,
memory, and restart observations do not rank successful search cost.

The [archive receipt](archive_receipt.json) binds deterministic gzip copies
of the constructed and ordinary formulas to their raw SHA-256 hashes; run
`python3 -B ../n131_w18_ninepair_orbit_20261012/archive.py . --verify` from
this directory for a fresh byte replay. A solver model would still need
signed-point sum, inverse-Frobenius transport, folded-row rank, and scalar
replay before promotion. The next algorithmic gate is a target-derived
partial-sum proposal or rejection rule that keeps the N41 ordinary source
control and yields an independently replayed ordinary N131 relation within
the frozen envelope. `candidate_id` remains `null` while the full pipeline
and paired single-target rho metric are pending.
