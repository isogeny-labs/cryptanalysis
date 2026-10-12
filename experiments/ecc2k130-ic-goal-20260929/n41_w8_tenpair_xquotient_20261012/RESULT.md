# Exact x-quotient lookup finds a new N41 ten-pair public relation

A global-sign quotient of the five-pair left table found a verified ten-pair relation on the frozen N41 public point after **136,258 target-dependent right probes**. The earlier full-point table, with the same source states, random seed, left kept-state count, and right sequence, needed **898,812** probes to its first accepted relation. Checked Sage independently reconstructed this run's 20 distinct source leaves, ten pair points, raw preimage sum, cofactor-four public point, and 20-column folded row. Twelve columns are new relative to the prior six- and nine-pair rows, raising their joint rank to three.

The instance is `EC1N41Ckb1h7d5e80d3c4d0` over `GF(2)[t]/(t^41+t^3+1)`, curve `y²+xy=x³+1`, prime subgroup order `549756390943`, cofactor four. The public point is `(920359962848,755404565011)`. The six-rotation W8 source contains 125 rational masks, B=1,000 usable signed-Frobenius points and 117 folded columns. Ten free signed pair slots use rotations `(0,7,14,21,28,35,0,7,14,21)`; each slot has 140 exact states and all selected edges must differ. Four raw preimages of the one public point are queried. This is a relation-stage component, `candidate_id: null`.

## Exact target-conditioned lookup

For every five-state left tuple, the builder computes its group sum `L`, replaces `L` by the canonical point of `{L,-L}` under numeric `y` order, and flips all five state IDs by XOR 3 when negating. The source check verifies that `sid XOR 3` is the exact negative point with the same edge for all 840 frozen states. The table indexes only `x(L)` and retains the canonical `y` and five IDs. Infinity uses a separate sentinel key.

For each right sum `R` and raw target `U`, the query computes `N=U-R` and looks up `x(N)`. On `y` equality it uses the stored tuple; on `y(N)=y(L)+x(L)` it flips all five IDs. The curve equation gives precisely these two points in a nonzero-`x` fiber, so a genuine completion cannot be lost. Every lookup candidate is reconstructed through all five original source points, checked against `N`, checked for edge disjointness, then checked by full ten-point addition against `U`. The successful hit used raw preimage index two and state IDs `(88,24,97,69,100,115,105,37,51,118)`.

| Frozen one-worker run | Full-point prior control | X-quotient run |
| --- | ---: | ---: |
| Left kept states / attempts | 5,000,000 / 6,741,384 | 5,000,000 / 6,741,384 |
| Right kept probes / attempts at accepted hit | 898,812 / 1,211,875 | **136,258 / 183,442** |
| Left build cumulative native time | 10.2516 s | 12.0333 s |
| Accepted-hit cumulative native time | 14.4364 s | 12.8235 s |
| Parent runner wall | 14.861791 s | 13.321680 s |
| Sampled combined peak RSS | 311,984,128 B | 308,051,968 B |
| Independent raw/public/row replay | pass | pass |

The [protocol](protocol.json) froze the source, binary, included group arithmetic, input, random seed, prior receipt, one-worker policy, five-million-state half caps, 180-second parent wall cap, and 4-GiB combined RSS cap before the run. The [receipt](receipt.json) records exact phase lines, process interval, child CPU, stop status, stdout/stderr hashes, and peak sample. The [Sage runtime receipt](sage_runtime_info.json) was saved before the independent [audit](audit_result.json), whose inputs were frozen in [audit_protocol.json]. The prior and new probes follow the same deterministic draw sequence: quotienting changes which sign completions the left index accepts. The reported CPU intervals are exploratory on an unisolated host; the probe counts establish the search-path improvement on this frozen point, while a controlled wall-time ratio requires an isolation receipt and paired runs.

The quotient is an exact two-sign compression of the left lookup. The next test should couple several unresolved pair blocks before expanding them, using a target-derived algebraic constraint with a demonstrable N41 cost below the exact join. An N131 promotion must bound the implicit family size, use the one-worker 600-second/4-GiB gate, and replay an ordinary relation. The full IC candidate remains unspecified.

The [proof map](PROOF_MAP.md) links the group-level soundness and completeness theorem to its pinned Lean check and records the concrete curve and source-state bridge.
