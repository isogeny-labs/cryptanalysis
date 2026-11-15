# CT34 — direct degree-49 Vélu transfer from the cyclic-49 kernel polynomial

**[pcc:unverified]** This is a bounded *elliptic-factor* certificate over F101. It neither certifies a genus-2 Jacobian isogeny nor demonstrates a DLP advantage. The source is independently written and self-contained; the producer cannot sign its own PCC verdict.

## Sources and prior work

- Original [crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877), horizontal hops [cryptanalysis #1492](https://github.com/isogeny-labs/cryptanalysis/pull/1492), and CT32/33 x-kernels [#1495](https://github.com/isogeny-labs/cryptanalysis/pull/1495), especially `ct33/CT33_XONLY_KERNEL.md`. Concurrent direct C2 norms are already in [#1496](https://github.com/isogeny-labs/cryptanalysis/pull/1496), so they are not duplicated.
- Classical Vélu isogeny formulas; Bostan–Morain–Salvy–Schost, *Fast algorithms for computing isogenies between elliptic curves*, Mathematics of Computation 77 (2008), [arXiv:cs/0609020](https://arxiv.org/abs/cs/0609020). This is an exact engineering cross-check of known mathematics, **not a novel isogeny formula**.
- Read `AGENTS.md`, CT33 session log and root `.resume/RESUME.md`. Shared research-KB tools and the locked autoresearcher atlas were unavailable; no claim of absent prior art or canonical atlas update.

## One-hop direct construction versus the existing 7+7 chain

Let E: `y²=f(x)=x³+a*x+b` and let `K` be the monic, squarefree polynomial of the distinct x-coordinates of the ± pairs in a separable odd-order kernel. Set `r=deg K`, `d=2r+1`, `s1=-[x^(r-1)]K`. The normalized Vélu map is `X=N/K²` where

```
N = (d*x-2*s1)*K^2 - 2*f'(x)*K'(x)*K(x)
                         + 4*f(x)*(K'(x)^2-K(x)*K''(x)).
```

For CT33's two fixed cyclic-49 kernels, `r=24`, `d=49`. The new oracle constructs `N` **directly from K**, without extracting geometric torsion points or using the two-stage rational map. A separate code path reconstructs the composition of the two degree-7 Vélu rational maps and checks exact numerator/denominator equality coefficient by coefficient. The target coefficients are derived separately using the first three Newton root sums of K. A full normalized point map uses `Y=y*(dX/dx)`.

| Control | E109 | E113 |
|---|---:|---:|
| Direct target coefficients | (59,27) | (23,7) |
| Newton root sums (S1,S2,S3) | (84,17,58) | (5,83,10) |
| Direct degree-49 vs two-seven polynomials | Equal | Equal |
| Mapped rational points / pointwise composition | 109/109 | 113/113 |
| All ordered rational-group additivity pairs | 11,881 | 12,769 |
| Cold BSGS known-answer solves on **each** domain | 109 | 113 |
| Direct and transported BSGS additions | 1685 / 1685 | 1768 / 1768 |
| Deliberate low- and high-coefficient errors rejected | 2/2 | 2/2 |

All rational points on each source and target curve are enumerated independently. Every point's direct image equals its two-hop image, is on the target, and is checked against the complete cyclic addition table. A fresh BSGS solves each public `kG` both on source and transported target; the solver does not use the expected `k`. The BSGS figures count table/giant additions only, excluding scalar checks, kernel construction, map cost, memory and field operations. They **cannot** support a complete-cost or speed claim.

**Development correction retained:** a negative control that changed only K's constant coefficient was expected to perturb the target coefficients, but it did not: the target uses only the top three non-leading coefficients through the first three root sums. The final test mutates a high coefficient to check the target separately while keeping the low-coefficient mutation to test the rational map.

## Reproduction

```sh
python3 -B experiments/chained-transfer-reference/ct34/ct34_direct49_audit.py
python3 -O -B experiments/chained-transfer-reference/ct34/ct34_direct49_audit.py
```

Both modes passed bounded local development checks; exact-head CI must be inspected separately. Output is deterministic JSON. See the companion SVG for the two paths and the local two-page illustrated report.

## Interpretation and next discriminating test

This proves a *concrete, fixed-polynomial* equality within producer-run checks: one degree-49 elliptic map equals the 7+7 composition. It does not show that evaluating the single degree-49 expression is faster than two degree-7 maps. Dense Horner evaluation uses much higher polynomial degree, although it can use fewer inversions; performance comparison would require a matched, approved protocol.

Next compare this elliptic K and exact map with the **native composite map and genus-2 Phi2/Psi2 kernel/correspondence**, including duals and exceptional divisors. Independently verify all 12,317 genus-2 classes using a separate Cantor engine, then run admitted complete-cost comparisons against matched optimized rho/index calculus. No cloud spend and no merge-gate bypass. Scientific standing **[pcc:unverified]**.
