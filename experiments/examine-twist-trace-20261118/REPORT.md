# Quadratic-twist / Frobenius-trace ECDLP transfer audit (2026-11-18)

**Known-method negative control — [pcc:unverified].** This is a toy-scale regression of the closed twist/Frobenius obstruction in [IC mega-pass BRIEF](https://github.com/isogeny-labs/crypto/blob/main/research/ic_mega_pass_20261031/brief/BRIEF.md), **not** a novel attack or cryptographic-scale speedup.

## Fixed instance and exact maps

Over F_1009 let E: y²=x³+2x+25, #E(F_1009)=991 (prime); nonsquare d=11; and Eᵈ: y²=x³+242x+987, #Eᵈ(F_1009)=1029=3·7³. Both are exhaustively enumerated independently. Let K=F_1009[s]/(s²−11); extension isomorphism φ:E(K)→Eᵈ(K) maps (x,y)→(11x,11s·y), with inverse (X/11,Y/(11s)). It sends the rational source subgroup injectively into the *anti*-Frobenius eigenspace, NOT the smooth rational twist subgroup.

The source generator G=(0,5) has order 991. Trace t=19 gives #Eᵈ(K)=(1010)²−19²=1,019,739=991·1029. A full-order rational twist generator H=(3,76) has order 1029; φ(G) has order 991; H+φ(G) has order 1,019,739. The trace T=1+Frob has image Eᵈ(F_1009) of order 1029 and kernel φ(E(F_1009)) of order 991, hence **T◦φ=0 on every source point**. All source logarithms disappear in the smooth projection.

## Exact pass/fail obligations (producer-local)

| Obligation | Outcome |
|---|---|
| Source prime subgroup & curve validity | **PASS** — 991 points, order of G exactly 991 |
| Extension order and smoothness | **PASS** — 1,019,739=991·3·7³; rational twist 1029=3·7³ |
| φ subgroup preservation, kernel, image | **PASS** — kernel {O}, 991 distinct images, 1024 homomorphism pairs |
| φ inverse and roundtrip | **PASS** — all 991 source points roundtrip |
| Frobenius sign, trace kernel/image | **PASS** — all images anti-invariant, im(T)=1029, ker(T)=991 |
| Rational-twist trace inverse | **PASS** — [515]T(R)=R on all 1029 rational twist points |
| Global inverse for T | **FAIL** — nontrivial kernel |
| Transported original DLP | **PASS** — 64/64 seeded planted logs recovered with BSGS, original Q=[k]G checked |
| Smooth rational twist DLP transfer | **FAIL** — Tφ(Q)=O identically |
| Strictly cheaper full DLP | **FAIL** — no cheaper destination algorithm and mapped arithmetic greater |
| Independent signed PCC standing | **PENDING** — local checks do not constitute independent verification |

### Counted arithmetic, same BSGS algorithm and 64 targets

| Primitive | Direct Fp | Mapped Fp² |
|---|---:|---:|
| EC group calls | 4,289 | 4,289 |
| Underlying Fp multiplications | 14,982 | 95,395 |
| Underlying Fp additions | 23,685 | 81,431 |
| Underlying Fp inversions | 4,097 | 4,097 |

The mapped route also needs 2 base multiplications per mapped point (2 one-time for G; 128 for 64 queries) and 2 per optional inverse. Trace costs one group addition (plus conjugation). The inverse of trace **on the rational subgroup only** by [515] takes 12 group calls on H; it does not invert the lost 991-order kernel. The Pollard rho estimate sqrt(π·991/2)=39.45 is **heuristic**, not measured; no cold S or IC comparison was claimed.

### Provenance, reproducibility and limitations

Python 3 standard library, deterministic seed 20261118; 64 distinct exponents including 0,1,990; 991 source images/inverses; 1024 sampled homomorphism pairs; 1029 trace restricted inverses; two independently coded finite-field point counts; three mutation-rejection tests. Raw result digest SHA-256 `6244f00affb3bb5111d30c91a54c15a04068e1c44681729b8ffcc6346d4454b7` from the full local replay; code/summary in this directory are intended for independent rerun. No external preregistration, signed PCC verdict or execution attestation. [pcc:unverified]

**Falsifier:** a useful transfer must retain k in the smooth target and produce a source-verified log for less end-to-end cost (including map, inverse, setup, misses, solver). This attempt fails the *first* requirement algebraically.

**Sources:** [Magma handbook quadratic twists](https://magma.maths.usyd.edu.au/magma/handbook/text/1557); [IC mega-pass closure](https://github.com/isogeny-labs/crypto/blob/main/research/ic_mega_pass_20261031/brief/BRIEF.md); [transfer completeness gap](https://github.com/isogeny-labs/cryptanalysis/blob/main/problems/transfer-audit-completeness.md); [existing twist leakage tests](https://github.com/isogeny-labs/cryptanalysis/blob/main/experiments/ec-leakage-harness-20261114/leads/1-twist-leakage/README.md); [previous 2-isogeny control PR #1775](https://github.com/isogeny-labs/cryptanalysis/pull/1775).

**Next:** do not re-propose the closed twist mechanism; evaluate an explicit non-homomorphic curve cover/Jacobian correspondence left outside the conservation lemma. Conductor work-claim and research-KB services were not exposed in this runtime; GitHub conflicts searched, and the change scoped to a new experiment directory only.
