# Quadratic certificates on complete six-pair source-code boxes

**Sixteen exact quadratic determinant-value certificates cover a complete 4,096-state N41 six-pair source-code box.** Independent checked Sage finds zero group-law relations in that box. The certificates are obtained by fixing the first two signed pair states, leaving 256 complete combinations per family. A larger 262,144-combination two-code box also has zero group-law relations, but its unsplit quadratic system is inconsistent after 860 evaluated combinations. These measurements give a concrete capacity and work boundary for this target-conditioned family filter.

## Frozen method

The field is `GF(2)[t]/(t^41+t^3+1)` and the curve is `y²+xy=x³+1`. The raw public target is `(2026560328086,1928332930914)`. The [source](../n41_sixpair_shared_target_20261017/join_input.tsv) has six slots, 40 pair codes per slot, and four signed states per code. The exact [protocol](protocol.json) pins the source and split-minor runner hashes, one worker, a 600 s cap and a 4 GiB ceiling. All code combinations in the four boxes have twelve distinct folded columns and pass the seven-point distinct-x chart check.

For each left triple and right triple, the [split-minor identity](../n41_rr_split_affine_20261017/RESULT.md) evaluates the seven-point Riemann–Roch determinant `D(L,R)` as 35 field-product terms. A quadratic Boolean functional in its 41 coordinates has 861 features and no constant. Solving `Q(D)=1` over every state in a box certifies the box contains no zero determinant. A linear-system contradiction says only that this certificate family cannot reject the box; it does not assert a group relation.

The [runner](run.py) tests four boxes. The positive boxes include the previously audited relation state IDs `(12,122,116,47,128,34)`; the negative boxes use column-disjoint code selections. [Independent Sage](audit_sage.py) computes exact group sums for every left and right partial state and counts all target matches.

| Complete box | States per side | Combinations | Quadratic system | Feature rank at contradiction | Exact group relations |
| --- | ---: | ---: | --- | ---: | ---: |
| Witness codes, one per slot | 64 | 4,096 | Inconsistent after 563 values, including the zero determinant | 562 | 1 |
| Disjoint codes, one per slot | 64 | 4,096 | Inconsistent after 865 values | 861 | 0 |
| Witness plus extra code, each slot | 512 | 262,144 | Inconsistent after 857 values | 856 | 1 |
| Shifted first code, two per slot | 512 | 262,144 | Inconsistent after 860 values | 859 | 0 |

The four-box runner took **9.885 s** in an ordinary-host Python process, including source-state parsing, split-minor vector preparation and the early certificate decisions; it made 2,314,447 counted field multiplications and reported 20,840,448 bytes peak self RSS. These are component diagnostics, not an IC candidate timing. `candidate_id` remains `null`.

## Partition iteration

The negative one-code box supplies a complete relation-free family in which to test whether source-state subdivision restores certificate capacity. The [partition protocol](partition_protocol.json) pins the exact code selection `(0,1,2,4,5,6)`, source hashes, and runner. The [partition result](partition_result.json) records every decision and coefficient vector.

| Fixed leading signed states | Families | Combinations per family | Certified families | Determinants evaluated for full cover |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 1 | 4,096 | 0 | 865 until contradiction |
| 1 | 4 | 1,024 | 0 | At most 1,024 per family until contradiction |
| 2 | 16 | 256 | 16 | 4,096 |

Each of the 16 coefficient vectors is replayed against all 256 values of its family with a separately written feature calculation; the [terminal verifier](verify.py) repeats the 4,096 checks and binds the exact Sage group audit. The partition run spent 1.544 s in its determinant/certificate interval and made 398,820 counted field multiplications. The first partition attempt used Python 3.10's `int.bit_count` on local Python 3.9 and stopped before emitting a result; its frozen source, protocol, and [failure receipt](partition_attempt1.stderr.txt) are retained.

## Proof boundary and next test

The readable argument is `Q(0)=0`: whenever `Q(D)=1`, `D` is nonzero. The 16 certified families form a disjoint partition of the negative one-code box by its first two signed states. The prior [Lean theorem](../n41_rr_quadratic_value_dual_20261016/QuadraticCertificate.lean), `QuadraticCertificate.certificate_excludes_zero`, proves the exact Boolean implication and was built with the pinned Lean 4.34.1 toolchain; its prior proof audit reports `propext` and `Quot.sound` only. The finite field, curve, determinant, source-chart and complete family bridges are checked by the archived source audit and this experiment's executable replay. No new general mathematical theorem is asserted by this finite capacity measurement.

The measured 16-way cover evaluates all 4,096 determinant combinations and thus supplies **no pre-expansion rejection** for the six-pair search. This is a cheap falsifier for quadratic *determinant-value* certificates on complete source-code boxes. The next algorithmic test should impose the public target on the source-code equations or on compressed partial-sum families before enumerating their Cartesian product; retain an unpinned N41 target, exact relation replay, and a projected one-worker N131 W23 cost.
