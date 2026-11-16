# CT39 — Two-field Frobenius fingerprint for the actual T0/T1/T2 sextics

**Scope/standing:** fixed public F_101 genus-two models, two independent bounded point counters; **[pcc:unverified]**. This is a necessary isogeny-class screening certificate, **not** a geometric kernel, selected correspondence, DLP solver or cost improvement.

## Input models and point counts

All sextics are coefficient vectors **constant first**, with leading coefficient 1 and gcd(f,f')=1 in F_101[x]. The quadratic extension is F_101[u]/(u²-2), irreducible since 2 is a nonsquare mod 101. A monic even-degree sextic has **two rational points at infinity** over both fields.

| Model | f coefficients (constant-first) | #C(F101) | #C(F101²) | #Jac(F101) |
| --- | --- | ---: | ---: | ---: |
| T0 | 31,75,74,54,71,55,1 | 120 | 10436 | 12317 |
| T1 | 95,26,19,27,94,91,1 | 120 | 10436 | 12317 |
| T2 | 95,93,43,39,92,17,1 | 120 | 10436 | 12317 |
| mutation T0 (coefficient of x +4) | 31,79,74,54,71,55,1 | 120 | 10314 | 12256 |

These values are unsigned, directly reproducible local arithmetic observations **[pcc:unverified]**.

For a smooth genus-two curve C over F_q, put N_k=#C(F_(q^k)), s_k=q^k+1-N_k. Its Frobenius characteristic polynomial is
`P_C(T)=T^4+a_1 T^3+a_2 T²+q a_1 T+q²`, with
`a_1=-s_1=N_1-q-1`, `a_2=(s_1²-s_2)/2`.
Thus N1=120 gives a1=18 and N2=10436 gives s2=-234, a2=279. For all three actual models,
`P_C(T)=T^4+18T³+279T²+1818T+10201
        =(T²+7T+101)(T²+11T+101)`.
Evaluating P_C(1) gives 12,317=109*113.

The **independently counted** mutant has N1=120 but N2=10314; its polynomial is
`T^4+18T³+218T²+1818T+10201`, with P(1)=12,256. Equal F_101 curve-point counts do **not** fix the genus-two isogeny class; the second extension count distinguishes this concrete smooth negative control. [pcc:unverified]

## Geometric interpretation and limits

By the finite-field isogeny classification (Tate/Honda-Tate), equality of the **complete** Frobenius polynomials identifies the abelian-variety *isogeny class*. Hence each of these actual Jacobians lies in the F_101-isogeny class of E109 × E113, with elliptic factor polynomials T²+7T+101 and T²+11T+101. No *new simple F_101-isogeny factor* appears among T0/T1/T2; every same-field homomorphic chain of these three Jacobians stays in this split isogeny class. This agrees with (but does not derive) the earlier native correspondence claims and CT37's separate no-cross-factor-Hom result. [pcc:unverified]

For a candidate target A/F_101 receiving a **nonzero algebraic homomorphism** from either fixed elliptic factor, its characteristic polynomial must share the appropriate elliptic factor. This necessary spectral test does not establish an efficiently computable map, injectivity on the intended ECDLP subgroup, the geometric kernel, the selected dual, or the cost of solving a logarithm **in a different representation**. It does not exclude extension-field or characteristic-changing computational procedures not modeled by F_101 abelian-variety homomorphisms.

## Independent arithmetic and reproduction

- Python enumerates 101² extension-field x-values using the norm character `chi_101²(z)=chi_101(N(z))`; separately checks this identity against Euler exponentiation on **all 10,201 field elements**, counts F_101 points, checks gcd(f,f')=1 for all four sextics, and reconstructs each degree-four polynomial.
- Independent Go code builds separate square-membership tables for all F_101 and F_101² elements, then enumerates the same curve equations. This does not call Python or any native producer Jacobian engine.
- Negative control changes only the coefficient of x from 75 to 79 and is itself smooth. It preserves N1=120 but changes N2, a2 and #Jac.
- Original target data came from crypto #3877 and its T2 checkpoint; CT37/CT38 source and cryptanalysis #1501/#1505 were inspected. The existing root route graphs remain unchanged, because this audit does not construct a new map.

Reproduce:

```sh
python3 -B experiments/chained-transfer-reference/ct39/ct39_zeta_fingerprint.py > /tmp/ct39.normal
python3 -O -B experiments/chained-transfer-reference/ct39/ct39_zeta_fingerprint.py > /tmp/ct39.optimized
diff -u /tmp/ct39.normal /tmp/ct39.optimized
python3 -m py_compile experiments/chained-transfer-reference/ct39/ct39_zeta_fingerprint.py
go run experiments/chained-transfer-reference/ct39/ct39_zeta_independent.go
```

Local checks passed on Python 3 and Go; Python normal/-O stdout identical. Python source SHA256 `5dc72b7df6f9a487c6d8b0effbf7765208fe9fcd314c247797ce1afc6a41f096` and stdout SHA256 `ac43b949d503bed9123c59a7e898b5892a1e37d7cfc755ab360fa2a473d85196`. These hashes are integrity aids, not a PCC verdict. Exact-head CI must be read separately from these local observations. **[pcc:unverified]**

## Sources and next acceptance gate

- Repo prior art: `cryptanalysis:tools/transfer-audit/THEOREMS.md` §2 already states the general Frobenius-gcd/Hom criterion; CT39 instantiates the actual three fixed sextic models, not a new theorem.
- LMFDB reviewed entry, [Honda–Tate theorem](https://www.lmfdb.org/knowledge/show/av.fq.honda_tate): P_A divides P_B iff A is isogenous to an abelian subvariety of B.
- Tate, *Endomorphisms of abelian varieties over finite fields* (1966), [primary text](https://pazuki.perso.math.cnrs.fr/index_fichiers/Tate66.pdf).

Shared research-KB MCP, locked autoresearcher atlas, EKS/S3 live-budget admission and signer were not available in this runtime. No novelty claim and no paid job.

**Next discriminating gate:** combine the verified model spectra with actual native Phi2/Psi2 correspondence, degree, geometric 7-kernel and dual proof (including exceptional nonsplit/ramified divisors), rather than inferring these from the common isogeny class. The independent 12,317-class Cantor replay remains a separate needed test, and rho/IC cold-cost comparisons require the frozen approved protocol and budget.
