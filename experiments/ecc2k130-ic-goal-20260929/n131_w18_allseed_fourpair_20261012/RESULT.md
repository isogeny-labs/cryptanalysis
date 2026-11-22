# All-seed four-pair geometry and exact target-coupled circuit

An all-seed W18 source makes **four signed diagonal-pair slots** sufficient for a dense labeled N131 relation source: its exact 34,482,792,912 admissible signed pair states per rotation give a **2,077.496 upper mean** of labeled four-pair tuples per uniform subgroup target before cross-slot folded-column and reciprocal-chart exclusions. Three slots give a mean upper ceiling of `6.025×10⁻⁸`. A compact Boolean circuit keeps the public target coupled to all four free pair outputs, enforces the rational source masks and eight distinct folded columns, and fits the frozen 4-GiB construction envelope. Its independently generated N131 control satisfies every clause and XOR row.

The matching N41 diagonal-source control found a new **eight-column public-point relation** after 96,094 right probes and independently checked its group equation and folded row. A source-law correction mattered: the first all-seed N41 join used raw points `P`, whereas the N131 pair inverse uses diagonal points `D=P+τ(P)`. The raw-point relation remains in [`n41_control`](n41_control); the corrected [`n41_diagonal`](n41_diagonal) is the transfer control. For each source mask `w`, checked Sage verified `x(D)=1/w` before exporting the signed pair states.

The curve is `EC1N131Ckb1heb5f1998f20b` over `GF(2)[t]/(t^131+t^13+t²+t+1)`, with subgroup order `680564733841876926932320129493409985129` and cofactor four. The public workload `cc09e7eb202a` is `(1052727368764798954359115163823647684025,2071227447786120917960296877345506689833)`. W18 supplies 131,307 rational masks and 131,068 folded columns. The four pair slots use Frobenius rotations `(0,32,64,96)`. This is a point-decomposition proposal with `candidate_id: null`.

## Circuit and exact source shield

For source-mask field elements `a,b`, set `s=a+b`, `p=ab`, and let `c=1/x(D_a±D_b)` be the unrotated pair reciprocal. The pair relation is the cleared reciprocal S3 equation

`(1+p²)c²+pc+s²=0`, equivalently `(pc)²+pc+s²+c²=0`.

The circuit chooses two supported 18-bit masks per pair, computes their field product, and enforces this relation. It applies the slot's Frobenius rotation to each pair reciprocal. Three more S3 links join the four pair outputs through two free internal reciprocals to the selected raw public-target preimage. Nonzero reciprocal clauses define the finite nonexceptional chart. Every pair of source masks must differ. The [v2 source](fourpair_v2.py) additionally enumerates all **243 unequal-mask pairs sharing a folded column** and forbids both orientations across every pair of leaf positions, adding 13,608 clauses. Thus any satisfying mask assignment has eight distinct folded columns. Sign choices remain existential in the reciprocal equations and are subject to full group replay on any ordinary solver model.

| Exact stage or control | Result |
| --- | ---: |
| N41 diagonal states per rotation / exported total | 30,952 / 123,808 |
| N41 public join, three million kept left states | verified relation in 8.913892 s parent wall, 211,451,904 B sampled RSS |
| N41 target-dependent right probes / attempts at hit | 96,094 / 99,810 |
| Independent N41 Sage audit | eight distinct columns; rank **4** with prior three rows |
| Exact-shield N41 formula | 14,803 variables; 35,804 clauses; 2,892 XOR rows; 712,086 B |
| Exact-shield N131 public formula | 790,156 variables; 845,990 clauses; 512,085 XOR rows; 32,628,346 B |
| N131 public formula projection | 24.842840 s parent wall; 391,348,224 B sampled peak |
| N131 constructed-target complete assignment | all 845,990 clauses and 512,085 XOR rows pass; 17.647118 s parent wall; 435,781,632 B sampled peak |

The [N41 join protocol](n41_diagonal/protocol.json) fixed the one-worker, 180-second, 4-GiB public query before execution; its [receipt](n41_diagonal/receipt.json) and [independent checked-Sage audit](n41_diagonal/audit_result.json) retain the selected source masks, raw preimage, cofactor projection, and relation coefficients. The [v2 protocol](v2_protocol.json) froze the Boolean source, source support, constructed fixtures, public workload, and one-worker 600-second/4-GiB construction cap. The [N131 public projection receipt](v2_n131_public_receipt.json) includes formula construction and serialization; the [constructed-control receipt](v2_n131_control_receipt.json) includes the full Boolean row check. These CPU intervals are exploratory on an unisolated host; the exact row counts, hashes, and pass/fail checks are the reproducible evidence.

## Search boundary and next experiment

The unpinned exact-shield N41 solver [reached its 190-second parent wall cap](n41_solver_receipt_v3.json) with active CryptoMiniSat restarts, exit `-9`, and no terminal SAT/UNSAT line; sampled peak RSS was 334,479,360 B. An earlier formula without the folded-column shield returned [`s INDETERMINATE`](n41_solver_receipt_v2.json) after its 180-second solver cap. The first launch's argument-parser failure is preserved separately in [its receipt](n41_solver_receipt.json). Each status belongs to its exact frozen formula and cap. The complete N41 witness assignment proves the v2 formula is satisfiable, while the bounded unpinned result measures the remaining search cost.

The N41 direct join is a source-geometry control. A fixed three-million-by-three-million half-list has negligible N131 target coverage under the [fixed-list counting bound](../n131_w18_tenpair_mitm_bound_20261012/RESULT.md); its quick N41 relation does not supply an N131 search procedure. The next experiment should use the fast joint-linear pair-output inverse to reject **two unresolved pair-output families jointly from the public target**, before expanding source masks. It must first beat the present N41 unpinned search boundary with independently replayed mask choices, then account for all target-dependent work under the one-worker N131 600-second/4-GiB envelope. The N131 ordinary solver query remains gated on that result.

The [proof map](PROOF_MAP.md) connects the tuple-count theorem, reciprocal S3 derivation, source-column shield, and exact verification boundaries.
