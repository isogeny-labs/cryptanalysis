# Exact completion ceiling for target-independent triple proposals

**A target-independent triple proposal reaches at most `594,531,503,488,697,323,416` two-pair sums among `680,564,733,841,876,926,932,320,129,493,409,985,129` subgroup targets.** For a uniformly drawn N131 target this is at most **8.736×10⁻¹⁹**, approximately `2⁻⁵⁹·⁹⁹`, per proposal, even with a free and perfect two-pair completion oracle. At least **572,353,802,824,861,734** such proposals are necessary before the union bound permits a 50% success probability. This pins down the amount of target dependence needed by an output-first five-pair method.

## Source, input law, and counting proof

The exact curve is `EC1N131Ckb1heb5f1998f20b` over `GF(2)[t]/(t^131+t^13+t²+t+1)`, `y²+xy=x³+1`. The [audited W18 source](../n41_common_frob_factor_20261012/source_projection_result.json) contains `S=34,482,792,912` signed unordered distinct-column pair states at rotation zero. The prime-order subgroup has `r=680,564,733,841,876,926,932,320,129,493,409,985,129` elements. The checked [target transformation](../n41_common_frob_factor_20261012/n131_projection_result.json) has nonzero factor `1+λ¹⁶` and a verified inverse modulo `r`, so a uniformly drawn subgroup target remains uniform after transformation.

Fix a triple sum `T=P₁+P₂+P₃` independently of the target. A two-pair completion requires `Q′=T+A+B`, where `A` and `B` are distinct signed source pair states: the five-pair rule demands ten distinct folded columns. Since addition is commutative, there are at most `M=binom(S,2)=594,531,503,488,697,323,416` candidate sums `A+B`. Collisions and cross-pair column exclusions only lower this count. Thus at most `M` of the `r` possible targets complete this fixed proposal. For `k` proposals fixed independently of a uniform `Q′`, a union bound gives

`Pr[at least one completion] ≤ min(1, kM/r)`.

The bound also applies after conditioning on any target-independent random choices used to select the proposals; averaging preserves it. It concerns the declared uniform-target input law. A method that derives proposal families algebraically from the actual public point can correlate them with `Q′` and is the constructive direction left open by this calculation.

## Exact arithmetic receipt

The [protocol](protocol.json) froze source and target receipt hashes, the input law, and three proposal budgets before the [integer calculation](count_result.json). Its [read-only verifier](verify.py) recomputes every count and rational bound directly from those receipts. The [Lean module](Bound.lean) checks the ordered `kS²` representation count; [the proof map](PROOF_MAP.md) records the remaining finite-probability formalization.

| Target-independent proposal budget | Upper bound for uniform-target completion |
| ---: | ---: |
| 1 | 8.7358552967×10⁻¹⁹ |
| 20,000,000 | 1.7471710593×10⁻¹¹ |
| 600,000,000,000, an assumed billion proposals per second for 600 seconds | 5.2415131780×10⁻⁷ |

The last row is a deliberately generous hypothetical rate, not a measured N131 worker. Exact numerators and the common denominator are in [count_result.json](count_result.json). This is a mathematical work gate with `candidate_id: null`; it makes no local CPU speed comparison.

## Next algorithm gate

The previously audited [two-free-pair symbolic inverse](../n41_symbolic_two_bucket_20261011/RESULT.md) rejects fixed seed families exactly but pays one GCD decision per seed pair; its N131 W18 Cartesian has `68,718,952,449` seed pairs per raw target lift. A viable next method must choose or exclude many seed families **from the public target before that Cartesian expansion**, then demonstrate an unpinned N41 relation while two pair outputs remain free. The N131 promotion gate is a source-bound one-worker 600-second/4-GiB estimate followed by an ordinary relation and independent replay; factor logs, target recovery, and the same-point rho comparison follow the full goal.
