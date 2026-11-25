# Exact free pair-collision rows in the M31 collector

The frozen screen followed `PROTOCOL.md` on the public auxiliary and plain M31 fixtures. Every candidate collision was checked by group addition before its signed four-column row entered the modular elimination matrix. The candidate retained the same first-payload exact index as the control: complete sorted map SHA-256 was `ce7dab41355b3b236be455dbeaf9c46aaac83d29b272de5db727f54676407879` on auxiliary and `8b55e48edff4cbc66ac73ba30bc601ade0e7ae03fbf5439aaaaf2d807ec0d6fa` on plain. All 96 fresh-process arms returned the generator-verified public scalar `123456789`; all 48 matched blocks had the same basis digest and index entry count. Trials and target-relation counts were allowed to differ because the candidate started with homogeneous pivots. No arm failed or was censored.

| Basis | Exact duplicate sums | Nonzero four-term rows | Independent homogeneous rank | Control trials median | Candidate trials median | Control target relations median | Candidate target relations median |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Auxiliary | 60 | 60 | 10 | 6,144 | 6,053 | 470 | 459 |
| Plain | 84 | 84 | 14 | 5,737 | 5,630 | 455 | 445 |

| Basis | Control wall median ms | Candidate wall median ms | Paired control/candidate wall | Candidate wall wins | Control CPU median ms | Candidate CPU median ms | Paired CPU ratio | Candidate CPU wins |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Auxiliary | 90.759 | 92.339 | 0.9550 | 9/24 | 79.796 | 81.516 | 0.9707 | 11/24 |
| Plain | 70.877 | 79.513 | 0.8922 | 8/24 | 65.005 | 71.817 | 0.9181 | 6/24 |

The collision lookup and group checks are part of charged table construction. Its median grew from `12.111` to `13.636` ms on auxiliary and `11.723` to `14.906` ms on plain. Pre-eliminating free rows took median `0.061`/`0.083` ms, while target elimination medians rose from `3.083` to `3.569` ms and `2.823` to `3.377` ms. The harvested rank saved only about 90–107 target trials on median, insufficient to repay the extra setup. This is a directly measured cold end-to-end regression for this M31 implementation; the row count alone would have overstated the benefit by a factor of six. [pcc:unverified]

The arithmetic premise is exact: equal group sums of two signed pairs yield a homogeneous relation among their four factor-base logarithms when all points are in the prime-order subgroup. The Rust implementation checked the equal point sums and the final answer on these fixtures. This screen did not produce a machine-checked Lean refinement of the Rust row encoder, and no performance claim is derived from a theorem. Binary-field pair-root self-collision work in the shared lead atlas had already reported low rank and a cold net loss; this M31 result is consistent with that prior finding and is not claimed as a novel algorithm.

Compilation, frozen JSON loading and complete index-map audits preceded timing. The wall and parent-plus-child CPU clocks began before factor-base regeneration and ended after process exit; OS caches were not flushed. Raw CSV SHA-256: `30a15db82873d19a256012221e3077df57c88a1dcebbfaa37af88c8e8bad25b3`. Independent signed standing is pending. [pcc:unverified]
