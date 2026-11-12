# CT33 — explicit prime-field polynomial for the nonbacktracking cyclic-49 kernels

**Scientific standing `[pcc:unverified]`.** This is an independently implemented *bounded* algebraic certificate for the previously selected **two consecutive degree-7 elliptic isogenies** over \(\mathbf F_{101}\). It is not an independently signed PCC result, a new general theorem, a genus-2 correspondence, or an ECDLP speedup.

## Sources and scope

- `crypto` PR [#3877](https://github.com/isogeny-labs/crypto/pull/3877), especially `research/chained_jacobian_transfers_20261110/evidence/elliptic-seven-witness-01.tsv`, supplies the first-stage normalized kernel polynomials and target curves.
- `cryptanalysis` PR [#1492](https://github.com/isogeny-labs/cryptanalysis/pull/1492), CT29–31, supplies the **nondual** second-stage kernels and backtracking negative controls.
- `cryptanalysis` PR [#1495](https://github.com/isogeny-labs/cryptanalysis/pull/1495), CT32, supplies independently checked Frobenius eigenline predictions, but **does not** explicitly construct the degree-49 support polynomial.
- Standard sources used: Vélu's odd-degree isogeny formulas; HLP (Howe–Leprévost–Poonen), [arXiv:math/9809210](https://arxiv.org/abs/math/9809210), for the existing gluing context; root `SEVEN_CHAIN_PROOF.md` for the global geometric identities. No novelty is claimed for polynomial pullback or Vélu itself. Shared research-KB tools are not loaded in this runtime; this is an explicitly limited literature audit.

## Constructive formula

Let \(E_0:y^2=f(x)=x^3+ax+b\), \(\alpha:E_0\to E_1\) be a normalized separable degree-7 isogeny, and \(h_0(x)\) be its monic degree-3 kernel polynomial. Define \(D=h_0^2\) and \(S_1=-[x^2]h_0\). Vélu's x-coordinate is \(X=N/D\), with the polynomial **entirely in the prime field**

\[
N=(7x-2S_1)D -2f'(x)h_0'(x)h_0(x)
  +4f(x)\bigl(h_0'(x)^2-h_0(x)h_0''(x)\bigr).
\]

For the next separable nondual 7-isogeny \(\beta:E_1\to E_2\), write its monic cubic kernel polynomial \(h_1(X)=X^3+c_2X^2+c_1X+c_0\). The **primitive 49-support** on \(E_0\) is the monic degree-21 polynomial

\[
H(x)=N^3+c_2N^2D+c_1ND^2+c_0D^3.
\]

The nonzero signed kernel of \(\beta\circ\alpha\) has 48 points in 24 x-pairs. Its x-support polynomial is

\[
K(x)=h_0(x)H(x),\qquad \deg K=24,\qquad D_{\beta\circ\alpha}=K(x)^2.
\]

Why cyclic, rather than \((\mathbf Z/7)^2\)? The inverse image of \(\ker\beta\) has order 49. Since \(\ker\beta\ne\ker\widehat\alpha=\alpha(E_0[7])\), the only 7-torsion in that inverse image is \(\ker\alpha\), of order 7. Therefore its group is cyclic of order 49. This relies on the kernel tests and standard separable-isogeny group facts; merely counting polynomial roots would not prove it. The kernel polynomials are **not** interpolated from discrete logarithm labels.

## Fixed F101 results (unsigned local executions)

| chain | first kernel \(h_0\), low-to-high | second kernel \(h_1\), low-to-high | target \(E_2=(a,b)\) | primitive \(H\) factor degrees | minimal x-support field |
|---|---|---|---|---|---|
| order 109 | `[72,100,35,1]` | `[99,94,75,1]` | `(59,27)` | `21` (irreducible) | \(\mathbf F_{101^{21}}\) |
| order 113 | `[59,46,8,1]` | `[53,19,40,1]` | `(23,7)` | `7+7+7` | \(\mathbf F_{101^7}\) |

**Primitive polynomial coefficients, low-to-high:**

- Order 109: `[9,78,22,78,88,78,90,64,94,74,63,12,66,63,87,78,67,69,81,60,83,1]`.
- Order 113: `[69,65,23,53,73,2,51,98,84,33,33,30,95,34,26,89,25,69,19,29,88,1]`.

The complete degree-24 polynomials \(K\), first-stage \(N,D\), orbit gcd counts and backtracking control counts are emitted as JSON by the Python oracle. An independently written Go implementation pins both degree-21 polynomials and recomputes the maps, coefficient identities, gcds, full degree-49 composite rational-function identity and Frobenius orbit checks. A third development-library spot check with SymPy `factor_list` gave 21 and 7+7+7. The latter is **not** signed independent scientific verification.

## Reproduction and negative controls

```sh
python3 -B experiments/chained-transfer-reference/ct33/ct33_cyclic49_kernel.py
python3 -O -B experiments/chained-transfer-reference/ct33/ct33_cyclic49_kernel.py
go run experiments/chained-transfer-reference/ct33/ct33_cyclic49_independent.go
```

Both implementations verify *each* degree-7 Vélu rational function by a coefficientwise identity on the elliptic equations; verify that the composition has a **reduced** rational x-map of degree 49, denominator \(K^2\), and the correct final elliptic equation; check \(H\) is squarefree and disjoint from the original kernel; and compute Frobenius \(\gcd(H,x^{101^d}-x)\) fixed-coordinate counts. Negative controls reject intentionally incorrect target coefficients and replacing the second kernel by the dual/backtracking kernel. Python's checks run identically with `-O` (no `assert`-dependent verification). These are exhaustive finite-polynomial *identities*, not exhaustive arbitrary-degree 49 point arithmetic.

**Failure retained:** An initial development tester incorrectly required the *backtracking* degree-21 support to split over \(\mathbf F_{101^{21}}\). The backtracking fiber instead has Frobenius orbit degrees 3 and 6; the test was corrected to require field-21 splitting **only** for the selected nondual \(H\). No source evidence was rewritten.

## Interpretation and precise remaining work

This makes the entire **coordinate-wise** cyclic-49 geometric kernel explicitly representable by 25 base-field coefficients, avoiding a degree-21 extension for its *polynomial description*. It does not represent its signed geometric points in the base field: CT32's degrees 42 and 14 for full signed kernel points are unchanged. It also does not eliminate extension-field work whenever a later correspondence evaluator needs individual support points and signs, or show a faster end-to-end Jacobian map. An extension-free rational description is **not** a new low-cost discrete-log algorithm.

Next independently compare the degree-24 support polynomials with the native composite elliptic numerator/denominator and the actual genus-2 \(\Phi_2\)/\(\Psi_2\) correspondence kernel. Only then explore resultant/traces for x-only Jacobian correspondence evaluation and its full cost, preserving the matched optimized-rho/index-calculus controls and EKS/S3 budget gates. Independent signed PCC, a full genus-2 Cantor homomorphism audit, and actual cold solve timings remain open.