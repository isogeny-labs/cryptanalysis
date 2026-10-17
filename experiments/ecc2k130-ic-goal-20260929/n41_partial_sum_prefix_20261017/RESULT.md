# Target-conditioned partial-sum prefix capacity on N41

**An exact relation-free N41 six-pair family still has 17 shared 32-bit x-prefix buckets across the public-target split.** Its first 20 canonical pair codes in each of six slots give 417,024 column-admissible triples per side. A native exact group join finds zero common points between the left sums and the target-translated right sums; an independent checked-Sage join reproduces that result and every prefix count. Both 8-bit and 12-bit prefix spaces are completely occupied on both sides. This gives a measured rejection and work boundary for coordinate-bucket summaries of large source families.

## Exact source and predicate

The curve is `y²+xy=x³+1` over `GF(2)[t]/(t^41+t^3+1)`, curve ID `EC1N41Ckb1h7d5e80d3c4d0`. The raw public target is `(2026560328086,1928332930914)`. The [frozen source](../n41_sixpair_shared_target_20261017/join_input.tsv) contains 40 canonical seed-56 pair codes and four signed states per code in each of six Frobenius rotations `(0,6,12,18,24,30)`. The [half-code protocol](half_protocol.json) fixes code ordinals `0..19` in every slot, target, input/source hashes, compiler and binary hashes, one worker, 180 seconds and 4 GiB. The archived six-pair relation has code ordinal 30 in slot 1 and is outside this selected family.

Let `L` be the column-admissible sums of slots 0–2, and let `R_Q={Q-(P₃+P₄+P₅)}` for column-admissible states in slots 3–5. The native worker stores full group points from `L` and queries each `R_Q` point. For nonidentity points it also forms `B_k(S)={x(P) >> (41-k): P in S}` for `k∈{8,12,16,20,24,28,32}`. A common group point must give a common prefix, so disjoint prefix sets would be an exact family rejection. A common prefix alone leaves that family unresolved.

| Top x bits | Distinct left buckets | Distinct target-translated right buckets | Shared buckets |
| ---: | ---: | ---: | ---: |
| 8 | 256 | 256 | 256 |
| 12 | 4,096 | 4,096 | 4,096 |
| 16 | 62,783 | 65,431 | 62,682 |
| 20 | 189,091 | 344,112 | 62,212 |
| 24 | 207,233 | 412,001 | 5,088 |
| 28 | 208,431 | 416,691 | 317 |
| 32 | 208,505 | 417,008 | 17 |

The exact point lookup has **zero coordinate hits and zero relations** for this complete half-code panel. Both sides have zero identity points in the enumerated triples. The [native result](half_result.json) records 4.455 seconds inside the worker and 7.070 seconds parent wall with 146,767,872 B sampled peak combined RSS and no monitor gaps. The [checked-Sage replay](audit_result.json) independently reconstructs all 960 saved curve points, performs the full 417,024-by-417,024 *indexed* group join, and recomputes all seven prefix intersections in 22.513 seconds of its own interval. The checked [Sage runtime receipt](sage_runtime_info.json) was captured before that run. These are ordinary-host component diagnostics. `candidate_id` remains `null`.

The separate full 40-code [worker payload](result.json) completed with 3,750,144 triples per side and full occupation of every bucket through 16 bits. Its parent recorded `PRODUCER_FAILURE` and `monitor_degraded: true` despite exit code zero and a complete worker JSON payload; that run's resource envelope is therefore not certified. The receipt is retained as an infrastructure-qualified diagnostic. The completed half-code worker and independent Sage audit support the exact table above.

## Proof and algorithmic decision

The readable proof of the rejection rule is immediate: if `P` belongs to both `L` and `R_Q`, then `x(P)>>(41-k)` belongs to both bucket sets. Thus an empty bucket intersection excludes a relation. [PrefixGate.lean](PrefixGate.lean) proves this for an arbitrary key map and finite lists, together with the disjoint-key contrapositive. The pinned Lean 4.34.1 build and `#print axioms` audit report only `propext` and `Quot.sound`. [PROOF_MAP.md](PROOF_MAP.md) separates those checked structural implications from the finite curve census established by independent execution. The first Lean source used the reserved identifier `prefix` and failed to parse; its exact source and log remain saved.

The half-code family requires enumeration of all **834,048** admissible partial triples to build its two prefix sets. At 32 bits the filter still cannot reject the family, while the full-point hash lookup on those same triples resolves it exactly. The frozen N131 W23 source has 4,196,872 labeled states per slot, so a direct unpruned three-slot product has `73,922,589,492,632,846,848` labeled choices per side before column checks; a direct prefix census of that product cannot fit the one-worker, 600-second gate. This is a source-size projection, not an N131 measured occupancy claim.

The next candidate should compute a target-conditioned **joint constraint on compressed source-code families** without enumerating their three-slot partial sums. The existing pair-output inverse and S3 resultants are the exact source primitives; an unpinned N41 complete-family test must demonstrate rejection or a verified relation at a lower charged cost than its full-point join before an N131 public-point attempt.
