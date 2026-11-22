# Proof map: serial implicit-oracle work

| Result | Lean declaration | Hypotheses and verification | Concrete bridge |
| --- | --- | --- | --- |
| Pair quadratic recovers the source product as `p=C/x+Hx` | Existing `OutputLinearization.pair_output_linear_iff` in `../n131_w20_output_inverse_linear_20261012/OutputLinearization.lean` | Characteristic-two commutative ring with an explicit nonzero reciprocal and inverse witness; prior checked proof | This run's product-inverse map is compared with direct point membership on every one of 109,340 examined candidates; checked Sage independently reconstructs all 385 key outcomes. |
| Complete misses of a serial oracle require `misses × first-slot width` candidate checks | `W9SerialOracle.missScan_count` | Natural-number recurrence, arbitrary miss count and width; checked under Lean 4.34.1 using the standard `propext` foundation | The native oracle scans all 284 first-slot states for every complete miss; the independent Sage replay confirms the frozen panel's hit and miss classifications. |
| The frozen join's minimum serial checks are 23,746,036,052 | `W9SerialOracle.frozen_complete_miss_checks` | Applies the recurrence at 83,612,803 complete misses and width 284; checked under `propext` | The prior frozen join made 83,612,805 lookups and reported two hash matches, so at least 83,612,803 keys were complete misses. `work_projection.py` verifies these counters and the arithmetic. |

`lean-toolchain` pins `leanprover/lean4:v4.34.1`; `lean SerialWork.lean`
built the actual module and `lean.stdout` records both `#print axioms`
outputs. The source has no `sorry`, `admit`, custom axiom, or native-evaluation
proof. `lean4checker --fresh` was unavailable on this host. The native
query counts and concrete elliptic-curve group bridge are independently
replayed computationally; they are not formalized in this Lean module.
