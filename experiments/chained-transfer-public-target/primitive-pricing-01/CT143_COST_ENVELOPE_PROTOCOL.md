# CT143 — exact single-target norm-reuse break-even envelope (pre-code contract)

Date: 2026-11-15. Standing: [pcc:unverified]. Root: crypto #3877; comparator control crypto #4215; norm-reuse derivative cryptanalysis #1533; custody extension #1562.

## Question and reason for a separate test

CT142 reports block-paired `C169 - C13_first - C13_second`. This is the **difference between two optimized map routes**, not the cost saved by norm-point reuse or the full ECDLP advantage. A positive sign alone is **insufficient**. Before native execution, freeze the correct route algebra and an implementation-independent self-test. Preserve original CT126 and CT142 sources, their synthetic fixtures and all negative runs.

## Exact model (one selected call, matched scalar and field)

For nonnegative primitive costs `a=C169`, `b=C13_first`, `c=C13_second`, `d=D`:

- Direct original `2a`, reuse `a+d`; saving `a-d`.
- Literal two-hop original `2(b+c)`, reuse `b+c+2d`; saving `b+c-2d`.
- Retained two-hop original `2(b+c)`, reuse `b+c+d`; saving `b+c-d`.
- Before route-dependent corrections, best original = `2 min(a,b+c)`; best reused = `d + min(a,b+c)`. Hence **single-call gross headroom** is `min(a,b+c)-d`.
- Optimized direct minus optimized retained = `a-b-c`. It ranks the two optimized routes only. It cannot establish positive reuse headroom.
- Let `h >= 0` be **additional** cold per-target setup/transfer/verification/LA time of reuse relative to the matched best original solver, including all costs not in the four primitives. Positive total saving requires **strictly** `h < min(a,b+c)-d`. If this gross headroom is nonpositive, no nonnegative `h` can make reuse faster in this model.
- These are arithmetic identities within the stated fixed operation-count model, **not** a theorem about real timings, probability distributions, group transfers or an end-to-end DLP.

## Frozen implementation and acceptance

Create additive `ct143_cost_envelope.py`. It must use exact rational arithmetic on raw CT126 12-block per-call samples, never floating point for sign or strict threshold, and invoke CT142 receipt and CT126 arithmetic/schema gates for admitted four-arm JSONL. Report all four-arm/12-block (48) envelopes, per-route gross headroom, direct-vs-retained ranking and strict nonnegative-extra-overhead criterion; avoid unpaired pooled median subtraction.

Run `--self-test` in normal and optimized Python using **standalone constructed synthetic costs** and 8 or more metamorphic/negative controls: invariance under common scaling, route transition boundaries, zero/negative saving, exact break-even, strict-inequality failure, variable setup overhead, positive-only primitive inputs, and independence of `a-b-c` from `d`. Exit nonzero upon any acceptance failure. Add source-guard CI tests only; never run native evaluators through `pull_request` or unadmitted dispatch. Add a synthetic mismatched-metadata corruption check through CT142, not a new implicit trust path. Outputs remain [pcc:unverified], with provenance/receipt hashes and full gates kept separate.

## Boundaries and next experiment

The original q223 primitive-price evaluator covers five known scalars, not the frozen original-prime 695/701-record Jacobian or a recovered unknown logarithm. No pricing has been measured and no improvement is claimed. After owner-approved bounded native execution, use the 48 guarded blocks to determine whether the gross headroom is consistently positive and its maximum allowable additional overhead; separately replay the 695/701 originals with checked scalar solutions and compare complete cold rho/BSGS/IC including source-side setup, norm corrections, LA, peak memory, uncertainty and signed PCC. Failure or instability is recorded as a negative or inconclusive result, never promoted.

Sources checked: crypto #3877, #4215; cryptanalysis #1533, #1549, #1553, #1562 and CT126 `src/main.rs`/`check_pair.py`; source prior reference Bostan–Morain–Salvy–Schost (2008), `arXiv:cs/0609020` as cited in CT141. Shared research-KB MCP and repository wrapper are unavailable in this connector/sandbox run, so no novelty/absence inference is made.

## Pre-execution amendment: matched cross-arm diagnostic (same date)

The per-arm 48-block identities do not by themselves compare the original binary to the reuse binary; those binaries can have distinct measured primitive costs. Add a separate 24-row **cross-arm** diagnostic: match `original-1[i]` to `reuse-1[i]`, and `original-2[i]` to `reuse-2[i]` for each of twelve fixed block indices `i`. Report `min(2*a_original, 2*(b_original+c_original)) - (d_reuse+min(a_reuse,b_reuse+c_reuse))` with exact rational arithmetic, plus the strict nonnegative-extra-overhead condition. Both sides must pass CT126/CT142 custody and A/A checks; never combine pooled medians to synthesize a paired advantage. The block indices are not synchronized across processes, so call these **ABBA-position-matched diagnostics**, not independent cold-solve pairings or a fixed whole-cohort solver comparison. Test the cross-arm expression on altered original/reuse synthetic costs before enabling it for admitted output. No run or price is being claimed.
