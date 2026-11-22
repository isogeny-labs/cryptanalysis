# CT164 — rational 2-torsion screen for the fixed-nu12 degree-eight quotients

2026-11-16 · **[pcc:unverified]** · Retrospective mathematical replication of an exploratory local finite-level calculation. No paid compute, native Jacobian replay or PCC signature.

## New finite result

Let k=F_223, K=F_(223^3), E/K the **actual fixed nu12 elliptic endpoint** from CT160, and A=Res_(K/k)(E). CT160 reports

- #E(K)=11,086,844=4·2,771,711, with all four E[2] points K-rational and no K-rational point of order four;
- K-Frobenius trace T=2724;
- CT163 exhaustively enumerated **nine** Frobenius-stable maximally isotropic subgroups H of A[2]: three factorwise and six mixed.

For **every one of these nine exact CT163 kernels**, the abstract principally polarized degree-eight quotient B=A/H has

`#B(F_223)[2] = 2`.

Because B is k-isogenous to A, `#B(k)=11,086,844`; hence the 2-Sylow subgroup of B(k) is **cyclic of order four**, not (Z/2)^2. This is a mathematical finite-module consequence under the inherited CT160/163 source identities, **not** construction of a smooth genus-three curve or DLP algorithm. [pcc:unverified]

### Mathematical derivation (finite computation plus two standard lemmas)

Write `pi` for K-Frobenius on the 2-adic Tate module T2(E). Full rational E[2] means `pi=I+2M (mod 4)`. Rational E[4] has exactly four points because #E(K) has 2-adic valuation two and E[2](K) already has four points. Therefore `det(M)=1 (mod 2)`. The trace identity `tr(pi)=2724 ≡0 (mod 4)` gives `tr(M)=1 (mod 2)`. Exactly **two** 2×2 binary matrices satisfy both conditions:

`[[0,1],[1,1]]` and `[[1,1],[1,0]]`.

In coherently Frobenius-transported Tate bases of the three conjugate geometric factors, k-Frobenius acts modulo four as

`F(v0,v1,v2)=((I+2M)v2,v0,v1)`.

For a CT163 maximal isotropic H subset (F2)^6, let `L'=2 Z_2^6 + lifts(H)`. The quotient B has 2-adic Tate lattice `(1/2)L'` inside the shared rational Tate module. Consequently `B[2]` is represented by `L'/2L'`, and

`#B(k)[2] = 2^(6-rank_F2(F-I | L'/2L'))`.

The primary Python checker constructs a systematic integral basis of this index-eight lattice and computes the rank over F2, obtaining **rank five** for all 9 kernels under both possible M. The independently structured Node checker instead enumerates **512** mod-4 lattice representatives, quotients by **eight** representatives of 2L', and counts Frobenius-fixed elements among the resulting **64** classes; it finds exactly two in each case. Both read and validate the actual checked-in CT163_RESULT.json rather than silently substituting unrelated kernels. Normal Python, Python -O and Node gave identical canonical JSON; five directed mutation controls were rejected per implementation in local untrusted execution. [pcc:unverified]

## Refined genus-three hyperelliptic filter

CT162 had four branch-orbit partitions of the eight hyperelliptic Weierstrass points compatible with the **Weil-polynomial mod-2 condition**. The new *actual even-degree quotient* condition requires two rational 2-torsion points, rather than relying on the inappropriate odd-degree preservation assumption:

| Branch Frobenius orbit lengths | #J(k)[2] from CT162 | Survives CT164's degree-eight quotient? |
|---|---:|---|
| 1 + 1 + 3 + 3 | 4 | No |
| 1 + 1 + 6 | 2 | **Yes** |
| 2 + 3 + 3 | 2 | **Yes** |
| 2 + 6 | 4 | No |

This is a **necessary** filter for a hyperelliptic genus-three Jacobian exactly isomorphic as the principally polarized k-abelian variety B=A/H. It does not apply to arbitrary other k-isogenies in the Weil class, nor to nonhyperelliptic plane quartics. The three factorwise H give product-polarized quotients, not genus-three Jacobians. The six mixed H still require explicit quotient geometry and indecomposable principal polarizations. [pcc:unverified]

