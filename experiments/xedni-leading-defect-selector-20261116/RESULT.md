# A leading-defect selector deepens one fresh rational residual

The first-order formal-parameter residues of `[q]P1` and `[q]P2` predict whether a short public relation residual reaches depth at least two. On a frozen fresh-target panel, this cancellation criterion agreed with the exact rational group result for **all 11,250 candidate lifts**. A coefficient-independent selector that favors models supporting the most vectors in the predeclared family changed 16 of 18 selected models, deepened one selected residual, and made none shallower. The 18 depth-two candidates remained nonidentity residuals. The [independent replay](audit.py) rebuilt every query, lift, residue, and exact group result.

## Construction and result

The [protocol](protocol.json) pins eight field/subgroup records through the source protocol hash, four fresh targets per field under `xedni-leading-defect-v1|p|j`, 16 public queries per target, and 13 fixed short vectors per query. Its 512 queries yielded 18 public relation hits among 6,656 vector tests. Each hit has 625 centered coordinate-shift rational models. No equal-x exceptional hit occurred.

For a lift point `Pi`, compute `[q]Pi` over `Qp(p, prec=8)` and its formal parameter `ti=-xi/yi`. The residue `ci=(ti/p) mod p` is the first graded coordinate of the kernel point. For every candidate model, score the number of the fixed 13 vectors `(a,b)` satisfying `a*c1+b*c2=0 mod p`. The selector maximizes that count, then minimizes full rational-model bit size, then uses lexicographic shift order. It is fixed before the rational relation is evaluated. The paired baseline minimizes model size. A separate vector-aware oracle diagnostic uses the actual public-hit vector and is excluded from the selector.

| Recorded item | Result |
| --- | ---: |
| Fresh targets / queries / vector tests | 32 / 512 / 6,656 |
| Public hits / candidate attempts | 18 / 11,250 |
| Candidate, q-multiple, rational controls | 11,250 / 22,500 / 11,250 passed |
| Candidate or prediction failures | 0 |
| Family score zero / one | 10,951 / 299 candidates |
| Exact residual depth one / two | 11,232 / 18 candidates |
| Leading cancellation predictions / matches | 18 / 11,250 |
| Baseline selected depth one / two | 17 / 1 hits |
| Family selected depth one / two | 16 / 2 hits |
| Family choice changed / improved / worsened | 16 / 1 / 0 hits |
| Vector-aware oracle finds depth two | 11 / 18 hits |
| Exact rational relations | 0 |

The one improved hit is event 222, vector index 1. The family score is at most one throughout this panel, so it identifies models that cancel one of the 13 vectors but cannot distinguish which public vector will hit. The oracle diagnostic locates a depth-two candidate on 11 hits, showing the information available after the hit vector is known. These selection counts are finite-panel observations, not an estimated success probability.

The checked-Sage producer took 15.49 seconds on an ordinary host. Its exclusive stage timers record 0.134 seconds for candidate construction, 10.113 seconds for q-multiple residue computation, and 4.655 seconds for rational relation evaluation. Public setup, query generation, serialization, and control flow occupy the remaining interval. The [runtime receipt](sage-runtime.json) was saved before execution. These are stage diagnostics; the protocol did not run a paired same-target online IC and rho comparison.

## Proof map and interpretation

The first graded piece of the elliptic formal group is additive: if `[q]P1` and `[q]P2` lie in the reduction kernel, the leading residue of their integer linear combination is `a*c1+b*c2`. For a public relation, `[q](aP1+bP2)=a[q]P1+b[q]P2`, so the residual has formal depth at least two exactly when that leading sum vanishes, provided the residual is in the kernel. The producer and an independent modular-Jacobian calculation check this implication on every recorded candidate, including both sides of the equivalence.

The [Lean module](formal/LeadingDefect.lean) proves `leading_linear_combination` and `leading_cancellation_iff_kernel` for an additive leading map from an abelian group to `ZMod p`. The exact hypotheses are an `AddCommGroup K` and `lead : K →+ ZMod p`; the declarations preserve arbitrary integer coefficients. `#print axioms` reports `propext` and `Quot.sound` only. The formalization is **partial**: the missing bridge is a Lean construction of the elliptic reduction-kernel filtration and its first graded coefficient as this additive homomorphism, together with the identification of the rational residual depth with membership in the next filtration step. The theorem does not assume the cancellation conclusion.

The next experiment should let the actual public-hit vector guide selection among candidates, charge the search over all candidates, and test fresh targets with a precommitted policy. It should also formalize the elliptic first-graded bridge. The [result manifest](run-result.json) indexes every compressed candidate part, and `python3 verify.py` checks the frozen files and replays the independent audit. New local Sage runs use `/Volumes/SSD990/cryptanalysis/sage --runtime-info` before `/Volumes/SSD990/cryptanalysis/sage -python /absolute/path/to/run.py`.
