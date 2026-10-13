# Target-conditioned residual completion gives another N41 public relation

**An exact fifth-pair residual lookup found a new relation on the frozen N41 public point in 29.848 seconds of one-worker parent wall.** Independent checked Sage replayed all ten signed source atoms, checked the transformed and original public group equations, verified ten distinct folded columns, and raised the known quotient-relation rank from **7 to 8**. The target-derived residual gate tested 6,427,002 disjoint-column four-pair partial sums before one full-point match. This experiment isolates a usable target-conditioned completion step and measures its source-density limit at N131.

## Method and frozen N41 result

The curve is `EC1N41Ckb1h7d5e80d3c4d0`, over `GF(2)[t]/(t^41+t^3+1)` with `y²+xy=x³+1`, subgroup order `549756390943`, and cofactor four. The public point is `(920359962848,755404565011)`. The already checked map `(1+Frobenius^7)⁻¹` gives transformed target `Q′=(1099765887764,1148205618145)`. The source is the same 30,952 signed W8 diagonal pair states used in the prior five-pair join, each projected to the prime-order subgroup by multiplication by four.

The worker first samples 100,000 valid two-pair sums from the complete slot-zero source and stores their point, state IDs, and folded columns. During the query it samples two of those entries, discards overlapping columns, computes `R=Q′−(P₁+P₂+P₃+P₄)`, and checks the exact group point `R` against a terminal pair-state hash. This rejects an entire fifth-pair family through one target-conditioned point lookup. A matching fifth pair is accepted only after all ten folded columns are distinct and the five-point equation is replayed. The [frozen protocol](protocol.json) binds the source, binary, runner, target, seed, one worker, 180-second parent cap, and 4-GiB combined RSS cap. Its informal `source_law` phrase describes four source states; the actual sampling law is the two-entry procedure above, as fixed by the hashed binary.

| Phase or result | Frozen value |
| --- | ---: |
| Two-pair table retained / attempts | 100,000 / 103,892 |
| Four-pair proposals / valid distinct-column probes | 7,506,857 / 6,427,002 |
| Full-point terminal matches / column rejects | 1 / 0 |
| Selected pair-state IDs | `(1636,9749,18489,10199,5473)` |
| Source and table construction inside worker | 0.615187 s |
| Target-conditioned probe interval inside worker | 29.2182 s |
| Whole parent process wall | 29.847786083 s |
| Sampled parent-plus-worker RSS peak | 36,667,392 B |
| Folded columns / known rank | 10 / **7 → 8** |

The [query receipt](result.json) preserves the exact stop status `HIT_PENDING_INDEPENDENT_REPLAY`, raw stdout hash, process exit, cap, and memory. The [independent checked-Sage audit](audit_result.json) resolves that pending model: it reconstructs each exported pair from W8 source points and sign bits, verifies each fourfold projection, checks the five-pair sum equals `Q′`, checks `Q′+Frobenius^7(Q′)=Q`, and evaluates the quotient relation row at the original public point. It tests the new row against the seven previously audited rows and finds rank eight. The [audit protocol](audit_protocol.json) froze the source, prior target, runtime, and hit receipt before replay. The [read-only verifier](verify.py) checks all frozen hashes, caps, selected IDs, source projection, and rank receipt.

These local CPU times are algorithmic diagnostics without an isolation receipt. The table construction is target-independent, but the prior checked computation of `Q′` was not timed in this run. Thus 29.2182 seconds measures the residual probe component, while a complete target-dependent online interval remains unknown. The IC `candidate_id` remains `null`; this is a decomposition and relation component, with no factor-log or target-scalar solve.

## N131 transfer gate

The [source projection](projection.json) independently recounts the frozen W18 support: 131,307 rational masks, 131,068 folded columns, and exactly **34,482,792,912 signed unordered distinct-column pair states**. The N131 prime subgroup has order `680564733841876926932320129493409985129`. If each target-derived residual is uniform in that subgroup, the probability it matches any terminal pair output is **at most** `34,482,792,912 / 680,564,733,841,876,926,932,320,129,493,409,985,129 ≈ 5.067×10⁻²⁹`. Output collisions only lower this bound. At the frozen 30-million valid-probe cap the expected number of hits is at most **1.520×10⁻²¹** under that model; one expected hit requires at least **1.974×10²⁸ ≈ 2⁹⁴** probes. This is a conditional uniform-residual calculation, not a lower bound on a deliberately nonuniform target-coupled generator.

The literal N131 terminal state table also exceeds the 4-GiB envelope before a hash index: even one byte per signed state is 34.5 GB. A source-implicit membership method such as the audited 131-by-53 W18 pair inverse avoids this table, but does not create high-probability residual proposals. The next method gate is therefore specific: derive a public-target constraint that concentrates four-pair residuals on the W18 pair-output image by roughly **6.6×10²⁰** relative to uniform for a 30-million-probe expected hit, while keeping pair families implicit and rejecting them before source enumeration. Freeze an unpinned N41 family-rejection control and an N131 work projection before another 600-second public query.

## Proof boundary

No new group identity is assumed. The group step is `P₁+⋯+P₅=Q′`, followed by the already formalized additive identity `Σ(P_i+τ⁷P_i)=(1+τ⁷)ΣP_i`; [CommonFactor.lean](../n41_common_frob_factor_20261012/CommonFactor.lean) and its [proof map](../n41_common_frob_factor_20261012/PROOF_MAP.md) retain the pinned Lean check and exact concrete-field bridge. This experiment's new claims are executable finite-source observations and the explicitly conditional uniform-model projection, backed by the frozen native worker, checked Sage replay, and exact integer source census. The N131 projection does not certify public-point relation yield or an online speedup.