## Evidence, reproduction, and known limitations

Exact frozen `CT164_RESULT.json`: SHA-256 `eb7651dca724b5ef15707b4b32eb8f510ab8f713811586cc3228d30399020508`. Input: CT163 `CT163_RESULT.json` (9 exact basis records). Scripts `ct164_quotient_two_torsion.py` (systematic lattice rank) and `ct164_independent_coset.cjs` (finite coset enumeration). Independent programs are still producer-authored and local runs are **not** signed PCC.

```sh
D=experiments/chained-transfer-public-target/norm-point-reuse-01
python3 -B "$D/ct164_quotient_two_torsion.py" --self-test > /tmp/ct164-py.json
python3 -O -B "$D/ct164_quotient_two_torsion.py" --self-test > /tmp/ct164-opt.json
node "$D/ct164_independent_coset.cjs" --self-test > /tmp/ct164-js.json
cmp /tmp/ct164-py.json /tmp/ct164-opt.json
cmp /tmp/ct164-py.json /tmp/ct164-js.json
cmp /tmp/ct164-py.json "$D/CT164_RESULT.json"
sha256sum /tmp/ct164-py.json
```

The exact-source bounded `.github/workflows/ct164-quotient-2torsion.yml` checks these comparisons in CI (check actual run status separately). Neither script performs elliptic/Jacobian native arithmetic, solves a public ECDLP, verifies the actual geometric quotient, measures any C169/C13/D primitive, nor produces a signed scientific PCC. A failed whole-corpus or paid owner-admission gate must **not** be bypassed. No existing frozen fixture, performance ledger or original project branch was changed.

### Scope and next decisive discriminators

1. Independently replay the **entire actual 695/701-record original/reuse Jacobian corpus**, including all exceptional records; only then, under existing owner admission/budget gates, measure paired same-host C169, C13-first, C13-second and D and source/reuse corrections. CT143's actual full headroom, `min(C169,C13a+C13b)-D`, can only be filled with those real costs.
2. For each mixed candidate that survives this necessary genus-three hyperelliptic screen, exhibit explicit smooth curve equations, polarization, and scalar-blind quotient evaluator, with the actual source field bound. CT161 still prohibits a nonzero k-homomorphism from **any k-elliptic curve** into the fixed-nu12 Weil restriction or its k-isogenous quotients. This source-specific obstruction means an explicit genus-three model alone cannot satisfy the owner's required *prime-field elliptic-input* transfer.
3. Compare a genuinely **complete cold single-target prime-field ECDLP solve** against matched optimized rho, BSGS and index calculus with setup, mapping, corrections, linear algebra, verification, process wall/RSS, uncertainty and independent PCC. No improvement ratio is asserted here.

### Research sources checked

- Source: CT160/161/162/163 reports and exact frozen results in this directory; [root crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877); native norm reuse [cryptanalysis #1533](https://github.com/isogeny-labs/cryptanalysis/pull/1533); source pricing [#1562](https://github.com/isogeny-labs/cryptanalysis/pull/1562); concurrent explicit higher-genus work [crypto #4357](https://github.com/isogeny-labs/crypto/pull/4357).
- Howe, Leprévost and Poonen, *Large torsion subgroups of split Jacobians of curves of genus two or three*, Forum Math. 12 (2000), 315–364, [arXiv](https://arxiv.org/abs/math/9809210), prior gluing context.
- Costa, Donepudi, Fernando, Karemaker, Springer and West, *Restrictions on Weil Polynomials of Jacobians of Hyperelliptic Curves*, [DOI](https://doi.org/10.1007/978-3-030-80914-0_7), for CT162's necessary branch-orbit screen.

Research-KB interface unavailable in this connector session; used original repository sources and primary literature instead. No novelty, best-performance or general no-transfer claim. **[pcc:unverified]**
