# A four-class holdout falsifies the rank-37 pre-lift skip rule

The frozen direct-rank gate said `SKIP` for all four newly selected 40-point D79 classes. Full 40-source challenges found one false reject: at (p=103357), base-plus-direct rank 35 over (F_{197}) rose to **39** after 218 Hecke rows. One anchor raised the relation system to full rank, and the independent Sage audit recovered and replayed all 40 projected class logs. The rank-37 threshold must therefore be withdrawn as a rule for skipping degree-13 source work.

| Prime (p) | Largest prime factor (q) | Direct rank | Full-source rank | Hecke rank gain | Gate outcome |
| ---: | ---: | ---: | ---: | ---: | --- |
| 102077 | 929 | 32 | 34 | 2 | Correct reject |
| 103357 | 197 | 35 | 39 | 4 | **False reject; anchored logs replayed** |
| 108557 | 701 | 31 | 34 | 3 | Correct reject |
| 115237 | 307 | 32 | 35 | 3 | Correct reject |

The selector scanned odd (v≥303) using the frozen (p=v²+316), curve-order and class-size rules. These were the first four eligible 40-point classes, and their direct ranks and `SKIP` decisions were hash-sealed before any degree-13 lift. Every selected class was then challenged with all 40 source lifts, including the three low-rank cases. All 160 source entries completed with `OUTSIDE_CLASS_TRACE` status. The independent audit re-evaluated the public prescreen, enumerated direct relations by Sage pair lookup, verified every source equation and derived Hecke group row, and rebuilt each matrix over its recorded field.

This is **one false reject among four frozen skips**, not an estimated population false-reject rate. The p103357 result is a concrete counterexample to the threshold's safe-skip interpretation; the other three outcomes remain retained. The observed four-direction Hecke gain also exceeds the earlier training maximum of three, so extrapolating a fixed gain cap from the current classes would be unsound.

Lean kernel-checks the gate logic over the four audited rank pairs: one false reject, three correct rejects, and the p103357 `(35,39)` counterexample. The numeric matrix ranks and curve-log replay are independently Sage-checked; their full Lean bridge remains open in `PROOF_MAP.md`. Source-lift intervals, direct enumeration, Hecke enumeration and peak memory are retained as local stage diagnostics. `candidate_id` and `target_online_ms` remain null.

## Next experiment

Replace the empirical rank threshold with a source-independent **provable upper bound** on the rank that any allowed degree-13 row pool can add, or treat the pre-lift direct rank as a prioritization score rather than a skip gate. A new gate should be frozen and challenged on fresh classes before deployment into a source scheduler.
