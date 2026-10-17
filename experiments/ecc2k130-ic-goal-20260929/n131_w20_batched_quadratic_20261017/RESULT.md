# Batched normalization of the N131 W20 quadratic-algebra oracle

## Contribution

Batching the two nonexceptional quadratic denominators across the full 264,090-left-root scan reduces the exact 19-step N131 product-span recurrence from eight field multiplications and three squarings per step to four multiplications and two squarings per step. On identical frozen source tables and the same two target points, the new oracle returned **exactly the same hit sets** as the archived division-free oracle. In the reverse-order paired run, total child CPU was **1.69 times lower** on the constructed point and **1.64 times lower** on the ordinary public point. The new implementation used about 88 MB peak RSS versus about 16.5 MB for the baseline, within the frozen 4 GiB envelope.

The child CPU improvement is an implementation result for this target-conditioned two-pair component. Parent wall varied sharply on the shared host: the two paired runs give opposite wall orderings on the constructed point. The measurement does not establish an isolated wall-time gain or a complete one-target IC/rho result. `candidate_id` remains `null`.

## Exact recurrence

For a left reciprocal coordinate `c` and residual target reciprocal `t`, the right reciprocal coordinate `b` obeys `A b²+B b+E=0`, with `A=1+(ct)²`, `B=ct`, and `E=c²+t²`. The right pair product is `p(b)=C b+H/b`. On the nonexceptional chart `A,E != 0`, the pair and target equations give

`p(b) = u₀ b+v₀`, where `u₀=C+H A/E` and `v₀=H B/E`.

Since `b²=(B/A)b+E/A`, if the `i`th linearized product-span polynomial evaluates to `Lᵢ(p(b))=uᵢb+vᵢ`, then

`uᵢ₊₁=(B/A)uᵢ²+αᵢuᵢ`, `vᵢ₊₁=(E/A)uᵢ²+vᵢ²+αᵢvᵢ`.

The `αᵢ` are exactly the archived 19-step product-span coefficients. One Montgomery batch inversion of all nonzero `A` and `E` values yields their individual inverses with a prefix scan and reverse pass. This adds linear source-scan work and memory while removing the carried denominator from all 19 target-dependent recurrence steps. Exceptional `A=0` or `E=0` still takes the archived exact-root fallback; neither frozen target encountered one. For `u₁₉!=0`, the same resultant `A v₁₉²+B u₁₉v₁₉+E u₁₉²=0` tests whether `b=v₁₉/u₁₉` is a quadratic root. The source-code, curve-pair, and folded-column checks are unchanged.

The pinned Lean 4.34.1 [theorem module](NormalizedStep.lean) proves the initial normalization identity, the monic quadratic reduction, the linearized update, and the reverse batch-inversion step under exact ring/field and characteristic-two hypotheses. `#print axioms` reports only `propext`, `Classical.choice`, and `Quot.sound`; the proof map names the computational bridge.

## Frozen controls and measurements

The [protocol](protocol.json) binds both native source and binary hashes, the original positive and ordinary point fixture, W20 source support and valid-code bitmap, the archived N41 audit, the exact command order, one worker, a 600-second parent cap per query, and 4 GiB RSS. The second [CPU protocol](cpu_protocol.json) freezes the reverse order with a 180-second parent cap per query. Both binaries scanned 132,045 valid codes and 264,090 left roots on each point. The [verifier](verification.json) checked all eight terminal result hashes and identical query dictionaries, including the constructed hit at codes `(3,16722)`, its exact coordinates and distinct columns, and zero full-span hits on the ordinary point.

| Frozen point | Baseline child CPU, second pair | Batched child CPU, second pair | Baseline / batched CPU | Baseline peak RSS | Batched peak RSS |
| --- | ---: | ---: | ---: | ---: | ---: |
| Constructed first-two-pair target | 14.657 s | 8.693 s | **1.686** | 16,465,920 B | 88,391,680 B |
| Ordinary public raw point | 14.317 s | 8.714 s | **1.643** | 16,482,304 B | 88,375,296 B |

Child CPU includes binary startup, source-table construction, inverse batch setup, recurrence, and source recovery. The positive and ordinary comparisons were each paired on the same frozen point, source table, compiler class, one-worker process, and memory cap. Parent wall intervals from the two orderings were: constructed baseline 38.9 and 76.0 s, batched 72.6 and 15.6 s; ordinary baseline 82.3 and 69.0 s, batched 41.3 and 15.1 s. These ordinary-host wall records are preserved, including their noise, rather than promoted as a speedup ratio.

The N41 control re-evaluated the normalized and archived denominator-carrying predicates on all **5,200** inputs of the frozen 65-residual, 80-left-root panel. They agreed on every decision, retained the independently audited unpinned relation coordinate once, and encountered no exceptional quadratic. The control inverted 10,400 nonzero denominators in 65 batches and completed in 28.362 s on this ordinary host. This is a component control conditioned on supplied residuals; it does not replace an unpinned N41 relation search.

## Next gate

The normalized kernel can serve as the right-span test when a joint solver proposes residuals while several pair-code families remain unresolved. The next experiment needs to couple at least two such families and the public target before generating residuals, then count full source-bound attempts and recover an unpinned relation on the frozen N41 point. Only a complete configuration projected below one worker, 600 seconds and 4 GiB should be promoted to the frozen N131 ordinary relation query. Factor-base rank, target descent, and same-point rho remain separate charged stages.
