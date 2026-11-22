# Held-out N41 six-pair target recovery and paired rho diagnostic

The precomputed N41 W8 six-pair pipeline recovered the scalar of a **fresh
single public point** from an unpinned decomposition. The native target path
used 2.315327 seconds after reusable pair tables and 70 verified factor logs
were ready. A one-worker Pollard-rho walk solved the **same point** in
9.822693 seconds. Both returned scalar `152754809504`, and
[independent Sage replay](audit_result.json) verified it against the curve,
the twelve selected source points, their folded columns, and the fourfold
projection. The local ratio `rho/IC = 4.242465` is an exploratory timing
diagnostic: the host has no isolation receipt, and Sage's independent replay
was recorded after each native interval.

The [frozen protocol](protocol.json) fixes curve
`EC1N41Ckb1h7d5e80d3c4d0`, subgroup order `549756390943`, generator
`G=(1236950581268,1658150202663)`, workload `86cc67dad07c`, and public
target `Q=(1096889081872,1442440541544)`. The target was generated after
the [70-column factor-log system](../n41_w8_sixpair_logprep_20261011/RESULT.md)
had reached full rank; it is absent from that 128-point preparation panel.
The scalar fixture was sealed from both executed modes. The [preparation
receipt](preparation_result.json) binds 840 state logs, each independently
checked against a curve multiplication, four torsion offsets, the public
point, and the checked Sage runtime. A separate smoke control recovered the
earlier transported point's audited scalar before this input was timed.

| One public point, one worker each | IC | Pollard rho |
| --- | ---: | ---: |
| Target-dependent setup/query | 25,666 ns | 1,309,500 ns |
| Decomposition or walk and collision | 2,315,278,917 ns | 9,821,362,083 ns |
| Relation check / scalar check | 458 ns | 21,750 ns |
| Target log combination | 292 ns | included in collision step |
| Native scalar replay | 21,625 ns | included above |
| **Exclusive native online phase sum** | **2,315,326,958 ns** | **9,822,693,333 ns** |
| Peak combined RSS sampled | 378,306,560 bytes | 22,462,464 bytes |
| Result | scalar replay passed | 1,383,721 steps, 10,656 distinguished points, one collision; scalar replay passed |

The IC clock starts after source-table and factor-log loading, construction
of the two 2,513,280-entry reusable triple tables, and public-point input
loading. It includes raw-preimage computation, every target-dependent group
join probe, exact relation checks, log combination, and native scalar
replay. The table build took 48.457 seconds on this unisolated host and is
reported separately from target online time. Rho starts before constructing
its 16 target-dependent additive partitions; it uses a fresh same-target
distinguished-point table and no cross-target work. Both modes had one worker,
a 300-second parent cap, and a 4-GiB combined RSS cap. The [native source](online.cpp),
input hashes, exact run order, output hashes, phase boundaries, and raw
failures are preserved in the protocol and mode receipts. Sage replay checks
the returned scalar, target equality, all six signed pair states, twelve
distinct folded columns, and the raw and projected group sums.

This completes a smaller-field end-to-end method control. Its current native
interval omits the external independent Sage replay, and the CPU host lacks
the required isolation and calibration receipt, so `candidate_id` remains
`null` in this exploratory run and the ratio is not promoted as a controlled
IC speedup. The next one-target N41 run should use a fresh point with an
independent verifier ready inside both online clocks and an isolated paired
host. For ECC2K-130, the current explicit three-pair table scales to more
than 37 PB before overhead; the degree-131 step requires a compressed
target-conditioned family join rather than this materialized MITM table.
