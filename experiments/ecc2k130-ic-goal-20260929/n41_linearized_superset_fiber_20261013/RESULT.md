# Sparse full-product-space GCD with exact usable-source filtering

The fixed-seed N41 right-product image has **128 field elements** and a
degree-128 vanishing polynomial with only eight nonzero power-of-two
terms. Replacing the explicit 32-usable-product polynomial by this full
linearized-space polynomial preserved the known public-point witness and
rejected a same-seed control. The final source check is essential: an
excluded zero product produced a genuine algebraic GCD root that the
usable-source predicate removed. An independent pair-equation calculation
found one excluded-product solution and zero usable-product solutions at
that same proposed four-atom coordinate.

| Frozen N41 public-target case | Target-derived right candidates | GCDs | Usable hits | Internal query wall |
| --- | ---: | ---: | ---: | ---: |
| Known positive left family | 16 | 481 | 1 | 23.688 s |
| Slot-1 same-seed control | 16 | 512 | 0 | 27.623 s |

The [protocol](protocol.json) froze the same public point and source
families as the earlier exact 32-root query. Its checked-Sage
[run](result.json) completed in 61.907 seconds parent wall, with 0.922
seconds internal full-space setup and 216,694,784 B sampled peak Sage
RSS. The process-tree monitor was degraded by macOS child-discovery
permission; the host had no CPU isolation receipt. These timings describe
the two stage queries only. The explicit usable-product GCD on the same
families previously took 9.891 and 12.200 internal seconds under different
host contention. The full-space variant's value is its sparse polynomial
representation and exact postfilter semantics, rather than a measured N41
timing gain.

The excluded-product control fixed the first usable product, examined all
96 products outside the usable right bin, and found one algebraic field
output: `q=0` with proposed right reciprocal `156396289942`. Its
unfiltered GCD had degree one. Checking all 32 usable first products gave
zero usable hits. The [independent pair-equation audit](audit.json)
confirmed one positive usable match, zero usable matches at the excluded
coordinate, and one match when the excluded zero product was offered.
The [terminal verifier](terminal_verification.json) binds those decisions,
source hashes, raw query logs, resource status, and accepted runtime.

The first invalid-source control skipped `q=0` and ended at its assertion;
its source and raw stderr are retained. The next version found the root
but failed while serializing a Sage integer; its source and partial output
are retained. The final control converted that value and completed. These
statuses describe control-script failures, not source-law negatives.

The [proof map](PROOF_MAP.md) contains the mathematical argument and a
checked Lean source-filter equivalence. The N131 W18 seed bin has 33,191
usable products inside a full `2^17` product image. The next experiment
is a native one-worker probe that constructs its sparse degree-`2^17`
vanishing polynomial, specializes the four-atom equation at a checked
positive block output, filters recovered roots to exact usable codes, and
charges build, GCD, root extraction, and filtering separately under the
600-second/4-GiB envelope. The existing W15 native linearized-product
code supplies a starting implementation; the source set and rotation must
be replaced and independently replayed.
