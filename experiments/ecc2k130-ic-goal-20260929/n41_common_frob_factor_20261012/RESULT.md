# Common Frobenius factor gives an N41 public relation and an N131 five-pair target

**An unpinned five-pair group join found a new relation on the frozen N41 public point in 9.096 seconds of one-worker runner wall.** Independent checked Sage rebuilt the five signed W8 pair states and their ten diagonal source atoms, verified the transformed and original public group equations, checked ten distinct folded columns, and raised the known relation rank from **six to seven**. The exact method factors a common Frobenius shift out of ten pair terms, leaving a five-pair target equation. Checked Sage then applied the same target transformation to the frozen N131 public point and all four raw preimages for a source-bound five-pair circuit gate.

## Factor and exact N41 source

For the curve `y²+xy=x³+1` over `GF(2)[t]/(t^41+t³+1)`, let `τ` be coordinate-squaring Frobenius and let `P_i` be a signed W8 diagonal pair state. Additivity gives

`Σ_{i=0}^4 (P_i + τ⁷P_i) = (1+τ⁷) Σ_{i=0}^4 P_i`.

On the prime-order N41 subgroup (`r=549756390943`), checked Sage identifies Frobenius eigenvalue `λ=256851699273`, so `1+λ⁷=148692722093` is invertible modulo `r`. The frozen public point `Q=(920359962848,755404565011)` transforms to `Q′=(1099765887764,1148205618145)`. [The target receipt](target.json) verifies `Q′+τ⁷Q′=Q`. The join uses the fourfold projections `4P_i`, searches `Σ 4P_i=Q′`, and requires ten distinct folded columns. Each accepted state therefore contributes its two source atoms twice to the original public relation, with the second copy at Frobenius shift seven.

The [source](../n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv) has 30,952 signed all-seed W8 pair states at each exported rotation; this experiment uses the rotation-zero list for all five free states. The native worker projects every state by four, checks the curve equation and global sign partners, then makes a two-versus-three group join. The [protocol](protocol.json) froze the input and binary hashes, deterministic seed, 2,000,000 kept left states, 5,000,000 maximum right probes, one worker, 180 seconds, and 4 GiB before the query. The input transformation used the checked repository Sage launcher with its saved [runtime receipt](sage_runtime_info.json).

| N41 join phase | Frozen result |
| --- | ---: |
| Source states checked | 30,952 |
| Left kept / attempted | 2,000,000 / 2,078,369 |
| Right kept / attempted at hit | 16,027 / 18,027 |
| X-coordinate matches before hit | 1 |
| Native time through left table / hit | 7.63143 / 7.84741 s |
| Whole runner wall | 9.095684375 s |
| Sampled parent plus worker RSS peak | 146,243,584 B |
| Selected state IDs | `15842,1006,22805,27411,11500` |
| Folded columns / rank | 10 / **6 → 7** |

The [independent checked-Sage audit](audit_result.json) reconstructs each pair from its two signed diagonal atoms, checks the original exported point and its fourfold projection, proves their projected sum equals `Q′`, and checks `(1+τ⁷)Q′=Q`. It builds the quotient relation row against raw projected factor-base representatives and evaluates that row to `Q`. Columns `23,37,57,85` are absent from the six prior rows and have nonzero coefficients in the new row; the audit also performs modular elimination and finds rank seven. The [read-only verifier](verify.py) checks the source, binary, protocol, raw logs, audit inputs, column certificate, and count receipts. These local wall measurements are exploratory without host isolation.

## N131 target and source gate

The same construction uses shift 16 on `EC1N131Ckb1heb5f1998f20b`, field `GF(2)[t]/(t^131+t^13+t²+t+1)`, subgroup order `680564733841876926932320129493409985129`, and the frozen public workload `cc09e7eb202a`. The [N131 Sage receipt](n131_projection_result.json) verifies `Q′+τ¹⁶Q′=Q`, identifies the nonzero subgroup factor `1+λ¹⁶=99717920955595431923619593794150750754`, and transports all four raw target preimages so that multiplication by four yields `Q′`. The [projection protocol](n131_projection_protocol.json) froze the source, target, and checked Sage runtime before execution.

The W18 support has `M=131307` rational masks and `K=131068` folded columns. Its signed unordered distinct-column pair list has exactly `S=34482792912` states. A column containing `m_c` masks occurs in `4m_c(M−m_c)` pair states, with maximum `D=2100848`. After choosing `j` pairs, at most `2jD` states touch one of their occupied columns. Thus the exact ordered five-pair source with ten distinct folded columns has at least

`∏_{j=0}^4 (S−2jD) = 48694833971851197475330691697357479346535949512212480`

labeled assignments. The [source projection](source_projection_result.json) and [verifier](verify.py) recompute every support multiplicity and factor. Dividing this count by the subgroup order gives a **uniform-mapping heuristic mean of at least 7.155×10¹³ assignments per target**; it is a density projection, not a measured public-point yield. A fixed 2-million-by-5-million N131 join has only `10¹³/r ≈ 1.47×10⁻²⁶` uniform-target hit expectation, so the successful N41 table sizes are not a viable N131 search by themselves.

## Formalization and next gate

[CommonFactor.lean](CommonFactor.lean) proves the shared additive-endomorphism identity for five summands, and [FivePairCount.lean](FivePairCount.lean) proves the multiplicative lower-bound step from five extension bounds. Both build under pinned Lean 4.34.1 with no theorem axioms; [PROOF_MAP.md](PROOF_MAP.md) records the executable field/curve and source-incidence bridges still outside Lean. The N41 relation and N131 target receipts are exact, while the N131 source-count-to-target-yield conversion is explicitly heuristic.

The next experiment is a **five-free-pair N131 source-bound circuit** on the four transformed raw preimages, with ten distinct-column masks and four upper point-sum links. Freeze and replay a complete constructed assignment before an unpinned 600-second/4-GiB public query. A public model must pass independent signed group and quotient-row replay, followed by useful-rank and factor-log accounting under the standing single-target objective. This component remains `candidate_id: null` until the complete IC pipeline is specified.
