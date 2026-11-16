# Optimized public vectors yield zero rational relations under the frozen CRT lifts

The target-independent 13-vector family from the fresh-field public coverage experiment produces **4,844 accepted reduced relations per lift arm** on the archived eight-field panel, compared with **4,504** for the original effective 13-vector baseline. Under the same frozen centered and shifted CRT lift laws, **none** of the optimized vectors yields a rational relation. The baseline packet has **4 centered** and **11 shifted** rational relation rows, all from `(1,2)` or `(2,1)`; neither direction belongs to the optimized family. This isolates the missing lift stage: an improved public relation family did not transfer to these rational constructions.

| Field `p` | Selected accepted public relations per arm | Selected centered rational | Selected shifted rational | Baseline centered rational | Baseline shifted rational |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 47 | 436 | 0 | 0 | 4 | 6 |
| 101 | 558 | 0 | 0 | 0 | 2 |
| 191 | 556 | 0 | 0 | 0 | 0 |
| 211 | 818 | 0 | 0 | 0 | 1 |
| 251 | 586 | 0 | 0 | 0 | 2 |
| 281 | 728 | 0 | 0 | 0 | 0 |
| 347 | 468 | 0 | 0 | 0 | 0 |
| 349 | 694 | 0 | 0 | 0 | 0 |

Each arm retains all **30,008** ordered public queries and **371,592** selected-family public vector tests on admitted pairs. The selected rational-test count is **4,844 per arm**; multiple selected vectors can hit the same accepted curve, so the centered arm reconstructs 4,812 distinct curves. The centered archive charges **5,282,834** auxiliary construction probes and the shifted archive **5,328,943**, including failed and nonrelation rows. Reconstructing the saved ordinal curve for replay does not replace that original probe work. No isolated wall-time or same-target rho comparison was performed.

## Frozen method and independent audit

`protocol.json` pins the optimized family, both parent lift datasets and the reconstruction source before replay. The runner tests each selected vector against the public points `Q−t₁G` and `Q−t₂G`, verifies all archived uncompressed row hashes and query order, and reconstructs a rational curve only for an accepted row with at least one reduced relation. It checks point incidence and reduction to the fixed curve over `F_p`, `F_7`, and `F_11`, then records every rational group test and its full curve/point witness. The per-field JSONL records retain all 9,688 selected rational tests.

The independent checked-Sage audit rebuilds every such curve directly from the archived CRT ordinals, checks all 9,688 rational group equations, validates the complete archived row and probe counts, and confirms the zero-yield result. It also replays a parent `(1,2)` rational positive control in each lift arm on `p=47`, query 239. The audit passes with empty stderr.

## Proof map and next falsifier

The structural theorem `XedniFirstHitDominance.relation_reduces` in the earlier checked PR #1611 says a rational relation reducing through a compatible homomorphism implies a public relation on the same query and coefficients. This replay checks the converse existence question for two exact lift laws; zero rational hits is an exhaustive computed result for the archived panel, independently checked by Sage. A Lean formalization of every rational curve and all 9,688 group computations is not included; `PROOF_MAP.md` records that missing bridge and the verification boundary.

The next experiment should use a **vector-dependent rational lift rule** fixed before fresh public queries, and charge all rejected curve constructions and rational tests. Choosing a curve after observing a reduced relation is not a relation-finding method unless it supplies a lift without first solving the public group equation.

Reproduce from the repository root with `python3 experiments/xedni-optimized-family-lift-replay-20261115/run.py`, `./sage --runtime-info`, `./sage -python experiments/xedni-optimized-family-lift-replay-20261115/audit_sage.py`, and `python3 experiments/xedni-optimized-family-lift-replay-20261115/verify.py`.
