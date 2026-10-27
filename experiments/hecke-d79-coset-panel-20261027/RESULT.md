# The order-five coset criterion predicts the zero-triple p397 class

The frozen (D_K=-79, f=4) four-prime panel matched its prospective prediction: the **p397** class lies entirely in two opposite nonzero order-five cosets and has **zero signed direct three-point relations**. Its four signed pair rows raise the 20-row base rank only to **24 over F5**. The other three classes occupy residues that permit three-term projection cancellation; they produced **44, 35, and 31** verified triples, each raising its 20-row base system to **rank 39** over the largest prime factor of its curve order.

| Prime | Curve order; rank modulus | Class projection residues and counts | Antipodal-only prediction | Verified pairs / triples | Base → direct rank mod q | Base → direct rank Q |
| ---: | --- | --- | --- | ---: | ---: | ---: |
| 397 | 400; 5 | 1:20, 4:20 | zero triples | 4 / **0** | 20 → 24 | 20 → 24 |
| 677 | 720; 5 | 1:20, 2:20 | no zero-count prediction | 0 / 44 | 20 → 39 | 20 → 40 |
| 757 | 780; 13 | 1:20, 2:20 | no zero-count prediction | 0 / 35 | 20 → 39 | 20 → 40 |
| 2917 | 2830; 283 | 0:20, 1:20 | no zero-count prediction | 0 / 31 | 20 → 39 | 20 → 40 |

All four classes matched the frozen **40-point** prediction, with conductor (f=1,2,4) strata **10, 10, 20** in each case. The [class receipt](class-result.json) retains every point, base row and order-five residue. The [relation receipt](analysis.json) retains all ordered signed candidates, the complete greedy rank paths and separate Q/mod-q ranks. The source code and [protocol](PROTOCOL.md) were frozen before any class output; [post_inputs.json](post_inputs.json) pinned that output before relation enumeration.

For each curve group of order (N), multiplication by (N/5) supplies the order-five projection used in the criterion. If every class point projects to (T) or (-T), every signed three-term sum projects to (\pm T) or (\pm3T), which is nonzero. The [pinned Lean theorem](formal/CosetPanel.lean) proves this implication for any addition-preserving map into `Fin 5`. The p397 curve audit establishes its exact 20/20 projection census, so its zero-triple result follows structurally. Residues 1 and 2 allow a modular pattern (1+2+2=0); residues 0 and 1 allow (0+1-1=0). These patterns only remove the quotient obstruction; exact curve addition verifies the observed relations in the other three cases.

The earlier p1277 class also had the antipodal 20/20 pattern and zero direct triples, while the p317 class occupied residues 1 and 2 with counts 20/19 and had 122 triples. Those are contextual receipts on different fields. The four cases here were frozen together before their class output. The independent [checked-Sage audit](audit_sage.py) scanned every rational curve point at each prime, reconstructed all class strata and projections, verified every base row, re-enumerated every signed support-one/two/three candidate, and recomputed each Q and mod-q rank. [audit.json](audit.json) records `PASS` for all four cases.

The iid nonidentity group-sum support-three means, retained as exact fractions in [analysis.json](analysis.json), are approximately **98.8, 54.9, 50.7, and 14.0**. They describe a count control with independently sampled points; the p397 class's coset condition explains why that model does not describe its triple yield. No significance tail was frozen for this panel.

The checked [Sage runtime](sage-runtime-info.txt) was saved before the producer. The shared degree-2/5 source build took **2.016 s**; case construction, enumeration and rank-analysis nanosecond fields are retained per case. This local host lacks exclusive CPU and frequency controls, so these costs are exploratory stage diagnostics. The panel keeps `candidate_id: null` and `target_online_ms: null`.

The central obstruction is Lean checked. The connection from the 160 audited curve points to the formal projection hypotheses and the four empirical matrix-rank results remains a partial formalization, recorded in the [proof map](formal/PROOF_MAP.json). The next experiment should run the degree-13 Hecke source at a prime where the direct coset criterion blocks triples and a substantial q-primary factor remains, using a frozen resource envelope and complete relation-rank accounting.

Reproduce from the repository root:

```sh
./sage --runtime-info > experiments/hecke-d79-coset-panel-20261027/sage-runtime-info.txt
gtimeout 900 ./sage -python experiments/hecke-d79-coset-panel-20261027/class_producer.py
gtimeout 120 python3 experiments/hecke-d79-coset-panel-20261027/analyze.py
gtimeout 900 ./sage -python experiments/hecke-d79-coset-panel-20261027/audit_sage.py
cd experiments/hecke-d79-coset-panel-20261027/formal
lake build CosetPanel
```
