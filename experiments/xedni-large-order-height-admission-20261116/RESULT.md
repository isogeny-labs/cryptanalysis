# Larger-order xedni lift admission with the public search charged

On eight preselected prime-order subgroups of orders 293–599, the frozen fresh-query panel found **17 public coefficient relations in 6,656 vector tests**. For those 17 events, the 27-shift rational construction produced valid witnesses in every variant. At a 128-bit cap on the complete witness, four events had an admitted shifted witness, versus two under the centered construction. At 384 bits all 17 were admitted by some shift, versus 11 centered. Thirty-two deterministic first-nonrelation controls produced 864 valid rational constructions but zero matches to their required second public point.

## Inputs and accounting

The [protocol](protocol.json) pins the eight fields from the earlier [larger-order numerical admission panel](../xedni-large-order-admission-20261115/RESULT.md) by the source result's SHA-256. It selects the first subgroup generator by an ordered finite-point rule. For each field, four target scalars are derived by SHA-256 from `xedni-large-height-v1|p|j`; the public points `Q=wG` are constructed outside the attempt phase. The first 16 admissible ordered pairs from offsets `[0,1,2,3,5,8,13,21]` define `U=Q−t₁G` and `V=Q−t₂G`. All 13 frozen coefficient vectors are tested on each pair, giving 8 × 4 × 16 × 13 = **6,656** public tests. Every test, including 6,639 nonrelations, is retained in [public.jsonl.gz](public.jsonl.gz).

| Field `p` | Subgroup `q` | Public hits / 832 tests |
| ---: | ---: | ---: |
| 313 | 331 | 2 |
| 421 | 439 | 1 |
| 431 | 419 | 3 |
| 547 | 571 | 1 |
| 571 | 599 | 2 |
| 593 | 313 | 1 |
| 617 | 293 | 3 |
| 677 | 353 | 4 |
| **Total** | | **17 / 6,656** |

For each hit, and for the first nonhit on each of the 32 targets as a control, the producer computes the finite common preimage `S=b⁻¹U` and centers its coordinates `(x₀,y₀)`. It evaluates all 27 triples `(kₓ,kᵧ,k_A)∈{-1,0,1}³`:

```text
x=x₀+kₓp,  y=y₀+kᵧp,  A=−1+k_Ap,
B=y²−x³−Ax,  T=(x,y)∈E_{A,B}(ℚ),  P=bT,  R=−aT.
```

The full-witness score is the largest numerator or denominator bit length among `A,B,Px,Py,Rx,Ry`. All 1,323 lift attempts are retained in the eight ordered `lifts.jsonl.partNN.gz` files listed in [storage-amendment.json](storage-amendment.json): 459 positive and 864 control variants, with zero construction failures. The source run wall interval was 0.63 seconds on this host, excluding the checked Sage startup; it is a diagnostic for this bounded script, without a calibrated same-target comparison.

| Full-witness cap | Centered positive / 17 | Any shift positive / 17 | Bounded control mismatches / 32 | Control admissions |
| ---: | ---: | ---: | ---: | ---: |
| 64 bits | 2 | 2 | 0 | 0 |
| 96 bits | 2 | 2 | 0 | 0 |
| 128 bits | 2 | 4 | 0 | 0 |
| 160 bits | 2 | 7 | 0 | 0 |
| 192 bits | 4 | 8 | 3 | 0 |
| 256 bits | 6 | 9 | 11 | 0 |
| 384 bits | 11 | 17 | 32 | 0 |
| 512 bits | 17 | 17 | 32 | 0 |

The positive median centered score was 322 bits; the median best-shift score was 244 bits, and the median paired reduction was 73 bits. The [storage amendment](storage-amendment.json) records lossless deterministic gzip packaging of the public transcript and eight ordered lift-transcript chunks, their original and compressed SHA-256 digests, and byte counts; the [compression script](compress.py) reproduces it. The [audit](audit.py) verifies decompression against the original producer hashes, then independently reconstructs every finite generator, target, query, group relation, rational point, reduction, and score using pure-Python group laws. It also checks scalar recovery on every public hit. [audit.json](audit.json) records `PASS` with empty stderr. [run-result.json](run-result.json) retains raw counts and file hashes; [sage-runtime.json](sage-runtime.json) records the verified local Sage build before the run.

The mathematical implication used here is the checked `precommitted_acceptance_iff_public` theorem in the [precommitted vector lift formalization in PR #1660](https://github.com/isogeny-labs/cryptanalysis/pull/1660): once `b·reduce(T)=U`, the second reduction matches `V` exactly when `aU+bV=0`, assuming multiplication by `b` is injective on the finite subgroup. Here `q` is prime and every selected `b` is nonzero modulo `q`. The parent [height-search formalization in PR #1666](https://github.com/isogeny-labs/cryptanalysis/pull/1666) proves the shifted coefficient and rational relation invariants. The concrete reduction checks for this panel are replayed independently in the audit.

The measured admission fraction is conditional on a public hit: at 128 bits it is 4/17 after 6,656 public tests and 1,323 lift attempts. The fixed SHA-derived targets and shared offset/vector family make these counts a deterministic panel, not independent Bernoulli trials. The next experiment should test a lift rule that commits to both public point images before checking a vector relation, with all selection, failed construction, and rank computations charged.

Reproduce with `/Volumes/SSD990/cryptanalysis/sage --runtime-info`, then `/Volumes/SSD990/cryptanalysis/sage -python experiments/xedni-large-order-height-admission-20261116/run.py`, then `python3 experiments/xedni-large-order-height-admission-20261116/compress.py`, then `python3 experiments/xedni-large-order-height-admission-20261116/audit.py` from this worktree.
