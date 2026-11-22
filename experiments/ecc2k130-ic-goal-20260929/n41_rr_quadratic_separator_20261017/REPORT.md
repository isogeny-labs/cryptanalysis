# Exact quadratic RR certificates and alternate-root transfer

## Contribution

An exact target-conditioned quadratic Boolean certificate excludes zero from 13 of 35 complete N41 first-slot root/code charts with five suffix points fixed. Symplectic factorization evaluates the certificate with 20 AND gates on linear forms over the 41 determinant bits. On an archived N131 four-chart panel, the same synthesis method covers all four root-0 charts with 11 AND gates; the linear method covers three. An alternate-root holdout accepted 133/256 determinant words and no complete chart, identifying the next generalization problem.

The certificate is applied **after** the seven-point Riemann–Roch determinant is available. Synthesis enumerates all 64 signs in each fitted chart. The AND counts describe certificate evaluation alone and do not include determinant generation, synthesis, factor-base setup, relation collection, or a target descent. These stage results therefore have `candidate_id: null` and no online IC/rho timing ratio.

## Mathematical construction

Fix six curve points \(P_0,\ldots,P_5\) and a public target \(Q\), with pairwise distinct seven \(x\)-coordinates. For a sign vector \(s\in\mathbb F_2^6\), let \(D_s\in\mathbb F_{2^n}\) be the determinant of the \(L(7O)\) evaluation matrix at the signed points and \(-Q\). The archived RR construction and the independent Gaussian and curve-sum audits check the relation test for these exact panels: \(D_s=0\) exactly when the signed points sum to \(Q\).

For a set \(V\) of nonzero determinant words, seek a Boolean polynomial with zero constant term

\[
q(x)=\sum_i a_i x_i+\sum_{i<j}a_{ij}x_i x_j
\qquad\text{such that}\qquad q(v)=1\quad(v\in V).
\]

Each \(v\) supplies one linear equation in the \(n+\binom n2\) unknown coefficients. We add whole charts in deterministic code order, rejecting a chart when its 64 equations make the system inconsistent. Since \(q(0)=0\), any complete chart on which every determinant satisfies \(q(D_s)=1\) contains no zero determinant. A chart with a zero cannot pass this test.

The polar form \(B(u,v)=q(u+v)+q(u)+q(v)\) is alternating. If its rank is \(2r\), a symplectic basis gives coordinates \(y_i\) in which

\[
q(x)=\ell(x)+\sum_{k=0}^{r-1}y_{2k}(x)y_{2k+1}(x),
\]

where \(\ell\) and every \(y_i\) are binary-linear forms. The construction uses \(r\) AND gates and XORs. The independent symbolic audits expand every product back into its linear and squarefree quadratic coefficients; equality of those coefficients proves equality of the functions on every input word, rather than on sampled words alone.

## Frozen experiments

The JSON protocol and source hashes in this directory bind every run. The N41 target and suffix are the earlier verified six-pair panel. The N131 target, field polynomial, suffix and four root-0 charts come from `../n41_n131_rr_code_family_span_20261017/panel_n131_v2.json`, whose coefficient hashes were checked by its independent Sage replay. `root-1` means the alternate first-slot root at each of the four frozen source codes. All values are field words in the panel's declared polynomial basis.

| Panel and input law | Complete charts certified, linear | Complete charts certified, quadratic | Polar rank / AND gates | Producer wall and child peak RSS | Independent checks |
| --- | ---: | ---: | ---: | ---: | --- |
| N41, 35 root-0 first-slot codes, fixed five-point suffix, 64 signs/chart | 1/35 | 13/35 (832 signs) | 40 / 20 | 3.374 s / 24,494,080 B | 2,304 Gaussian determinants and group sums; 861 symbolic coefficients |
| N131, four archived root-0 codes, fixed five-point suffix, 64 signs/chart | 3/4 | 4/4 (256 signs) | 22 / 11 | 24.089 s / 23,412,736 B | Archived independent coefficient replay; 8,646 symbolic coefficients; 256 sign values |
| N131 alternate root-1 at the same four codes, certificate frozen from root-0 | 0/4 whole charts | 133/256 sign words accepted; 0/4 whole charts | same fixed 11-gate circuit | 0.096 s screen; 0.882 s independent audit | 256 Gaussian determinants and curve sums; zero group hits |

The N41 screen used one worker with a parent 180 s cap and a 4 GiB RSS boundary; its receipt is `run_result.json`. The N131 transfer used the same one-worker cap and boundary in `transfer_run_result.json`. These are ordinary-host stage measurements, with no physical-host isolation or paired rho. The N41 original polynomial has 385 quadratic coordinate monomials and 4 linear terms, reduced to 20 products of linear forms and a 16-bit linear mask. The N131 polynomial has 135 quadratic monomials and no direct linear terms, reduced to 11 products and a 7-bit linear mask. The product input forms contain 430 and 144 literals, respectively; XOR work is therefore present even though the AND count is small.

The alternate-root holdout had certificate-one counts 33, 34, 30, and 36 among its four 64-sign charts. None of these charts is wholly excluded by the frozen root-0 certificate. The independent holdout audit recomputed each determinant by seven-by-seven Gaussian elimination and each six-point curve sum. This result narrows the next hypothesis: a useful selector must preserve its no-zero property across alternate roots or exploit the root choice explicitly, and must reject branches before paying for their full determinant families.

## Reproduction and proof status

Run the Python scripts from this directory with `python3`; they use the pinned source hashes in their JSON protocols. The producer order was `freeze.py`, `run.py`, `audit.py`, `freeze_factor.py`, `factor.py`, `audit_factor.py`, then `freeze_transfer.py`, `run_transfer.py`, `audit_transfer_n131.py`, `freeze_holdout.py`, `holdout_n131.py`, and `audit_holdout_n131.py`. Running a producer again changes timing fields and artifact hashes; copy the directory before a fresh replay. `audit_attempt1.stderr` preserves an audit-code tuple/list comparison error, corrected before the passing independent audit.

`lean-toolchain` pins Lean 4.34.1 and the bundled `Std` dependency. `lean QuadraticCertificate.lean` built with exit code 0 on arm64 macOS; `lean_check.stdout` contains the `#print axioms` output. The checked theorems establish the no-zero implication for both the direct polynomial and the factored XOR/AND circuit. `PROOF_MAP.md` identifies the remaining formal bridges for the symplectic construction and the RR determinant relation test. `lean4checker` was unavailable on this host.

## Next test

Pull the certificate condition back through partial RR determinant data so it can be evaluated on unfinished source branches, then freeze a root-balanced family before fitting. Measure whole-branch rejection on unseen first-slot codes and alternate roots, including determinant or partial-data construction cost. Promote only a selector that passes an independent no-zero replay and reduces charged target-dependent work on a previously unseen same-point instance.
