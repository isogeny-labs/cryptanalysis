# Target-advice cardinality required by N131 two-pair completion

**A three-pair proposal method with 20 million fixed proposals per target-advice value needs at least 35 bits of advice before its exact coverage upper bound permits 50% success on a uniform N131 subgroup target.** Even granting a perfect two-pair completion oracle, 32 advice bits permit at most 7.504% coverage under this model. The bound gives a concrete target-conditioning threshold for the next partial-sum design; it does not assume an implementation speed.

The exact curve is `EC1N131Ckb1heb5f1998f20b` over `GF(2)[t]/(t^131+t^13+t²+t+1)`, `y²+xy=x³+1`, subgroup order `r=680564733841876926932320129493409985129`, cofactor four. The audited W18 source contains `S=34482792912` signed distinct-column pair states. Two different pair states give at most `M=binom(S,2)=594531503488697323416` group sums; collisions and cross-pair column restrictions reduce this number. The common-Frobenius transformation used for the frozen public point is invertible on this prime-order subgroup, so it preserves the declared uniform-target law.

## Bound and proof

Let `a(Q)` be target-derived advice taking at most `C` values. For each advice value, the method fixes at most `k` three-pair proposals. A perfect two-pair completion of one proposal can hit at most `M` targets. Thus the union of all completion sets for one advice value has size at most `kM`. Every successful target is in the union over all `C` advice values, regardless of how the advice partitions the target space. For a uniform subgroup target,

`Pr[success] ≤ min(1, CkM/r) ≤ min(1, 2^b kM/r)` when `C≤2^b`.

This remains valid if the proposal sequence uses only yes/no completion feedback: before the first hit, its proposal sequence follows the all-negative path fixed by the advice value. Richer target-dependent output from the completion oracle, target-dependent proposals within a branch, or another target side channel fall outside the bound's model.

The [Lean theorem](AdviceBound.lean) `AdviceBound.successful_targets_le` proves the central finite counting implication for arbitrary target and advice types: if the target list has no duplicates, each target's advice lies in the declared code list, and each code's completion list has length at most `K`, then the successful-target count is at most `codes.length * K`. `reachable_length_le` and `selected_mem_reachable` supply the length and membership steps. The exact N131 source-to-`K=kM` and finite uniform-probability bridges are written here and remain outside the concrete Lean model; the [proof map](PROOF_MAP.md) states that formalization boundary.

| Fixed proposals `k` per advice value | Minimum advice values before 50% is permitted | Minimum bits `b` | Bound with 32 bits | Bound with minimum bits |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 572,353,802,824,861,734 | 59 | 3.7520×10⁻⁹ | 0.50359 |
| 20,000,000 | 28,617,690,142 | 35 | 0.07504 | 0.60032 |
| 600,000,000,000 | 953,924 | 20 | 1 | 0.54961 |

The 600-billion proposal row is a deliberately generous hypothetical one-billion-calls-per-second, 600-second ceiling, not a measured N131 worker. The table's `1` means the upper bound is vacuous at that bit count. The [exact integer result](count_result.json) retains every numerator and denominator and the 8-, 16-, 20-, 32-, 35-, 59-, and 60-bit panels. A minimum bit count says only when this necessary bound stops excluding 50%; it is not a success prediction.

## Frozen evidence and next experiment

The [protocol](protocol.json) binds the earlier N131 source and completion-count receipts, calculation code, and Lean source by SHA-256. The [read-only verifier](verify.py) recomputes all thresholds and rational numerators. Lean 4.34.1 built the theorem with `#print axioms` showing only `propext`, `Classical.choice`, and `Quot.sound` for the central result; `lean4checker --fresh` was unavailable. The initial arithmetic calculation preceded a stronger success-count theorem, so its [preproof protocol](protocol_preproof.json) and [preproof count](count_preproof.json) are retained separately; the current result was recomputed against the strengthened source.

The next constructive test should make the public point eliminate or select whole **joint two-partial-sum families** before pair-mask expansion. On the frozen N41 public point, freeze an unpinned input law and measure exact family rejection, total proposal cost, and independently replayed ordinary relation yield. For N131, the proposed selector must have a source-bound path within one worker, 600 seconds, and 4 GiB; the advice threshold is a necessary cardinality gate for any fixed-proposal branch method. This stage has `candidate_id: null`.
