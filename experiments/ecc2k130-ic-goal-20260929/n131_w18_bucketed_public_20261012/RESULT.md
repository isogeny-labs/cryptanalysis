# Target-ordered N41 source bucket: a verified public relation and exact N131 memory gate

## Contribution

An exact source bucket selected by a hash of the frozen N41 public point produced a new eight-column relation through a one-worker group join. The join kept four signed first-pair states, built 119,856 compatible left entries, and found a row after 7,615,892 admissible right probes. Independent checked Sage reconstructed the eight source points and their signed Frobenius transports, proved their raw sum equals public preimage 1, checked cofactor projection to the public point, and raised the rank of four saved reference rows from 4 to **5**. The bounded parent interval was **9.325023250 s**, with **44,089,344 B** sampled peak combined RSS.

The matching N131 W18 source has **4,161,596** admissible first-pair mask edges in this low-six-bit bucket, or **16,646,384** signed first-pair states. The literal two-pair left hash used by the N41 join would insert **573,996,287,552,471,808** entries after distinct-column filtering. One bit per entry already takes **71,749,535,944,058,976 B**, 16.7 million times the 4-GiB cap. An independent exhaustive cross-class count reproduced that exact entry count. The verified N41 row is therefore a source-law control for a new symbolic joint filter, while the literal hash construction fails the N131 memory gate.

## Frozen method and measurements

The N41 curve is `EC1N41Ckb1h7d5e80d3c4d0`, with field `GF(2)[t]/(t^41+t^3+1)`, curve `y²+xy=x³+1`, subgroup order `549756390943`, and public point `(920359962848,755404565011)`. Source slots use Frobenius rotations `(0,7,14,21)` and the complete diagonal-pair input `../n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv`, with 30,952 signed states per slot. The source partition fixes the low six bits of the two first-pair masks for each attempt. Its bucket order is SHA-256 of the public point and bucket code, filtered only for source-valid mask edges; `bucket_plan.json` freezes the first eight choices before any solver search. The first bucket is code 905, with mask residues `(9,14)` and one unordered source edge. It permits both mask orientations and all four signs. No witness ID, exact mask, pair output, or group sum was used to select the bucket.

| Frozen N41 query | Result | Charged parent wall | Sampled peak RSS |
| --- | --- | ---: | ---: |
| Eight independent native-XOR SAT bucket processes, 18 s solver limit each | Eight `BOUNDED_UNKNOWN` rows; six solver `INDETERMINATE` terminals and two 20 s parent caps | 153.668 s total | 447.7 MB |
| One persistent native-XOR solver with the same ordered bucket assumptions and learned-clause reuse | Seven `BOUNDED_UNKNOWN` calls, then 175 s parent cap | 175.062 s total | 454.1 MB |
| Full 180 s solver cap for bucket 905 | `BOUNDED_UNKNOWN`, 190 s parent cap | 190.063 s | 409.2 MB |
| Exact group join for bucket 905 and raw public preimage 1 | `PASS_INDEPENDENT_N41_BUCKET_905_PUBLIC_RELATION`; rank 4→5 against four saved rows | 9.325 s, including 0.151 s source/table setup | 44.1 MB |
| Full 180 s solver cap after adding the exact two-value first-pair reciprocal table | `BOUNDED_UNKNOWN`, 190 s parent cap; complete positive assignment passes 35,880 CNF clauses and 2,892 XOR rows | 190.055 s | 358.2 MB |

All times are local stage diagnostics on a host without an isolation receipt. The independent Sage audit runs after the native join interval. The source table gate adds 58 clauses to bucket 905's 12 unit clauses; its two reciprocal values come from all four source states, and the hit's derived complete assignment checks every augmented formula row. The separate Python native-XOR parser control found and replayed a complete positive model before the incremental comparison. Each capped solver attempt remains a `BOUNDED_UNKNOWN` row, with its log and exact formula hash retained.

The N131 source is `EC1N131Ckb1heb5f1998f20b` over `GF(2)[t]/(t^131+t^13+t²+t+1)` with the same published public workload as the preceding four-pair study. It has 131,307 rational W18 masks, 131,068 folded columns, and 34,482,792,912 signed distinct-column pair states per rotation. `projection_result.json` counts every literal left tuple using source-column multiplicities; `projection_audit_result.json` independently iterates the 4,161,596 admissible cross-residue mask edges and subtracts incident pair edges. This transfer gate concerns the literal `bucket_join.cpp` hash layout, which stores each compatible two-pair tuple.

## Exact count and verification

Let `M` be the 131,307 usable masks, `k_i` the number in folded column `i`, and `C = binom(M,2) − Σ_i binom(k_i,2)` the number of unordered distinct-column mask edges. For a first edge in columns `i ≠ j`, the slot-1 edge count after excluding both columns is

`C − k_i(M−k_i) − k_j(M−k_j) + k_i k_j`.

The first two subtractions remove edges incident to either occupied column; the last term restores edges joining those columns, which were subtracted twice. Each first edge and each remaining slot-1 edge has four sign choices, so multiplying this count by 16 and summing over the complete `(9,14)` residue-class cross product gives the literal left-entry count above. The producer uses the equivalent complement formula; the independent audit uses this incident-edge formula. The minimum one-bit storage figure follows by ceiling division by eight.

The checked Lean lemma `BucketRelation.map_four_sum` proves the structural transport of an exact four-summand equation by an additive homomorphism. `lean_check.txt` reports no axioms. The finite field curve equality, signed-source reconstruction, cofactor map, and rank-five certificate are independently checked in Sage; their concrete Lean formalization remains open as listed in `PROOF_MAP.md`.

## Next method gate

The direct path to N131 must represent a **joint two-pair output family without materializing its tuples**, then use the public target to reject families while at least two more pair outputs remain free. The exact N41 hit supplies a positive input for an upper-S3 or resultant propagator. The first-pair reciprocal table alone left the ordinary SAT search capped, so the next predicate must constrain the interaction of at least two partial sums. Freeze that predicate and its complete work/RSS model, prove it preserves this checked row, then test an unpinned N41 public query before another one-worker, 600-second, 4-GiB N131 run. This component study has `candidate_id: null` until the full pipeline is specified.
