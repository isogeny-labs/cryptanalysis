# Six-pair shared-inverse circuit and exact public-point join

**An exact target-conditioned three-plus-three join found a six-pair relation on the frozen N41 public point.** Independent checked Sage reconstructed all twelve signed source points from the field and curve definitions, verified twelve distinct folded columns, summed the six pairs to raw point `(2026560328086,1928332930914)`, and checked that cofactor-four projection equals subgroup point `(1654986373106,1310318707590)`. The [relation certificate](join_audit_result.json) records the six state IDs, masks, signs, columns, pair sums, and input hashes.

The [monitored native join](join_result.json) completed in **6.927 s**, with 247,955,456 bytes sampled peak combined RSS. Its left table held 3,750,144 internally column-disjoint triples, compared with 4,096,000 unrestricted triples. The public target supplied the exact lookup key `Q-R` for each right triple. A hit appeared after 1,100,323 right probes; the first accepted hit had twelve distinct columns. These are ordinary-host search diagnostics on the archived N41 public target, with `candidate_id: null`.

## Matched six-pair circuit measurement

The shared-inverse circuit represents each fixed-seed source pair `a,b=a+s` with one witness `v=(ab)^(-1)`. Its linearized product equation and two trace equations replace separate endpoint inverses. Both versions use the same six rotations `(0,6,12,18,24,30)`, five S3 links, public raw target, 40 permitted canonical pair codes per slot, and cross-slot folded-column exclusions. Constructed full assignments passed every CNF clause and native XOR row for both builds; [Sage replay](audit_result.json) independently checked the constructed six-pair curve sum.

| Same-topology N41 circuit | AND gates | Variables | CNF clauses | Public XOR rows |
| --- | ---: | ---: | ---: | ---: |
| Two endpoint inverses | 28,659 | 33,561 | 88,369 | 3,749 |
| Shared product inverse | **26,937** | **31,533** | **82,957** | **3,689** |

The shared design saves **1,722 AND gates (6.0%)** and 2,028 variables in the complete six-pair circuit. The [matched baseline control](two_inverse_check_result.json) and [shared control](build_result.json) record the two assignment checks. The [frozen public SAT query](public_result.json) returned `BOUNDED_UNKNOWN`: one CryptoMiniSat worker reached the 185 s parent wall cap, with 205,340,672 bytes sampled peak combined RSS and no terminal SAT/UNSAT line. This status is a capped search observation; the independently verified group join supplies the relation.

## Instance and scaling gate

The field is `GF(2)[t]/(t^41+t^3+1)` and the curve is `y²+xy=x³+1`, curve ID `EC1N41Ckb1h7d5e80d3c4d0`. Each of six slots has 160 signed pair states from 40 seed-56 edges. The raw public target is the archived seven-pair positive-control target; its six-pair relation was not supplied to either unpinned search. The [SAT protocol](protocol.json) and [join protocol](join_protocol.json) freeze sources, geometry, inputs, binaries, target, worker count, and caps. The checked [Sage runtime](sage_runtime_info.json) belongs to both independent audits. The join's 6.927 s includes its native input read and left-table construction; this ordinary-host timing is not a complete one-target IC or paired-rho measurement.

For the frozen N131 W23 source, the [census](../n131_w23_sixpair_density_20261016/RESULT.md) gives 1,049,218 edges and four signs per slot. Direct three-plus-three enumeration therefore has `(4 × 1,049,218)^3 = 73,922,589,492,632,846,848` labeled states **per side** before column checks. The N41 join demonstrates exact target-conditioned matching but its direct state expansion is too large for the N131 one-worker, 600 s, 4 GiB gate. The next experiment must give an exact, cheaply checkable target constraint on *families* of source codes before expanding three signed slots, then measure its surviving-family count on frozen N41 inputs against this join.

## Proof and verification

The [proof map](PROOF_MAP.md) links the source-inverse theorem to the earlier axiom-free `SharedInverse.lean`, and the new [SixPairJoin.lean](SixPairJoin.lean) proves six-input reassociation and the exact `left + right = target ↔ left = target - right` lookup. The pinned Lean 4.34.1 [build log](lean_check_final_verified.stdout.txt) reports no axioms for either new theorem. The bridge from these abstract group lemmas to the concrete binary curve and the native join is checked by the independent Sage replay and frozen input hashes.
