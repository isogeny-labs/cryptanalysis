# Linked Frobenius pair: an N41 public relation and an N131 source gate

**One source pair reused at Frobenius rotations 0 and 7 produced an independently replayed relation on the frozen N41 public subgroup point in 47.609646958 seconds.** Its two repeated source points fold with coefficient `1 + λ^7`, leaving 18 nonzero folded columns. Against the prior six-, nine-, and ten-pair rows, the new row raises modular rank from 3 to 4 and introduces eight columns. The N131 W18 source census then proves a conservative lower bound of `48,726,983,364,467,415,666,726,804,718,080,936,636,800` labeled nine-code assignments with distinct folded columns, using a rotation gap of 16. This is a source-support result; target-conditioned witness generation is the next algorithmic step.

## Construction and N41 measurement

The ten pair slots use Frobenius rotations `0,7,14,21,28,35,0,7,14,21`. Slots 0 and 1 select the same signed pair state, so the ten slots have nine free signed states and nine distinct source edges. The two corresponding factor-base columns repeat. In the subgroup relation, each repeated column receives its original coefficient multiplied by `1 + λ^7`; the independent [Sage audit](audit_result.json) checks that this factor is nonzero modulo the N41 subgroup order. The other eight slots remain free. The source-point equality is checked under full Frobenius rotation, rather than inferred from the x coordinate alone.

The [protocol](protocol.json) was frozen before running the [native join](join_linked.cpp). It fixes one worker, 5,000,000 kept left states, at most 5,000,000 kept right probes, 180 seconds, 4 GiB combined RSS, and the four raw preimages of the same frozen N41 public point. The [receipt](receipt.json) records 5,000,000 kept left states and 854 kept right probes at the hit, 47.609646958 seconds parent wall, 304,840,704 bytes peak sampled combined RSS, and exit code 0. The native worker checked the full group sum; the separate [Sage audit source](audit_sage.py), run through the checked repository launcher with saved [runtime information](sage_runtime_info.json), replayed the raw point and relation row. The read-only [receipt verifier](verify.py) checks hashes and cross-record invariants.

| Stage | Exact input or result |
| --- | --- |
| Curve | `EC1N41Ckb1h7d5e80d3c4d0`; public point `[920359962848,755404565011]` |
| Input law | Four raw preimages of that single public subgroup point |
| Join | 5,000,000 kept left states; hit at 854 kept right probes, 1,127 attempts |
| Resource envelope | One worker; 180 s; 4 GiB; sampled peak 304,840,704 B |
| Wall | 47.609646958 s parent interval, including process and input work |
| Independent audit | `PASS_INDEPENDENT_N41_LINKED_FROBENIUS_PUBLIC_RELATION`; 18 nonzero columns; rank 3 to 4 |

The timing is an exploratory stage measurement on an unisolated host. It is not a one-target online IC pipeline measurement. `candidate_id` remains `null` because factor-base log solving, target descent, and scalar recovery are not wired into this candidate.

## N131 projection and search gate

The frozen W18 seed-212 source has 33,191 pair codes. The exact column-conflict census contains 65 unequal code pairs; any code conflicts with at most two other codes. Sequentially selecting nine codes while excluding each earlier code and its at most two conflicts leaves at least

`∏_{i=0}^{8}(33191 - 3i) = 48,726,983,364,467,415,666,726,804,718,080,936,636,800`

labeled assignments with 18 distinct folded columns before the linked duplication. Dividing by the N131 subgroup order `680564733841876926932320129493409985129` gives 71.5978670969 as a **uniform-mapping heuristic mean** for labeled tuples per target; collisions between sums and the actual target distribution are unmeasured. The [projection record](projection_result.json) keeps the exact integer ratio and source hashes. For the two roots of `X²+X+2` modulo the subgroup order, `1+λ^16` is respectively `99717920955595431923619593794150750754` and `580846812886281495008700535699259234826`, both nonzero. Thus either possible subgroup Frobenius eigenvalue preserves the linked columns at rotation gap 16.

The [fixed-list join coverage proof](../n131_w18_tenpair_mitm_bound_20261012/RESULT.md) bounds a five-million-by-five-million N131 join over all 131 rotations at `4.81218×10^-24` success probability for a uniform target. The N41 join implementation therefore supplies a correctness control, while the N131 step needs a target-dependent generator or compact constraint that rejects families before building fixed half lists. The previous [N131 ten-pair binary-Frobenius query](../n131_w18_tenpair_binary_frob_20261012/query_result.json) recorded `BOUNDED_UNKNOWN` after 588.5150735 seconds and does not measure the linked source.

## Proof and next experiment

The [Lean theorem](LinkedFactor.lean) proves `λ^a + λ^(a+k) = λ^a(1+λ^k)` over natural numbers; see the [proof map](PROOF_MAP.md) for its exact scope. The code-conflict count and modular eigenvalue checks are executable arithmetic certificates in [projection.py](projection.py), frozen by [projection_protocol.json](projection_protocol.json). The next experiment is a linked-source N131 Boolean circuit with slot 1 constrained to the full Frobenius image of slot 0, the 18-column shield, and the existing one-worker 600-second/4-GiB public-query cap. Before that query, a constructed control must check source completeness and independent group replay. Measure solver status and target-dependent cost on the public query; a bounded result stays recorded at its cap.
