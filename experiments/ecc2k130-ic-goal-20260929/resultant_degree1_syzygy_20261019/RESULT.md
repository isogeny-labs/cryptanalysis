# A cubic degree fall in the target-conditioned two-pair resultant

Multiplying the frozen 13-term two-pair resultant by its first source product `p` reduces its Boolean code degree from four to **three**. For the N131 width-four block this removes all 2,976 quartic ANF monomials and reduces the field-valued ANF from **5,317 to 2,314 monomials**. The same transformation reduces the N41 width-five block from 886 to 446 monomials. An exhaustive N41 block check and a seeded N131 panel verify `scaled = p·resultant` on the frozen positive and ordinary target rows. This supplies an exact lower-degree source constraint that a joint solver can use while keeping the second source code free.

The standalone cubic Gröbner solver recovered the N41 positive codes `(253,63)` and returned the unit ideal on its paired ordinary residual, with **15.74 and 15.79 seconds** of monitored parent wall respectively. The corresponding N131 positive width-four run reached its **4-GiB RSS cap at 395.09 seconds**. Adding the cubic equations to the original quartic system also passed both N41 controls, then reached the N131 positive RSS cap at **429.37 seconds**. These resource outcomes select neither solver for the N131 relation search; the verified lower-degree representation remains available for a different elimination strategy.

## Exact algebra and source

The two-pair resultant is `F(p,q)=Σ cᵢⱼ pⁱqʲ` with frozen support

`(i,j) = (0,0),(0,2),(0,4),(1,1),(1,3),(2,0),(2,2),(2,4),(3,1),(3,3),(4,0),(4,2),(4,4)`.

The source products `p` and `q` are binary-linear functions of the two canonical code words. In characteristic two, `p²` and `p⁴` remain linear in those bits; `p³=p·p²` and `p⁵=p·p⁴` have degree at most two. The same holds for powers of `q`. After multiplying each displayed term by `p`, its combined code degree is at most three. In the field, `pF=0` is equivalent to `F=0` whenever `p≠0`. At `p=0`, the scaled equation is identically zero, so that branch must be excluded or checked against `F` separately. The hybrid experiment retains `F` as well as `pF` and therefore has exactly the original solution set even at `p=0`.

The N41 panel uses `EC1N41Ckb1h7d5e80d3c4d0`, `GF(2)[u]/(u^41+u³+1)`, seed `112`, rotations `(12,24)`, ten second-code bits, and a five-free-bit first-code block with offset `224`. Its positive residual `(1434452595080,1460136977354)` is the right two-pair sum of the independently replayed N41 public five-pair relation. Its paired ordinary residual is `(1537610160516,1106209404072)`. The N131 panel uses `EC1N131Ckb1heb5f1998f20b`, `GF(2)[u]/(u^131+u^13+u²+u+1)`, seed mask `898618`, rotations `(0,18)`, all 32 second-code bits, and first codes `0..15` with four bits free. The positive pair is `(3,16722)`; the ordinary row is the frozen public raw point in the [source coefficients](../n131_w33_freecode_resultant_20261018/coefficients.json). These are two-pair component blocks, with `candidate_id: null`.

## Frozen finite and formal checks

The [rank scan](result.json) built the exact ANF for both target rows in both fields. Among the 655 N131 equations formed by the 131 original coordinate equations and their four first-bit multiples, the degree-at-least-four coefficient matrix has rank **524**, leaving **131 independent cubic consequences**. Its degree-at-least-three matrix has full rank 655, so no degree-two consequence occurs in that multiplier span. The N41 width-five ranks are 205 of 246 above degree three and 246 of 246 above degree two. The scan checked 129 direct finite-field evaluations per row before ranking.

The [scaled profile](profile_result.json) exhaustively evaluated all `32×1024=32,768` N41 code assignments per target row and found `p≠0` throughout the chosen first-code block. It matched the positive row's one zero and ordinary row's zero zeros before and after scaling. On each N131 row it checked 4,096 seeded assignments plus the known positive pair. Every nonzero-`p` assignment preserved the zero decision; sampled `p=0` assignments are counted separately in the receipt, rather than classified as valid scaled hits.

The [Lean module](DegreeFall.lean) proves nonzero-product zero-set equivalence, the zero-product exception, fourth-power additivity in characteristic two, fourth-power linearity for an idempotent code bit, and the 13-term scaled support degree check. Its pinned Lean 4.34.1 build and `#print axioms` output are in [lean.stdout](lean.stdout); the declarations use only standard `propext`, `Classical.choice`, and `Quot.sound` foundations, with no proof placeholders. The [proof map](PROOF_MAP.md) records the remaining formal bridge from the abstract degree facts to the complete quotient-field ANF implementation.

## Solver measurements and statuses

Every new Sage job used the checked repository launcher, with [runtime information](sage_runtime_info.json) saved before the workloads. Each run used one solver child, a monitored 4-GiB combined-RSS cap, and a 120-second N41 or 600-second N131 parent wall cap. The [N41 cubic gate](n41_gate.json) and [N41 hybrid gate](hybrid_n41_gate.json) hash-bind the completed positive and ordinary controls to the archived independent relation replay.

| Formulation and frozen block | Positive row | Paired ordinary row | Peak combined RSS on positive row |
| --- | --- | --- | ---: |
| Prior quartic, N41 width five | `GB_COMPLETE`, 38.65 s | `GB_UNIT_IDEAL`, 32.90 s | See prior receipt |
| Standalone cubic, N41 width five | `GB_COMPLETE`, 15.74 s, codes `(253,63)` | `GB_UNIT_IDEAL`, 15.79 s | 365,576,192 B |
| Hybrid quartic plus cubic, N41 width five | `GB_COMPLETE`, 24.93 s, codes `(253,63)` | `GB_UNIT_IDEAL`, 20.11 s | 365,608,960 B |
| Prior quartic, N131 width four | `GB_COMPLETE`, 426.50 s, codes `(3,16722)` | `GB_UNIT_IDEAL`, 335.48 s | 2,250,686,464 B |
| Standalone cubic with `p=0` guard, N131 width four | **`RSS_CAP`**, 395.09 s | Gated | 4,295,098,368 B |
| Hybrid quartic plus cubic, N131 width four | **`RSS_CAP`**, 429.37 s | Gated | 4,306,124,800 B |

The prior quartic values come from the [degree-order panel](../joint_block_order_20261018/RESULT.md); they were recorded in separate ordinary-host runs. The N41 wall differences are stage observations, not isolated paired speedups. The two N131 capped rows have no completed Gröbner basis or decoded code result; their exact stdout, stderr, and monitored receipts are retained. Both N131 public-block runs in this experiment were gated after the corresponding positive resource failure. `RSS_CAP` is a resource outcome for this solver configuration, not an unsatisfiability result or a relation-yield estimate.

## Next algorithmic test

The full positive width-four block has a known first code with low bit one. The next controlled branch is to fix that bit to one, remove the exceptional `p=0` code without a degree-four nonzero guard, and test the pure cubic equations on the resulting eight-code N131 block. The other nonzero branches must then be covered by the same explicit policy and charged before a full two-pair oracle is considered. A useful promotion requires whole-family rejection or reusable elimination across far more first codes per query; serial width-four block solving cannot cover the W29/W33 source inside the one-worker, 600-second relation gate. The original ECC2K-130 objective remains the frozen N131 ordinary public-point relation, followed by rank, target descent, independently verified scalar recovery, and same-point isolated rho comparison.
