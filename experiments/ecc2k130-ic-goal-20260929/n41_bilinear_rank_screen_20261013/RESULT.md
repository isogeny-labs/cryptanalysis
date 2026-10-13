# A pivot-conditioned rank-one solver for two pair-output families

**Branching on the first nonzero left-basis bit turns the target-conditioned S3 link into a sequence of binary linear systems, then exact rank-one checks classify the whole pair of output spaces.** On 1,026 frozen N41 family and target cases, the method found the one constructed positive and agreed with an independent direct join on every case. It enumerated **2,065 affine candidates** across the panel, while the direct comparator opened **64,638 left coordinates**. A plain linear span-rank screen rejected only **2** cases, exposing the trace-zero hyperplane as its structural limitation.

## Bilinear gate

Use the same curve and `c=1/x` coordinate chart as the [complete N41 product-span census](../n41_joint_product_span_relaxation_20261013/RESULT.md): `GF(2)[t]/(t^41+t³+1)`, `y²+xy=x³+1`, curve ID `EC1N41Ckb1h023d9a38bbf7`. Each fixed product `p∈span(t²,…,t^12)` defines a linear pair-output space `C_p`. Of the 2,048 product families, **2,026** project to six-dimensional coordinate spaces and **22** to seven-dimensional spaces. The panel uses only the six-dimensional families, leaving their seed sums, output coordinates, signs, and source masks free. This remains a point-decomposition component with `candidate_id: null`.

For bases `c=Σα_i u_i` and `d=Σβ_j v_j`, the target equation is

`S3(c,d,t)=(cdt)²+cdt+c²+d²+t²=0`.

Introduce `γ_ij=α_iβ_j`. The field equation becomes linear in the `r+s+rs` bits `(α,β,γ)`:

`Σ_i α_i u_i² + Σ_j β_j v_j² + Σ_ij γ_ij((t u_i v_j)²+t u_i v_j)=t²`.

The first screen tests whether `t²` lies in the span of those columns. For exact solving, branch on the **first** set bit `α_i=1`, set earlier `α` bits to zero, and substitute `γ_ij=β_j` in that pivot row. Solve the remaining linear system, enumerate its affine kernel, impose every other `γ_kj=α_kβ_j`, reject zero coordinates, and replay S3. Every nonzero `c` has one first set bit, so these branches cover it without duplication. The [native solver](native.cpp) recomputes both family bases from the frozen halftrace equations and compares its pivot hits against a direct quadratic-root join for each case.

## Frozen N41 panel

The [protocol](protocol.json) fixes the previous source and Sage group-control hashes, the native source and binary, two target reciprocals, a deterministic 512-pair sample from the 2,026 six-dimensional families, one worker, a 180-second wall cap, and 4 GiB. The positive family pair `(819,176)` comes from source-mask pairs `(21,63)` and `(8,22)` on the previously checked constructed target. It is included once for each target before the 512 sampled pairs, giving **1,026** case rows. The sampled family pairs are reused for both targets.

| Same frozen family sample | Constructed target | Public-point reciprocal |
| --- | ---: | ---: |
| Sampled family pairs | 512 | 512 |
| Plain rank rejections | 1 | 1 |
| Native rank histogram, including positive-family row | 510 rank 40; 3 rank 39 | 511 rank 40; 2 rank 39 |
| Exact rank-one / direct-join hits | 1 / 1 | 0 / 0 |

Across all 1,026 rows, **1,021** lifted matrices have rank 40 and **5** have rank 39. The two rank-inconsistent rows have no direct hit. The pivot solver completed every row with maximum affine nullity **3**, and its single positive has one exact match. The [case file](cases.jsonl) retains every product pair, target, rank, status, affine candidate count, and exact hit count. The [independent Python audit](audit_result.json) replayed 64 selected rank screens and 16 direct joins, including the positive and both rank-inconsistent cases; it checked all 1,026 native pivot/direct equalities and receipt hashes.

The [checked-Sage control](sage_result.json) reconstructs the positive family's four source points from masks `(21,63,8,22)`, verifies product codes `(819,176)`, and finds two sign assignments whose complete group sum has the frozen target reciprocal. Its [runtime receipt](sage_runtime_info.json) was saved before the group job.

The empirical rank rejection rate is `1/512 = 0.195%` for each target's pseudorandom sample. A descriptive 95% Wilson interval for each target's sampled family-pair rate is approximately **0.034%–1.098%**; the two target samples reuse the same product pairs and are not independent. No ordinary relation rate is inferred from the planted positive. The one-worker [receipt](receipt.json) records **4.435 seconds** runner wall, **3.580 seconds** in the case loop, and **2.44 MB** sampled peak RSS. These are local stage diagnostics without host isolation; the experiment does not establish a CPU speedup over another complete solver.

## Structural limit and N131 gate

For every sampled target, `Tr(t)=0`; the six W6 basis elements have trace zero. Each linearized S3 column is a square of a trace-zero coordinate or has Artin–Schreier form `z²+z`. Its trace is therefore zero. The entire span lies in the **40-dimensional trace-zero hyperplane**, explaining the observed rank ceiling of 40; the [Lean proof](BilinearGate.lean) checks the column implications under explicit trace laws. The target constant `t²` also has trace zero, so a rank-only filter usually sees a consistent system. The rank-one constraints carry nearly all the selectivity.

For W18 over N131, every fixed-product halftrace system has 150 variables and at most 132 equations. Its projection onto the output coordinate is injective: if `c=0`, the halftrace equation and trace guard give `H(s²)=ε` and `Tr(s²)=0`, hence `s²=H(s²)²+H(s²)=0` and then `s=ε=0`. Each projected family therefore has dimension **at least 18**. The first-pivot bilinear branch has at least `18(18+1)−1=341` Boolean variables but at most 131 field equations. Any consistent branch has nullity **at least 210**, so enumerating every affine solution before the rank-one checks requires at least `2^210` candidates for that branch. A full product-family-pair scan would also have `2^70` pairs. The [machine-readable bound](transfer_bound.json) applies to this literal lift, not to an algorithm that couples several unresolved pair blocks or imposes rank-one structure earlier. The next experiment must add target-derived constraints across more than two free pair blocks **before** linear-solution enumeration and family-pair traversal.

The [proof map](PROOF_MAP.md) states the checked structural lemmas and the remaining complete-solver formalization obligation. The [read-only terminal audit](terminal_audit.json) binds the frozen sources, cases, receipts, independent audit, Sage control, Lean output, and transfer arithmetic. Replay it with `python3 -B experiments/ecc2k130-ic-goal-20260929/n41_bilinear_rank_screen_20261013/verify.py` from the repository root; the independent arithmetic check is `audit.py` in the same directory and the formal module builds with `lean BilinearGate.lean` there.
