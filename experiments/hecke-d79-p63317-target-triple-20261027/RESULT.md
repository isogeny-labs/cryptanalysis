# Six probes find a three-source relation for the retained p63317 target

The exact public point `(31493,39327)` that returned `NO_RELATION` in the frozen signed pair experiment has a verified three-source relation after six pair-index-plus-one residual probes. The first witness is `Q=B₇+B₂₈+B₂`, with three distinct projected class points. Their anchored logs are 2266, 169 and 1069; the signed sum is `3504 ≡ 973 (mod 2531)`, and independent Sage replay verifies `973T=Q`.

## Frozen search and accounting

This run uses the hash-pinned p63317 public point, 40 class logs, failed pair result and audit, and pair coverage receipt. The pre-run manifest sealed the construction of all 3,120 signed distinct-source pairs, retention of every witness per index point, third-source order `k=0,…,39`, sign order `−1,+1`, distinct-index filter, first verified stop, and 80-probe cap before the triple producer ran. The target was not changed after the earlier miss.

The pair index still has 689 distinct points. For each target-dependent probe, the producer queried `Q−cB_k`, scanned all pair witnesses in the bucket, and required `i,j,k` to be distinct. The first five probes were recorded as misses. Probe six (`k=2`, `c=+1`) found pair sources 7 and 28 with positive signs, then checked the group equation and scalar replay.

| Stage | Observed time | Boundary |
| --- | ---: | --- |
| Base projection and all-witness pair-index build | 3,181,000 ns | Target independent, after anchored logs are loaded |
| Six residual probes | 15,834 ns | Target dependent |
| Pair-bucket scan and relation check | 4,249 ns | Target dependent |
| Scalar replay | 14,042 ns | Target dependent |
| Interval overhead | 7,833 ns | Target dependent |
| Complete measured component interval | 41,958 ns | Sum of the four target-dependent entries above |

The independent checked-Sage audit rebuilt the exact all-witness pair index and digest, reproduced every attempted residual and the first witness, and verified scalar 973 against the public point. It also enumerated every signed triple on three distinct class indices: **79,040 patterns cover 2,503 of 2,531 subgroup points**, leaving 28 outside this relation family. The target is among the covered points. These are one-run local component diagnostics with target-independent class-log and relation preparation retained in parent receipts; `candidate_id` and `target_online_ms` remain null.

`TargetTriple.lean` proves conditional transport of the three-source group relation through the projected-log map and checks `2266+169+1069 ≡ 973 (mod 2531)` with no axioms. `PROOF_MAP.md` records the concrete curve-group bridge and the finite coverage formalization still open.

## Next experiment

The 28 uncovered subgroup points give a fixed residual set for a further relation-family test. Freeze a new target from that set only for a separately labeled coverage question; retain this target as the unchanged one-target progression from pair miss to triple success. A complete IC comparison would also need a fully specified candidate, charged upstream preparation and a same-point rho reference under an admitted measurement tier.
