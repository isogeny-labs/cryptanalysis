# CT150 — q223 cubic source is not a prime-field base change

15 November 2026, America/Denver. Scientific standing: **[pcc:unverified]**. This is an exact integer/Frobenius calculation **conditional on the source-reported group orders and cubic field model**, not a new native transfer, independently certified point count, or measured attack.

## Why the source-field distinction matters

CT126 `primitive-pricing-01/src/main.rs` identifies source characteristic **223**. The established Jacobian/Weil-restriction model has extension degree **three**, so the relevant elliptic group is over `K=F_(223^3)`, not `F_223`. This follows the original whole-chain source and root [MAP_NORMS_AND_DEGREES_01](https://github.com/isogeny-labs/crypto/blob/research/chained-jacobian-transfer-20261110/research/chained_jacobian_transfers_20261110/evidence/public-n4-complete-chain-checkpoint-01/08-MAP_NORMS_AND_DEGREES_01.md). The reported source orders are those already audited as **reported integer inputs**, not independently point-counted, in CT149.

An elliptic curve `E0/F_223` has integer Frobenius trace `t` with `|t|<=29`, and its cubic-base-change trace is

```
t3 = t^3 - 3*223*t.
#E0(F_(223^3)) = 223^3 + 1 - t3.
```

The test exhausts **all 59 admissible integral values of t**, not a sampling or probabilistic search.

| Reported cubic source | #E(K) | Cubic trace | Closest cubic trace of an F223 base change | Minimum gap | Can arise from F223 elliptic base change? |
| --- | ---: | ---: | ---: | ---: | --- |
| Original fixed | 11,092,292 | -2,724 | -2,612 (t=4) | 112 | No, conditional on reported #E(K) |
| Fixed nu12 | 11,086,844 | +2,724 | +2,612 (t=-4) | 112 | No, conditional on reported #E(K) |

Consequently, **if the reported point counts and cubic-field interpretation are correct**, neither elliptic source curve can be isogenous **over F_(223^3)** to the cubic base change of any elliptic curve defined over F_223. Isogenies preserve the point count over a common finite field. This does **not** preclude a Weil-restriction/Jacobian over F_223: in that representation `Res_(K/k) E(k)=E(K)` by definition.

The Hasse bound for an elliptic curve **over F_223** gives `#E(F_223)<=253`. Both reported prime subgroup orders (2,773,073 and 2,771,711) are larger than 253. These source groups therefore cannot themselves be elliptic prime-field groups at characteristic 223. The q223 timing work is a cubic-extension ECDLP fixture even though the destination Jacobian is defined over the prime field. This scope distinction is crucial when assessing the owner's original **arbitrary prime-field ECDLP** goal.

## The separate 2-primary qualification

Under the root's **conditional** polarized quotient diagram, `deg(phi)=8`. A degree-169 elliptic isogeny over the cubic field induces degree `169^3=4,826,809` on its three-dimensional Weil restriction. Therefore an actual composite homomorphism `phi o Res(gamma)`, if defined and compatible as claimed, has geometric degree

```
8 * 169^3 = 38,614,472.
```

For each reported order `#E(K)=4 ell`, the exact integer checks are:

| Model | gcd(ell, 8*169^3) | gcd(4ell, 8*169^3) |
| --- | ---: | ---: |
| Original fixed | 1 | 4 |
| Fixed nu12 | 1 | 4 |

The standard finite-kernel argument therefore gives **injectivity on the prime ell-subgroup**, conditional on an actual geometric group homomorphism with the stated degree and exact source order. It **does not** establish injectivity on the whole 4ell group, because the degree-8 quotient can interact with its two-primary torsion. A gcd greater than one signifies lack of a guarantee, not demonstrated collisions.

This extends CT149's 13-primary elliptic-hop check to the explicitly assumed **degree-8 quotient and dimension-three degree**. It does not certify the real q223 encoded maps, a rational/inseparable scheme-theoretic morphism or a usable inverse algorithm. Even injectivity on a subgroup does not prove that the result is computationally cheaper.

## Executed arithmetic and falsification

Developer-local Python 3.13.5:

```sh
python3 experiments/chained-transfer-public-target/norm-point-reuse-01/ct150_cubic_source_scope.py > /tmp/ct150-normal.json
python3 -O experiments/chained-transfer-public-target/norm-point-reuse-01/ct150_cubic_source_scope.py > /tmp/ct150-opt.json
cmp /tmp/ct150-normal.json /tmp/ct150-opt.json
```

Normal and optimized output matched byte for byte in local execution; JSON SHA-256: `3997570c8a9ecd254984433164561a4e254bf7982b4b3d28da327cf4c0c7df9c`. Both alleged source traces fail every allowed prime-field cubic-trace case. Controls reject wrong recorded cofactor and composite base characteristic; the artificially constructed `t=4` trace polynomial is positively recognized as an eligible cubic base change. The controls check arithmetic statements only; a curve for the synthetic positive example was not constructed. No hosted CI/PCC signature or native group-order replay has been claimed.

## Research consequence and next discrimination

This is a **source-scope obstruction**, not an impossibility theorem for transfers from E(F_p). A genuine prime-field target should be chosen independently (for example the existing 2^31-1 baseline), with its own full original curve identity, prime-order subgroup, and a new explicitly computable injective transfer. The currently exhibited cubic-source group cannot silently be relabeled as an arbitrary prime-field ECDLP.

Meanwhile the original q223 norm-point optimization still needs admitted **same-host native C169, C13a, C13b and D** timing, independently checked full 695/701-record parity, and a complete cold same-public-target comparison against the fastest matched source rho, BSGS and IC. All setup/transport/LA/verification/RSS, confidence intervals, root ledger/CI and signed PCC remain gated. There is no authorization here for a paid run and no claim of full-solve advantage. [pcc:unverified]

**Sources:** root crypto #3877 and frozen 00/08 fixture; cryptanalysis #1589 CT149, #1534 CT126 source, #1533 prospective norm-reuse protocol; standard elliptic Frobenius trace recurrence (Silverman *Arithmetic of Elliptic Curves*, V) and Weil restriction's functor-of-points identity. KB MCP and checkout-local CLI unavailable, so no novelty or prior-art absence claim.
