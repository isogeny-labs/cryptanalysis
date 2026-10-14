# Complete N41 cross span leaves one universal trace multiplier

Across all **2,048** W6 product families, the reciprocal output-coordinate
spaces span the full 40-dimensional trace-zero subspace of `GF(2^41)`.
Their target-conditioned S3 cross terms also span that entire subspace.
Consequently the trace multipliers that cancel the cross term for
**every** family pair form exactly the one-dimensional space `{0,1}`.
The nonzero universal multiplier `1` gives the already-known trace
identity; any additional useful low-rank trace cut must depend on a
restricted family region. An independent checked-Sage replay verified
all 40 coordinate pivots, all 40 cross pivots, and the full-rank trace
pairing. The [terminal verifier](terminal.json) binds those receipts.

## Source and finite certificate

The exact field is `GF(2)[t]/(t^41+t³+1)`, the curve ID is
`EC1N41Ckb1h023d9a38bbf7`, and the frozen public reciprocal is
`1000731834126`. The source is the W6 **product-span relaxation** of
the [two-family bilinear screen](../n41_bilinear_rank_screen_20261013/RESULT.md).
For each product label `p∈span(t²,…,t^12)` the worker independently
constructs the binary-linear reciprocal-output space `C_p` from the
halftrace and trace equations. It examined 12,310 basis vectors from
all 2,048 families. Gaussian elimination retained 40 coordinate pivots,
whose source family labels and exact field encodings are archived in
[result.json](result.json).

Let `t` be the public reciprocal and let `c,d` range over two family
spaces. The bilinear S3 cross term is

`B_t(c,d)=(tcd)²+tcd`.

Because the map is additive in each argument over `GF(2)`, all possible
cross terms from all family pairs lie in the span of the `40×40` terms
formed from the coordinate-union pivot basis. The worker evaluated all
1,600 such terms and retained 40 independent pivots. Every value has
absolute trace zero by `Tr(z²+z)=0`; thus the upper bound is 40 as well.
The concrete trace-pairing matrix in the polynomial basis has rank 41.
Since the cross span has codimension one and `Tr(1·B_t(c,d))=0`, its
orthogonal complement under that pairing is precisely `span{1}`.

| Frozen measurement | Result |
| --- | ---: |
| Product families processed | 2,048 / 2,048 |
| Coordinate basis vectors examined | 12,310 |
| Coordinate-union rank | 40 |
| Cross-term pivot rank | 40 |
| Trace-pairing rank | 41 |
| Native parent wall / sampled combined peak RSS | 1.336346167 s / 26,066,944 B |
| Independent Sage audit parent wall / sampled combined peak RSS | 33.868281875 s / 236,797,952 B |
| Worker/resource cap | one worker, 120 s and 4 GiB for each job |

The [independent audit](audit_result.json) rebuilt the nine families
needed by the pivot certificate using Sage's field and matrix code,
checked each coordinate against its family, recomputed every cross term,
and obtained ranks 40, 40, and 41 again. It used the repository's checked
Sage launcher and saved [runtime receipt](sage_runtime_info.json).
The native [protocol](protocol.json), [run receipt](run_result.json), and
separate Sage audit protocols fix source and binary hashes, input, cap,
and raw output. Timings are stage diagnostics on an unisolated host.

## Proof and next gate

The written proof above uses bilinearity, the Artin-Schreier trace
identity, the 40-pivot finite certificate, and nondegeneracy of the
field trace pairing. The inherited checked Lean theorem
`BilinearGate.artin_schreier_trace_zero` covers the trace identity;
the [proof map](PROOF_MAP.md) records the remaining Lean finite-field
and rank-certificate bridge. This finite census has `candidate_id: null`.

This rules out a **single universal cross-cancelling linear trace cut**
for the declared N41 relaxed source. The next constructive experiment
must represent **many product-family regions implicitly**, derive
target-conditioned cuts that vary by region, and reject regions before
enumerating family pairs. It should preserve the existing unpinned W8
N41 public relation, then meet the N131 whole-search source bound from
the [paired-cut study](../n41_lowrank_trace_joint_20261013/RESULT.md).
