# Full W29 terminal stream and linear half-trace query

**A precomputed linear half-trace map completed an exact full-domain W29
two-pair terminal query in 69.330 seconds on the constructed N131 residual,
versus 303.087 seconds for the direct half-trace implementation on the
same 134,219,672-output stream.** Both queries derived 268,439,344 S3
roots, produced the same full-stream digest, and recovered the pair-code
witness `(22,29)`. On the frozen public raw-point residual, both complete
queries again agreed on every aggregate count and digest, with zero
product-image hits; their observed parent walls were 94.407 and 314.383
seconds. These are ordinary-host component measurements. The staged method
has `candidate_id: null` while the remaining three free pair families and
complete IC pipeline are unresolved.

## Exact instance and method

The field is `GF(2)[u]/(u^131+u^13+u²+u+1)`, curve
`y²+xy=x³+1`, ID `EC1N131Ckb1heb5f1998f20b`. The fixed-seed W29
source uses seed mask `898618`, 28 free source-code bits at positions
`0..18,20..28`, left Frobenius rotation 54, and right rotation 72. The
constructed residual reciprocal is
`1240393003299480760304964344285952783315`; the public raw-point
reciprocal is `770794657550069419943936485965613853151`, independently
checked as the inverse of the archived public point's x-coordinate.

The reusable source producer visited all `2^28` codes, retained
67,109,836 endpoint-valid codes, and wrote both nonzero pair-output
reciprocals for each one. Each output occupies 17 bytes in the binary
stream, **2,281,734,424 bytes total**. The producer's full-domain count,
quadratic-failure count, and digest exactly match the earlier independent
W29 census. It used 149.731 seconds parent wall and 28,721,152 bytes
sampled combined peak RSS. This source preparation precedes both
target-dependent query intervals.

For left output `c` and target residual `t`, put
`A=1+(ct)²`, `B=ct`, `D=(c+t)²`, and `z=c+1/c+t+1/t`. The exact S3
root argument satisfies `AD/B²=z²`. The baseline computes the 66-term
half-trace of `AD/B²` for every left output. The new query precomputes
the half-trace image of each of the 131 field basis bits squared, then
XORs those images for the set bits of `z`. Both versions check the
Artin–Schreier equation, derive the two right outputs, decode the unique
right source product with the fixed-seed linear basis, and check S3
before reporting a hit. The source-product inverse and exceptional
branches are exact; every output in these two full scans took the
nonexceptional branch. All 134,219,672 left outputs were
trace-compatible on both residuals, so the root count is exactly twice
the output count. The checked [proof map](PROOF_MAP.md) states the field
and trace hypotheses and the remaining concrete formalization bridge.

## Frozen one-worker measurements

All four target-dependent scans read the same SHA-256-pinned 2.28 GB
stream, used one worker, and completed below the frozen 590-second parent
wall and 4-GiB combined-RSS caps. The query interval begins after
reusable source preparation and includes stream reads, batch inversions,
root generation, product-image membership, S3 checks, and hit reporting.
Checked-Sage auditing followed outside the interval. The physical host
was not isolated, so the paired ratios are exploratory stage diagnostics.

| Residual | Root algorithm | Parent wall | Native interval | Roots | Product-image hits | Sampled peak combined RSS |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Constructed right-two-pair sum | Direct half-trace | 303.087 s | 303.069 s | 268,439,344 | 1 | 47,349,760 B |
| Constructed right-two-pair sum | Linear map | **69.330 s** | 69.282 s | 268,439,344 | 1 | 47,185,920 B |
| Frozen public raw point | Direct half-trace | 314.383 s | 314.326 s | 268,439,344 | 0 | 47,480,832 B |
| Frozen public raw point | Linear map | **94.407 s** | 94.364 s | 268,439,344 | 0 | 47,038,464 B |

The observed parent-wall stage ratios are 4.372 on the constructed
residual and 3.330 on the public residual. Host-frequency, affinity,
throttling, and noise receipts required for a Tier 1 or Tier 0 speed
comparison were not collected. The exact workload counts, digest
agreement, and operation replacement are the algorithmic evidence.

## Replay and evidence boundary

The [independent checked-Sage audit](audit_result.json) compared the
first 2,128 binary stream outputs with every archived Sage output from
the first 4,096 W29 source codes. It reconstructed their source codes,
checked endpoint eligibility and pair-output quadratics, and tested the
square identity and 131-column half-trace table on 256 frozen
coordinate/target cases. It replayed every reported hit's code, source
eligibility, pair quadratics, and S3 equation. Both constructed queries
reported the same reciprocal pair
`(1086750577208236436978597812999327289651,
2574347418686931891520539840794901883705)` at stream index six,
matching the earlier Sage-audited `(22,29)` witness. The two public
queries reported zero hits and identical digests. The native paths
share the finite-field kernel and source-product decoder; the Sage audit
independently checks a finite prefix and all emitted hits, while the
full-domain zero-hit agreement is between two native root paths.

The separate [N41 linear-map control](n41_linear_control_result.json)
replayed all 562 left outputs of the prior ordinary public-derived
terminal residual. Its direct and table half-traces agreed on every
input, all 1,124 S3 roots matched the exact quadratic solver, and the
single product-image hit was the previously audited `(253,63)` pair.
This checks the optimization across a second field degree and against
the existing unpinned N41 relation control.

The [producer receipt](produce.receipt.json), four query protocols and
receipts, checked [Sage runtime record](sage_runtime_info.json), compiler
hashes, raw stdout/stderr, and [terminal verifier](verification_result.json)
bind the measured execution. Lean 4.34.1 built four results and
`#print axioms` reported only standard foundations. The first auditor
stopped at an overly strict helper for trace-one half-trace table
columns; its [protocol](audit_v1.protocol.json) and [stderr](audit_v1.stderr)
are preserved. The revised auditor computes the raw 66-term table
columns and passed. The exact 2.28 GB stream remains on this local
workspace as `all.bin`, ignored by Git; its SHA-256 digest in the
receipts is `9d612838d04f0f43fee70c154bcbbe11de5424b3b15fa186954114832f538881`.

## Next experiment

The completed terminal takes 69–94 seconds for **one** supplied
residual. The five-pair relation search requires a target-conditioned
constraint over the other three free pair families before their
Cartesian expansion. The next controlled experiment should freeze an
unpinned N41 public relation, test a lossless joint filter on multiple
still-free source-code blocks, count entire families rejected before
partial-sum enumeration, and compare its complete query cost with the
native N41 join. An N131 public-point run follows only if that
filter's source-bound projection fits one worker, 600 seconds, and
4 GiB. Relation rank, factor logs, unseen target recovery, and matched
same-point rho remain later full-pipeline gates.
