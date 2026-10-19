# Quadratic feature rank on Q1358 pair outputs and public-target residuals

An independently replayed set of 8,647 Q1358 pair sums spans the entire
8,647-dimensional Boolean quadratic feature space of the 131-bit sum
\(x\)-coordinate. Three more seeded pair sums yield full quadratic rank in
each of the four public-target translated coordinate sets
\(x(T_j-S)\). Consequently, a nonzero output-only Boolean polynomial of
degree at most two cannot vanish on every pair sum, nor can a separate such
polynomial vanish on every target residual for any one of the four frozen
public-point lifts. This removes a compact quadratic output filter from the
target-conditioned pair-join design space.

## Exact input and method

The exact curve is `EC1N131Ckb1heb5f1998f20b`, with the Q1358 d10 geometry
and four verified public-point cofactor lifts pinned by the
[geometry source](../n131_phi_torsion_frobenius_domains_20261005/m15_d10_static/d10_exact_geometry_v1.json).
The signed pair domain has 532 valid phi codes in each of slots 0 and 1,
with two signs per leaf. The sample draws independent uniform code indices
and a uniform sign on slot 0, keeping slot 1 positive. This is a subset of
the full signed pair domain and is sufficient for a full-rank certificate.
Repeated sum \(x\)-keys are discarded. The frozen [protocol](protocol.json)
sets seed `2026101824`, a 12,000-attempt cap, 600 seconds, one worker and
4 GiB RSS. The [checked Sage runtime](sage_runtime_info.json) was saved
before the run. The IC `candidate_id` is `null`: this is a component
constraint experiment, not a complete IC pipeline.

Feature columns are the constant, 131 low-to-high coordinate bits, and all
unordered pairs \(x_i x_j\), \(i<j\), in lexicographic order. Incremental
GF(2) elimination uses highest-set-bit pivots. The [independent audit](audit_result.json)
reconstructs every point from its frozen code/sign witness, rebuilds feature
rows separately, and eliminates with lowest-set-bit pivots.

| Measured component | Ordinary pair \(x(S)\) | Public residual \(x(T_j-S)\) |
| --- | ---: | ---: |
| Feature dimension | 8,647 | 8,647 per lift |
| Initial sampled draws | 8,720 | Same 8,647 independent pair witnesses |
| Repeated \(x(S)\) draws | 73 | Not used as new rows |
| Additional seeded pair draws | 0 | 3 |
| Final rank | 8,647 | 8,647, 8,647, 8,647, 8,647 |
| Producer elapsed time | 5.241 s | 29.040 s for four lifts and extension |
| Independent audit elapsed time | 24.530 s | 69.536 s for four lifts |
| Peak RSS in producer | 34,897,920 B | 54,149,120 B |
| Peak RSS in audit | 39,354,368 B | 42,090,496 B |

The target translation trial first processed only the initial 8,647
witnesses and recorded ranks `(8646, 8645, 8646, 8647)` in
[translated_result.json](translated_result.json). Its status field incorrectly
said `ALL_FOUR_FULL_RANK`; that first receipt and its
[frozen protocol](translated_protocol.json) are retained verbatim.
The [extension protocol](translated_extend_protocol.json) froze a new seed,
`2026101825`, and a 1,000-draw cap before the repair run. Three draws filled
all four ranks. The [translated audit](translated_audit_result.json)
reconstructed 8,650 distinct pair witnesses, rebuilt translated rows with
different feature code, and independently checked full rank under the
opposite pivot convention.

The [proof map](PROOF_MAP.md) gives the readable linear-algebra argument,
the checked Lean theorem, and the exact external certificate bridge. These
are ordinary-host correctness and component timings; no IC online timing
comparison is inferred from them.

## Next algorithmic gate

An output-only quadratic equation, including one formed after translation
by any frozen public-point lift, cannot reject incompatible pair outputs
exactly on this domain. The next candidate should condition on **joint leaf
codes or middle partial sums** before their combinations are enumerated.
Test that candidate first on the unpinned N41 public-target control with
positive relation replay, then freeze the N131 target-compatible family and
measure generated states, exact rejects, witness completeness, memory, and
all attempted joins under the one-worker/600-second/4-GiB cap.
