# Pointer-indexed Frobenius join cuts N41 storage while preserving the public relation

**A pointer-indexed join reduced the extra storage for Frobenius-folded triple reuse by 90,062,848 bytes** on the frozen N41 six-pair public target. It found the same independently replayed twelve-column relation after exactly 1,100,323 probes in both repetitions. The source-specific saving is structural: each right triple sum is the eighteenth Frobenius image of the corresponding left triple sum, and the new join keeps an 8-byte pointer to each left hash-table entry instead of a second 32-byte triple record.

## Exact method and source

The input, target, six 160-state slots, rotation pattern `(0,6,12,18,24,30)`, and curve `EC1N41Ckb1h7d5e80d3c4d0` are those in the [previous folded experiment](../n41_frobenius_folded_join_20261016/RESULT.md). Its algebraic result gives `P_(j+3,i)=F^18(P_(j,i))` for `j=0,1,2`; addition commutes with Frobenius. The direct arm recomputes right triple sums. The vector arm stores each left sum and its three state IDs. The pointer arm inserts the same sum in the left hash table and stores a pointer to that entry in insertion order. It then applies Frobenius to the entry's point for the right probe. The left table reserves 4,100,000 entries before the 3,750,144 inserts and never erases an entry. All arms use the same public target, source ordering, column checks, hash lookup, hit replay, and exact stop rule.

The [independent audit](audit_result.json) reconstructs the 41-bit field arithmetic, checks all 480 pointwise Frobenius correspondences and 76,800 pairwise column-compatibility correspondences, and replays the six-point group sum and twelve distinct columns. It confirms all six runs produced state IDs `(12,122,116,47,128,34)`, 3,750,144 left triples, 1,100,323 right probes, and three coordinate matches. The sum is raw public point `(2026560328086,1928332930914)`.

## Matched one-worker diagnostic

The [protocol](protocol.json) hashes the three source files, three binaries, input and runner, fixes the compiler flags, and orders the arms direct/pointer/vector/vector/pointer/direct. Each child ran in its own Python process, so `RUSAGE_CHILDREN.ru_maxrss` is a per-run peak rather than a cumulative reading. The parent wall includes input parsing and table construction. All six children exited zero below the 180 s and observed 4 GiB resource boundaries. The host has no isolation-tier receipt, so these times are exploratory component measurements.

| Arm | Parent wall, two runs | Peak child RSS | Same hit and probe counts |
| --- | --- | ---: | --- |
| Direct | 4.901, 5.342 s | 223,592,448; 223,559,680 B | yes |
| Pointer folded | 4.312, 4.203 s | **253,575,168 B** both | yes |
| Full-vector folded | 4.266, 4.093 s | 343,638,016 B both | yes |

The pointer version uses 29,982,720 more bytes than the first direct run and 90,062,848 fewer than the vector version. Both folded versions have lower wall readings than the direct arm in this batch, while the pointer version reads slightly slower than the full vector. The two readings per arm and ordinary host do not establish an isolated speedup. Source-specific computation saves the 1,100,323 right triple additions reached before this witness; target subtraction and hash probes remain charged.

## N131 transfer boundary and next gate

The frozen N131 W23 source has 1,049,218 usable edges per slot with four signed states per edge. Its explicit three-slot list has `(4×1,049,218)^3 = 73,922,589,492,632,846,848` labeled entries. Even an 8-byte pointer per entry would consume **591,380,715,941,062,774,784 bytes** before the hash table, roughly 513 EiB. This is a capacity bound for the pointer-list representation, not for implicit source-family methods. It makes another explicit-table optimization irrelevant to the N131 600 s / 4 GiB relation gate.

The next experiment must use the public target to reject *implicit three-slot families* before enumerating a Cartesian triple list. A concrete starting point is a shared-residual constraint joining two unresolved pair-product blocks and a third free block, with N41 public witness preservation, ordinary misses, complete query cost, and source-region rejection all measured before N131 promotion. `candidate_id` remains null until the full IC pipeline is specified.

## Verification

`python3 audit.py` passed the independent finite-field and group replay. `python3 verify.py` checked every frozen hash, exit status, cap observation, row count, hit, and audit binding; its [terminal receipt](terminal.json) is `PASS`. The [proof map](PROOF_MAP.md) references the previously checked Lean group theorem and records the new pointer-lifetime obligation. No new mathematical identity is asserted by the pointer layout.
