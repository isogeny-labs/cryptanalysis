# Native N41 suffix-axis traversal and exact algebraic gates

The exact four-free-pair-state N41 traversal now completes in **1.32–1.33 seconds** in three native runs on the frozen public raw point. It performs all 2,715,648 first-three state sums, uses a target-conditioned index to resolve the fourth pair-code axis, and reproduces the unique seven-pair witness `(97,151,42,0,14,109,51)`. A 100-root algebraic batch-norm pilot preserved the same witness but spent **51.45 seconds** in polynomial GCDs, making that implementation a poor replacement for the native index.

## Frozen instance and algorithms

The instance is `EC1N41Ckb1h7d5e80d3c4d0`, `GF(2)[t]/(t^41+t^3+1)`, curve `y²+xy=x³+1`, subgroup order `549756390943`, raw target `(1970584690684,115750356512)`. Pair slots 0–3 each have 160 signed states in 40 source codes; slots 4–6 are fixed at state IDs `(14,109,51)`. The first-two family file has 1,554 admissible code pairs. The [input producer](n41_fouraxis_native_prepare_20261025.py) checks the archived traversal protocol's source hashes and exports 643 source-state rows, 160 target-index rows, and all family rows to [the exact native input](n41_fouraxis_native_input_20261025.tsv).

The [native traversal](n41_fouraxis_native_20261025.cpp) computes each admissible first-two state sum, extends it by a third state, and probes the 160-entry map of target residual points. A hit expands the fourth state only after the lookup; it checks distinct folded columns, sums all seven points, and verifies the raw target. It validates field coordinates and every input point against the curve. The comparison is with the archived Sage traversal on the *same frozen search*: that recorded 22.101 seconds in its traversal loop and 22.708 seconds including setup. The native loop's implementation-level ratio to that earlier Sage loop is about 16.6–16.7. These ordinary-host runs are stage diagnostics across different language implementations, not a Tier 0/1 paired IC/rho result.

The exact algebraic alternative uses the third source products `p` and a first-two prefix chart `u`. For the suffix chart variable `T`, set `B=u(u+1)T(T+1)`, `D=T²+u²`, and `S=s²`. The specialized quartic is

`R(p,T)=D²+S²+(S²+S)B²+p B(D+S)+p²D(D+1)`.

For a fixed `u`, the [batch-norm pilot](n41_suffix_norm_pilot_20261025.py) multiplies the quartics over all 40 actual third-source products and takes one GCD with the vanisher of the 160 frozen suffix charts. A nonconstant GCD is equivalent to at least one product/chart root. The pilot tests the known witness root and 99 seeded ordinary prefix roots. The witness GCD had degree one and resolved to `(fourth state 0,left 24,right 37,root 2,third code 10)`; all sampled ordinary roots had degree zero. Its measured 100-root costs were 4.122 seconds to build norms and 51.453 seconds for GCDs. Straight-line scaling to all 12,432 prefix roots would exceed 1.9 hours; that is a projection, not a full measured run.

The compact right-quotient gate from the previous step is represented by [RightQuotient.lean](RightQuotient_20261024.lean). The image vanisher for `L_λ(p)=p²+λp` is `∏_{p∈V}(Y+L_λ(p))`, and its zero test is exact over the recorded source-product span. A coefficient recurrence evaluates the same predicate without enumerating the full span. The Lean module proves the image-vanisher composition and membership statements and the chart identities `A=1+B`, `D=T²+u²`, and the simplified resultant. The link between the compact coefficient recurrence and the image vanisher is algebraically derived and computationally checked on frozen chart queries; its Lean formalization remains open. The concrete curve/source/chart bridge is checked by the frozen Sage and native replays.

## Measurements and replay

| N41 frozen four-axis traversal | Sage archive | Native run 1 | Native run 2 | Native run 3 |
| --- | ---: | ---: | ---: | ---: |
| Eligible triples | 42,432 | 42,432 | 42,432 | 42,432 |
| Eligible quadruples | 1,386,816 | 1,386,816 | 1,386,816 | 1,386,816 |
| First-three state sums | 2,715,648 | 2,715,648 | 2,715,648 | 2,715,648 |
| Verified matches | 1 | 1 | 1 | 1 |
| Traversal loop, seconds | 22.101 | 1.331 | 1.333 | 1.323 |

The native interval begins after parsing the frozen input, constructing compatibility masks, and building the 160-point target index. It ends after the complete family traversal and exact hit replay. Setup is separately recorded at 0.001–0.003 seconds. The run file is [n41_fouraxis_native_runs_20261025.jsonl](n41_fouraxis_native_runs_20261025.jsonl). The checked Sage launcher was used for the norm pilot; its [runtime receipt](n41_suffix_norm_sage_runtime_20261025.json) was captured before that run. Native compilation used Apple clang 17.0.0 on Darwin arm64 with `-O3 -std=c++20 -Wall -Wextra -pedantic`; the [compiler receipt](native_compiler_20261025.txt), compiled binary, and exact input are saved here. `candidate_id` is `null` because this is a point-decomposition traversal stage, with the last three pair states fixed.

Reproduce and verify from the repository root:

```sh
python3 experiments/ecc2k130-ic-goal-20260929/n41_cubic_product_inverse_20261024/n41_fouraxis_native_prepare_20261025.py
c++ -O3 -std=c++20 -Wall -Wextra -pedantic experiments/ecc2k130-ic-goal-20260929/n41_cubic_product_inverse_20261024/n41_fouraxis_native_20261025.cpp -o /private/tmp/n41_fouraxis_rebuild
/private/tmp/n41_fouraxis_rebuild experiments/ecc2k130-ic-goal-20260929/n41_cubic_product_inverse_20261024/n41_fouraxis_native_input_20261025.tsv
./sage -python experiments/ecc2k130-ic-goal-20260929/n41_cubic_product_inverse_20261024/n41_suffix_norm_pilot_20261025.py
lean experiments/ecc2k130-ic-goal-20260929/n41_cubic_product_inverse_20261024/RightQuotient_20261024.lean
python3 experiments/ecc2k130-ic-goal-20260929/n41_cubic_product_inverse_20261024/verify_suffix_pivot_20261025.py
```

The [Lean output](right_quotient_lean_stdout_20261025.txt) reports only `propext`, `Classical.choice`, and `Quot.sound` for the six checked declarations; the build exited zero. [The proof map](PROOF_MAP_SUFFIX.md) records exact hypotheses and the remaining recurrence bridge. `lean4checker --fresh` was unavailable on this host. The next algorithmic step is an exact constraint coupling at least three still-free pair families before specializing a terminal residual; neither a fast fixed-suffix lookup nor a per-root membership predicate reduces the full five-free-family search by itself.
