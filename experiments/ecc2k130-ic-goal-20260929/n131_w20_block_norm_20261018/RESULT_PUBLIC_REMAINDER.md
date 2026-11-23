# Exact block-norm classification of the N131 W20 public two-pair residual

**The ordered 132,045-code W20 source has an empty two-code resultant-zero
set for the frozen public two-pair residual in `coefficients.tsv`.** The first
run completed public blocks 0–19 before its 600-second cap. A frozen
continuation completed blocks 20–32 in 218.818 seconds of parent wall time.
All 33 block GCDs had degree zero, so their disjoint union covers every
ordered second code: 32 blocks of 4,096 and one block of 973. This is an exact
classification of this residual under the recorded field arithmetic and
input coefficients, rather than a statistical estimate from sampled pairs.

The public residual is the two-pair control from `coefficients.tsv`, distinct
from the full frozen challenge point in `fresh_target_public.json`. The
continuation is a separate run; the first run's 600.036-second parent time
also included a completed constructed row. These receipts do not constitute
one public query completing inside the 600-second cap.

| Run | Public block indices | Codes covered | GCD degrees | Parent wall | Peak sampled combined RSS | Status |
| --- | --- | ---: | --- | ---: | ---: | --- |
| [First full-source run](receipt_132045_b4096.json) | 0–19 | 81,920 | all zero | 600.036 s | 293,142,528 B | `BOUNDED_UNKNOWN` at wall cap |
| [Frozen continuation](receipt_public_remainder.json) | 20–32 | 50,125 | all zero | 218.818 s | 193,429,504 B | `COMPLETE_NATIVE_NTL_PUBLIC_REMAINDER_BLOCK_NORM` |
| Union audit | 0–32, each once | **132,045** | all zero | separate runs | — | `EMPTY_EXACT_PUBLIC_TWO_PAIR_RESIDUAL` |

The continuation used one native NTL worker, 600 seconds and 4 GiB as caps,
the same selected source and 4,096-code blocks as the first run, and the
public target index 1. It rebuilt the degree-132,045 first-product vanisher
in 32.983 seconds, then spent 0.125 seconds constructing block quartics,
7.122 seconds building block products, and 177.767 seconds in GCD plus root
localization. Its completed row took 185.031 seconds of worker time. The
parent wall included process startup, input, monitoring and source setup.
These timings are ordinary-host stage measurements.

[`protocol_public_remainder.json`](protocol_public_remainder.json) fixes the
worker and runner hashes, source and NTL/GMP hashes, interval, caps, and the
SHA-256 of the prior receipt. [`verify_public_remainder.py`](verify_public_remainder.py)
checks those hashes, both receipt hashes and monitors, exact block indices,
block sizes, zero degrees and zero pairs, and the union count. It emits
`PASS_PUBLIC_REMAINDER` and `EMPTY_EXACT_PUBLIC_TWO_PAIR_RESIDUAL`.
The [proof map](PROOF_MAP.md) links the block-union implication to its checked
Lean theorem and records the computational bridge from NTL GCDs to the
specific field and coefficients.

## Next target-conditioned test

The empty public residual supplies a complete negative control for any
partial-sum family filter. A useful filter must reject this residual early
while preserving the constructed residual's independently verified pair
`(3,16722)`. Freeze both residuals, rank them using only coefficients and
small sketches of the first-product vanisher, and replay the exact block-norm
oracle only after the ranking is fixed. Charge sketch construction, false
positives, and every queried block to the same one-worker cap. Promotion to
the full challenge point requires an ordinary factor-base relation with an
independent point-addition replay; the current union result alone supplies
the negative-control label, not that relation.
