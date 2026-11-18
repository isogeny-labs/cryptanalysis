# CT199 — physical-route carryover estimand correction

2026-11-18 UTC. **[pcc:unverified]**. [Draft PR #1756](https://github.com/isogeny-labs/cryptanalysis/pull/1756). Frozen protocol: [CT199_CARRYOVER_STANDARDIZATION_PROTOCOL.md](CT199_CARRYOVER_STANDARDIZATION_PROTOCOL.md), committed `d5d4239fc7db14ccfd5cac98ac02520e4107fdf8` before implementation.

## Concrete mathematical correction

CT190 fits, for each selected public Jacobian packet and within one four-slot physical A/B block, a log-duration model

```
 log(t_i) = alpha_block + period_i + beta_B B_i + beta_z z_i + gamma B_i z_i
 z_i = 1 if the preceding physical operation in that block was B, else 0
```

Its historical displayed `exp(-median(beta_B))` is **a conditional A/B route ratio for z=0**. It is *not* automatically a roster-marginal ratio. At fixed prior operation z, the route contrast is `exp(-(beta_B + gamma*z))`. For an explicitly chosen standardization distribution P(z=1)=q, the model-standardized geometric ratio is `exp(-(beta_B + q gamma))` for each packet. We report medians over packets in log space, not a misleading per-process CI.

The frozen CT188 multiset `(AABB,ABAB,ABBA,BAAB,BABA,BBAA,ABBA,BAAB)` includes exactly **12/32 previous-B slots**, giving **q=3/8** identically for every one of the 48 packets, independent of block permutation. The shared prior-operation nuisance term `beta_z` cancels from each fixed-z route contrast. The new report keeps separate prior-A and prior-B ratios, a q=3/8 model-standardized ratio, and the old legacy alias with an explicit `previous_B=0; NOT marginal` label. The roster digest, 14-column rank, CT188 native producer, CT125 source and 48 public packets remain unchanged.

## Two independently derived source/synthetic falsifiers

For a deliberately programmed direct/retained factor of 1.25 with a further multiplicative **B-after-B** latency of 1.08 and common prior-B latency 1.15, the exact mathematical expectations are:

| Estimand | Programmed expectation |
|---|---:|
| Previous A | 1.250000 |
| Previous B | 1.25/1.08 = 1.157407 |
| CT188 roster standardized (q=3/8) | 1.25 / 1.08^(3/8) = 1.214440 |

With a nominal previous-A ratio of 1.05 and B-after-B penalty 1.7, the **direction of the inferred gain flips**: legacy conditional ratio is 1.05 (>1) while q-standardized ratio is **0.860540 (<1)**. These are analytic/synthetic constructions, not physically observed shocks or ECDLP gains. This is a conditional-model estimand issue, not an assertion that either transfer route actually exhibits a significant interaction.

An independent floating-point linear-algebra check using eight block indicators, three periods, B, z and Bz yielded rank 14 and coefficients `beta_B=-log(1.25)`, `beta_z=log(1.15)`, `gamma=log(1.08)`; the three analytical contrasts above agreed to floating-point precision. That check is separate from the repository Python source tests, not signed execution proof.

## Reproduce / status

```sh
D=experiments/chained-transfer-public-target/primitive-pricing-01
python3 -S -m unittest discover -s "$D" -p test_ct190_block_fixed_effect_diagnostic.py -v
python3 -O -S -m unittest discover -s "$D" -p test_ct190_block_fixed_effect_diagnostic.py -v
python3 -S -m unittest discover -s "$D" -p test_ct199_route_contrasts.py -v
python3 -O -S -m unittest discover -s "$D" -p test_ct199_route_contrasts.py -v
```

The implementation consists of `ct190_block_fixed_effect_diagnostic.py`, `test_ct199_route_contrasts.py`, and the existing CT190 scoped CI workflow. At report authoring, exact-head source CI was queued; **do not infer a passing result from this report**. No physical native measurement, paid compute, complete single-target solve or independent PCC occurred.

## Decision and experiment gate

Any actual native C169 vs two-C13 route price decision must state whether it is conditional on previous A, previous B, or standardized to a declared workload mixture; it must not silently substitute `exp(-beta_B)` for a marginal estimate. This correction does *not* eliminate higher-order treatment history, drift or block-order confounding, which need independent controls. Even a defensible route-time difference must enter the **complete cold single-target ECDLP** accounting against strongest matched rho/BSGS/IC, with original 695/701 custody, native parity, setup, target recovery, LA, memory, uncertainty and signed PCC. [pcc:unverified]

Sources: [CT188 #1725](https://github.com/isogeny-labs/cryptanalysis/pull/1725), [CT190 #1732](https://github.com/isogeny-labs/cryptanalysis/pull/1732), [CT198 #1748](https://github.com/isogeny-labs/cryptanalysis/pull/1748), [original crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877) and [queue #3904](https://github.com/isogeny-labs/crypto/issues/3904). Shared research KB unavailable, no novelty claim.
