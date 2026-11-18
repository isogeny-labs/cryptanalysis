# CT190 — block-wide latency can spoof the randomized physical crossover estimator

2026-11-17 UTC · **[pcc:unverified]** · draft [cryptanalysis #1732](https://github.com/isogeny-labs/cryptanalysis/pull/1732)

## New precise finding

The merged CT188 seven-column log-time model controls for treatment period and first-order preceding treatment but **omits eight independent block intercepts**. A source-only counterexample gives *identical intrinsic A and B costs* while each of a packet's eight blocks has a common multiplicative startup/load factor applied identically to **both** actual routes. Because sequence and block are not orthogonal for the original seven-column regression after including carryover nuisance columns, this can give a **1.50× false positive direct/retained ratio**, with a zero within-block A/A log drift.

This is an omitted-variable falsification on intentionally engineered synthetic times, not an observation about hardware, a flaw in the underlying isogeny arithmetic, or evidence that a faster ECDLP method exists.

For each fixed public packet `p` and one of eight blocks `b`, write the first-four-slot model as

```
log(T[p,b,i]) = alpha[p,b] + period_effect[p,i]
              + beta_B[p] * B[b,i]
              + beta_previous[p] * previous_B[b,i]
              + beta_interaction[p] * (B[b,i] * previous_B[b,i])
              + error[p,b,i] .
```

The original seven columns omit `alpha[p,b]`. With eight block intercepts added, the exact rational model matrix has **rank 14/14 for every one of the 48 frozen packets**. Removing the within-block mean from both log durations and six varying predictor columns cancels *any* additive log-block offset exactly, leaving six identifiable columns (exact rational rank 6/6). For an exact error-free model this recovers `beta_B`, regardless of the eight block offsets. This mathematical statement is conditional on the modeled log-additive nuisance and does not establish causal identification against arbitrary higher-order effects.

## Source-only evidence

On source/workflow commit `f3ed3ee7a856c0600d75ad1fe907bc22798b1a5b`, [CT190 scoped Actions run #44165880160](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44165880160), job `134331664810`, completed **success**. Decoded job logs report **5/5 Python normal and 5/5 Python -O tests passing**. All full-roster inputs are generated synthetic durations (2,304 positions); zero physical native runs occurred. [pcc:unverified]

| Fully synthetic condition | Original CT188 diagnostic | New CT190 block-fixed diagnostic | Final A/A |
|---|---:|---:|---|
| Equal A/B, uniform cost | 1.00× | 1.00× | no drift |
| Equal A/B, common block startup factors | **1.50× spurious** | **1.00×** | no drift |
| Actual programmed direct/B 1.25× with block offsets and first-order carryover | distorted by omitted offsets | **1.25×**, carryover recovered | no drift |

The crafted block offsets are determined by the exact seven-column projection weights for the eight sequence instances: `(-53, 11, -11, 11, 53, -11, -11, 11)/284`, squared norm `793/10082`. For each packet, the weights follow the packet's shuffled sequence, not absolute block index. This is an adversarial **possibility** test, not an estimate of the distribution of cold-start noise. Programmed 1.15 prior-B and 1.08 interaction factors are also recovered in the new estimator's synthetic positive control.

The code also rejects population truncation, extra records, wrong physical treatment, zero duration and Boolean timing substitution, via CT188's unchanged complete-record/roster validation. Test code and source are committed separately from the earlier prospective [protocol](CT190_BLOCK_FIXED_EFFECT_PROTOCOL.md).

Reproduction from the exact-source checkout:

```bash
root=experiments/chained-transfer-public-target/primitive-pricing-01
python3 -S -m unittest discover -s "$root" -p 'test_ct190_block_fixed_effect_diagnostic.py' -v
python3 -O -S -m unittest discover -s "$root" -p 'test_ct190_block_fixed_effect_diagnostic.py' -v
python3 -S "$root/ct190_block_fixed_effect_diagnostic.py"
```

## Operational disposition

CT189's offline reader **still calls CT188's original seven-column estimator**. CT190 is intentionally a separately versioned source-only diagnostic; source integration into CT189 or actual native pricing must be prospective, reviewed, and separately tested. Do not relabel the existing v3 contract or publish its legacy treatment ratio as block-robust. A/A equality does not establish the absence of blockwise sequence confounding; randomization mitigates but does not mathematically rule out this risk with only eight finite sequences per packet.

The broader inherited repository CI has several failing workflows on the scoped source commit; a green CT190-only workflow is **not** broad CI/PCC approval. PR remains draft and scientific standing remains [pcc:unverified]. No original 695/701-record authentication, native 48-packet parity, paid EKS/Spot/GPU, actual `C169,C13a,C13b,N2_actual,D` prices, complete cold prime-field public-target logarithm recovery, matched rho/BSGS/IC solve or signed independent PCC occurred.

The next meaningful speed experiment is the authorized native norm-reuse derivative with actual N2 (not a proxy doubling), true paired physical A/B timing, and the all-phases cold single-target solver comparison. Use both treatment readers as a falsification pair and preserve any negative performance result.
