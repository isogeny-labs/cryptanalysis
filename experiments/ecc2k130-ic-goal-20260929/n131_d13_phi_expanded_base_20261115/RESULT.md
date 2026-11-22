# Adjacent image doubles the exact N131 d13 base with the same log unknowns

The exact signed Frobenius closure of `P + tau(P)` contains **1,083,108**
subgroup points and has **zero point overlap** with the current d13 factor
base. Their union has **2,166,216 distinct usable points**, while every
image-point logarithm is a known nonzero scalar multiple of one of the
current **4,134** folded orbit logarithms. This supplies a concrete
factor-base design for a shorter point-decomposition chain. The frozen
[census](census_result.json) ran in 4.053 s with 230,670,336 B peak RSS;
an [independent checked-Sage replay](audit_result.json) matched the image
x-coordinate of all 4,134 representatives and eight subgroup scalar checks.

## Exact construction and count

The source is the live candidate's immutable [factor-base receipt](protocol.json)
on `EC1N131Ckb1heb5f1998f20b`, with 4,134 signed Frobenius orbit
representatives and 1,083,108 points. For every source point `P`, add
`phi(P)=P+tau(P)`. On the exact curve, the nonexceptional x-coordinate map is
`x(phi(P))=x(P)+1/x(P)`. Frobenius acts as scalar
`lambda=196511074115861092422032515080945363956` on the prime subgroup,
so `log_G(phi(P))=(1+lambda) log_G(P) (mod r)`. The coefficient is nonzero.
[PROOF_MAP.md](PROOF_MAP.md) gives the proof and formalization boundary.

| Exact set | x coordinates | Signed subgroup points | Folded log unknowns |
| --- | ---: | ---: | ---: |
| Existing d13 base | 541,554 | 1,083,108 | 4,134 |
| Adjacent image | 541,554 | 1,083,108 | 0 additional |
| Intersection | 0 | 0 | — |
| Union | 1,083,108 | **2,166,216** | at most 4,134 |

Both enumerations traverse all 131 Frobenius positions of every
representative. The [frozen protocol](protocol.json) binds the source
receipt, code, Sage runtime, exact curve, 180-second and 4-GiB limits.
The [independent audit protocol](audit_protocol.json) was frozen before the
polynomial-basis Sage replay; both stderr streams are empty. This is a
factor-base construction result, `proposal_id=Q20261115082001` and
`candidate_id=null` until a complete decomposition and log pipeline is
specified and measured.

## Shorter-chain screen

Each current position supplies 8,268 signed **projected subgroup points**.
Adding the disjoint image supplies **16,536** per position. If independent
ordered sums of these projected points were uniform in the prime-order
subgroup, the mean number of assignments for one target would be **0.13583**
for nine leaves and **2,246.13** for ten leaves. The current twelve-leaf
base has a corresponding mean of **149,946,445.36**. These are **derived
combinatorial heuristics**, not measured decomposition yield or SAT runtime.
The ten-leaf design trades fewer S3 links and 140 source-selector bits for
ten adjacent-image selector/map gates; its actual formula and solver cost
remain unmeasured. The nine-leaf mean is too low to select as the first test.

The current SAT construction searches raw curve lifts and four cofactor
preimages of a subgroup target. Applying the adjacent map to a raw lift may
change its cofactor component. Thus the projected-subgroup mean cannot be
assigned equally to four raw fibers without an additional distribution
argument. An exact raw-fiber and sign audit is a prerequisite for any
ten-leaf SAT model-count claim or frozen N131 solver run.

The adjacent map and its plus-only SAT leaf were previously checked on
[N41 and N131](../n41_n131_adjacent_frob_leaf_20261017/RESULT.md), and the
related ten-pair N131 public search reached its
[600-second cap](../n131_w18_adjacent_plus_public_20261017/RESULT.md).
Those runs use a linked pair as one internal summand and have a different
factor-base policy; they establish map correctness and a solver warning,
not this union-base ten-leaf result.

## Next falsifier

Audit the raw-lift/cofactor bridge, then build the exact union-base source
gate on a smaller-field full pipeline,
with an unpinned ordinary relation and independent point/log replay.
Compare its complete search cost and useful rank with the corresponding
original-base chain on the same target. Only then freeze an N131 ten-leaf
formula, retain a constructed positive assignment, and measure an unpinned
ordinary target under one worker, 600 seconds and 4 GiB. Charge all
preparation attempts and preserve every failure. The active d13/m12
collector is unchanged and its prospective yield gate remains separate.

Run `python3 verify.py` to check the frozen receipts and recompute the
shorter-chain arithmetic. Reproduction of both arithmetic programs uses
`/Volumes/SSD990/cryptanalysis/sage -python` after saving `--runtime-info`.
