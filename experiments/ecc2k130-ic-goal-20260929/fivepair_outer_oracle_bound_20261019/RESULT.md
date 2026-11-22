# Exact N41 right support and W29 outer-proposal coverage bound

The unpinned N41 five-pair source has **1,258,720 distinct compatible right two-pair sums from 1,258,720 compatible ordered pairs**. A hash-set census and an independent sorted-vector replay agree on every count. Instantiating the previously proved target-advice counting theorem for the N131 W29 mask capacity gives a necessary condition for any method that fixes outer three-pair proposals and then calls a perfect two-pair completion oracle: with **one proposal per advice value**, 68 advice bits cannot make its uniform-subgroup success upper bound reach one half; **69 bits** is the first arithmetic threshold. Even granting **20 million fixed proposals per advice value**, the threshold is **44 bits**. This identifies the amount of target-dependent joint selection that a fixed-outer design must replace or supply before the fast native two-pair filter can contribute to the complete relation search.

## Exact N41 support measurement

The N41 curve is `y²+xy=x³+1` over `GF(2)[u]/(u^41+u³+1)`, ID `EC1N41Ckb1h7d5e80d3c4d0`, subgroup order `549756390943`, cofactor four. The archived width-11 source has 281 valid canonical codes and four signed states per code, hence 1,124 states in each of five Frobenius-rotated slots. Its frozen native join independently found and Sage-replayed an ordinary relation on the public raw point after 396,919 probes.

The [hash-set census](run_v2_result.json) reread the frozen `join_input.tsv`, checked every source point and all 128 archived Sage addition triples, then inserted every compatible ordered sum of slots 3 and 4 into a set keyed by full curve point. It counted 1,258,720 compatible pairs, 4,656 rejected pair combinations, **1,258,720 distinct sums**, and zero duplicate pairs. The [sorted-vector audit](audit_result.json) independently sorted all compatible full-point sums and obtained the same result. The parent intervals were 1.167 and 0.886 seconds, with raw child peak RSS 75,579,392 and 31,997,952 bytes. Both used one process, a 120-second parent timeout, and a post-run peak check below 4 GiB on an ordinary host.

For a hypothetical uniformly random **raw** N41 target, one fixed outer triple can land in this exact right-sum set with probability `1,258,720 / 2,199,025,563,772 ≈ 5.724×10⁻⁷`. The archived public target is fixed, and its observed 396,919-probe hit is a relation control rather than a sample from that uniform-target law. The first supervisor attempted to set a 4-GiB address-space limit and failed in `preexec_fn` before worker startup; [attempt 1](attempt1.json) is retained. The revised supervisor imposed the wall timeout and checked the completed child's peak RSS.

## W29 counting implication

The N131 curve is `y²+xy=x³+1` over `GF(2)[u]/(u^131+u^13+u²+u+1)`, ID `EC1N131Ckb1heb5f1998f20b`, with prime subgroup order

`r = 680564733841876926932320129493409985129`.

The canonical W29 source has at most `2^28` raw source codes and at most four signed pair states per code. Hence each of two rotated right slots has at most `S=4·2^28=2^30` states. Their ordered two-pair sum set has at most `M=S²=2^60` distinct subgroup points. Different rotations and column restrictions can only decrease this ceiling. This bound uses the **prime subgroup** as the uniform target space after the declared cofactor projection; it does not assume that the frozen public point is randomly sampled from the raw curve group.

Suppose target-derived advice takes at most `C` values. For each advice value, a method fixes at most `k` outer three-pair proposals, and a perfect oracle reports whether the residual belongs to the right two-pair set. Across all targets, those fixed proposal branches cover at most `CkM` subgroup points. For a uniform subgroup target,

`Pr[success] ≤ min(1, CkM/r)`, and `C≤2^b` gives `Pr[success] ≤ min(1, 2^b kM/r)`.

| Fixed outer proposals `k` per advice value | Minimum advice bits before the **rigorous capacity** upper bound permits one-half success | Minimum bits using the **sample-rate projection** |
| ---: | ---: | ---: |
| 1 | **69** | 72 |
| 20,000,000 | **44** | 48 |
| 600,000,000,000 | **29** | 33 |

The 600-billion row is a deliberately generous proposal budget, not measured throughput. The actual [native quartic filter](../n131_native_quartic_filter_20261019/RESULT.md) classified a `2^20`-code public prefix in 7.204 seconds for **one fixed two-pair query**. Applying the sampled eligible-code fraction to the full W29 space projects about 68,308,992 eligible codes and 469 seconds for one serial eligible-list scan, excluding list preparation and all outer-slot work. Thus `k=1` is closer to this measured complete-filter granularity; the `k=20,000,000` row describes a much stronger hypothetical outer proposal engine.

The 65,536-mask source sample had 16,677 eligible pairs. Its observed fraction is 0.25447, with a descriptive Wilson 95% interval `[0.25115, 0.25782]` under the sample's pseudorandom-mask law. Scaling that fraction gives the **projection** of 68,308,992 eligible codes; the resulting 72- and 48-bit columns are conditional arithmetic, not a census-based bound. The [exact integer result](bound_result.json) retains all counts, numerators, denominators, thresholds, and the measured-rate projections.

## Proof and next algorithmic gate

The [proof map](PROOF_MAP.md) links the general coverage implication to the already checked Lean theorem `AdviceBound.successful_targets_le` and the new [Lean arithmetic instance](W29AdviceThreshold.lean), which verifies both sides of all six threshold rows with no axioms. The [terminal verifier](verify.py) checks 24 frozen source hashes, two N41 counting methods, the archived relation audit, the prior Lean theorem receipt, every exact integer threshold, the sample projection, and the new Lean output. Its [receipt](verification_result.json) records `PASS_TERMINAL_AUDIT`. `candidate_id` remains `null` because the source/selection method has no complete IC pipeline yet.

The bound applies to fixed outer proposals **within each advice value**, including a sequence that only learns yes/no completion feedback before its first hit. A method that uses richer target-dependent information to choose outer source codes can fall outside this model. The next constructive test should couple the public target to **multiple still-free outer pair codes** in one exact constraint and measure whole-family rejection on an unpinned N41 ordinary relation. Its N131 transfer needs an explicit 600-second, one-worker, 4-GiB path to an independently replayed ordinary relation before target descent and the same-point rho comparison.
