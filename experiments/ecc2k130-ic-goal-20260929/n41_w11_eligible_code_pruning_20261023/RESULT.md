# Exact eligible-code clauses and frozen N41 orientation sweeps

An exact source-code domain check removed 743 ineligible ten-bit values per pair slot before four-pair SAT search. The resulting 2,972 clauses preserve all 32 independently replayed public relations in the N41 W11 census. Lean 4.34.1 proves that the mismatch clauses accept exactly the listed eligible codes for all four slots. Under matched, predeclared 41-orientation schedules, both the original and domain-pruned circuits exhausted their solver budgets without a SAT model. This establishes correctness of the pruning layer on the frozen source while showing that this particular clause layer did not clear the N41 search gate.

## Instance and method

The field is `GF(2)[u]/(u^41+u^3+1)`, with `y²+xy=x³+1`, subgroup order `549756390943`, cofactor four, and curve ID `EC1N41Ckb1h7d5e80d3c4d0`. The public raw point is `(1936680952394, 910597499030)`. The W11 source has 281 eligible ten-bit codes, 1,124 distinct subgroup-usable points, and 557 folded columns. Four pair slots use rotations `[0,12,24,36]`. The archived independent group census has 32 distinct-column relations across 23 of 41 Frobenius orientations.

The baseline used the archived exact `orbit41.xcnf` circuit. Both schedules fixed its six selector bits successively to orientations `0..40`, with 13 seconds of CryptoMiniSat 5.14.7 per orientation, one solver thread, a 590-second global parent cap, and a 4 GiB sampled combined RSS cap. The first schedule attempt stopped after two slices because its RSS monitor interpreted a child-exit race as `MONITOR_FAILURE`. The corrected baseline reran all 41 orientations from zero. The revised circuit appended a ten-literal exclusion clause for each of the 743 code values outside the 281-code source set, separately in each of four slots; its solver schedule was otherwise identical. Both formulas were regenerated and hash-checked against their frozen protocols. Each slice used the same public target point; no witness orientation or code was pinned.

An exhaustive `FixedSeed.source_valid` evaluation for all 1,024 ten-bit codes matched the archived 281-code source list exactly. The 32 independently replayed census witnesses use only those codes. For a forbidden code `c`, the generated clause is the disjunction of ten bit mismatches against `c`; it is false precisely on `c`. The Lean proof map below gives the general equivalence for all four source slots. The pruned formula has 16,224 variables, 43,782 CNF clauses, and 2,342 native XOR rows, compared with 40,810 CNF clauses in the baseline.

| Frozen one-worker N41 diagnostic | Corrected orientation baseline | Eligible-code clauses |
| --- | ---: | ---: |
| Orientations attempted | 41 | 41 |
| Solver model returned | 0 | 0 |
| `BOUNDED_UNKNOWN` slices | 15 | 31 |
| Parent `ORIENTATION_WALL_CAP` slices | 26 | 10 |
| Schedule wall, seconds | 550.944 | 547.650 |
| Sampled peak combined RSS, bytes | 391,446,528 | 556,630,016 |
| Source-code values excluded per slot | 0 explicit | 743 explicit |
| Added CNF clauses | 0 | 2,972 |

The terminal solver outputs in bounded slices are `INDETERMINATE`; parent-capped slices have no terminal SAT or UNSAT assertion. Both rows have `candidate_id: null` because the measured component does not specify and execute a complete IC pipeline. Formula generation and the pre-run source checks are outside the reported schedule wall, so these numbers are solver-stage diagnostics, not single-target online IC times. The runs used an ordinary host and are not CPU-isolation-tier speedup measurements. The small difference in two capped schedule totals does not estimate solved-instance speed.

The first two-slice attempt has status `MONITOR_FAILURE` and is retained in `../n41_w11_orbit_schedule_20261023`. The corrected baseline is in `../n41_w11_orbit_schedule_r2_20261023`. `python3 verify.py <run-directory>` checked both of those archives and this directory: frozen hashes, all reconstructed orientation formulas, compressed solver transcript hashes, terminal-status flags, and slice order. The Lean command `lean EligibleCodeClauses.lean` exited zero; its axiom audit reports only `propext`, `Classical.choice`, and `Quot.sound`. `lean4checker --fresh` was unavailable on this host.

The next search change should enforce an exact **target-conditioned constraint on multiple free source-code families** before expanding S3 roots. A candidate rule should be tested against every one of the 32 census relations and every orientation, report the number of families rejected and cost per rejection, and beat the 38.246-second exact N41 group join on the same public point before an N131 public query. Explicit enumeration of ineligible codes scales as `2^w` and is therefore not the N131 construction. The N131 one-worker 600-second/4-GiB ordinary-relation gate, then useful rank, factor-base logs, unseen target recovery, and same-point rho comparison remain the active goal stages.

## Reproduction

The frozen protocol and runner are [protocol.json](protocol.json) and [schedule.py](schedule.py); [result.json](result.json) retains all 41 statuses. Compressed `orientation_XX.stdout.gz` and `.stderr.gz` files retain each solver transcript. Run `python3 verify.py .` for this archive and `python3 verify.py ../n41_w11_orbit_schedule_r2_20261023` for the baseline. The precise proof statements and assumptions are in [PROOF_MAP.md](PROOF_MAP.md).
