# N131 W20 global source norm retains a verified pair through 4,096 codes

**The target-conditioned global norm recovered source codes `(3,16722)`
on the frozen N131 constructed point with 256, 1,024, and 4,096 valid W20
codes left free in each pair slot.** The 256-code norm also returned a
degree-zero GCD on the paired frozen public raw point. An independent
native field implementation exhaustively evaluated all code pairs on
both points at widths 256 and 1,024 and found the same single positive
pair and no public-point pair.

## Frozen source and method

The field is `GF(2)[u]/(u^131+u^13+u²+u+1)` and the curve is
`y²+xy=x³+1`, ID `EC1N131Ckb1heb5f1998f20b`. The exact selected W20
source contains 132,045 valid unordered pair codes for seed mask 898618.
The subset at size `n` is the first `n−1` ascending valid codes plus the
known positive code 16722. It includes first code 3. This source law is
explicitly a correctness and scaling pilot; all other valid codes remain
outside these three measured subsets.

For each selected source code `c`, compute `p_c=a_c(a_c+s)` and
`q_c=p_c^(2^18)` in the N131 field. The frozen 13-term W33 resultant
`F_T(X,Y)` is evaluated on the W20 embedded source. The worker forms
`N_T(X)=∏_c F_T(X,q_c)`, intersects its roots with
`A(X)=∏_c(X+p_c)` by polynomial GCD, and localizes each first-code root
to its second-code factor. This is one exact target-conditioned decision
over the entire selected two-code Cartesian family. The
[proof map](PROOF_MAP.md) states the finite-product theorem and concrete
formalization boundary. `candidate_id` is null at this component gate.

The constructed target and ordinary raw point are the exact frozen rows
in [coefficients.json](../n131_w33_freecode_resultant_20261018/coefficients.json).
The first source code's product equals the archived `5990700`; the
second source code's rotated product equals the archived positive
coefficient-row value. The existing independent Sage replay checks the
signed pair source and group sum for this positive pair.

| Valid codes per slot | Frozen point rows | Norm degree | GCD outcomes | Parent wall | Sampled combined peak RSS | Monitor |
| ---: | --- | ---: | --- | ---: | ---: | --- |
| 256 | positive and public | 1,024 | degree 1, `(3,16722)`; degree 0 | 37.343 s | 494,501,888 B | intact |
| 1,024 | positive | 4,096 | degree 1, `(3,16722)` | 51.001 s | 684,785,664 B | intact |
| 4,096 | positive | 16,384 | degree 1, `(3,16722)` | 113.965 s | 2,354,397,184 B | sampling degraded |

All runs used one checked-Sage arithmetic worker and a 4-GiB sampled
combined RSS cap. The 256/1,024 runs had a 180-second child alarm and
190-second parent cap; the 4,096 run had a 300-second child alarm and
310-second parent cap. The 4,096 arithmetic result and child self-peak
`2,322,153,472 B` were saved before exit; its monitor reported degraded
sampling, so its resource envelope is recorded with that
qualification. The completed 256/1,024 receipts have intact monitoring.

| Width and point | Quartic construction | Balanced norm product | GCD | Target-dependent row interval |
| --- | ---: | ---: | ---: | ---: |
| 256 positive | 0.699 s | 0.644 s | 15.829 s | 17.260 s |
| 256 public | 0.429 s | 0.393 s | 14.250 s | 15.073 s |
| 1,024 positive | 2.672 s | 3.859 s | 36.558 s | 43.586 s |
| 4,096 positive | 5.972 s | 6.507 s | 91.392 s | 104.894 s |

The source-ready and vanisher setup intervals are separate in each
result. At width 4,096 the GCD consumed most of the target-dependent
work and the checked-Sage process used over 2.3 GiB. The full W20
source has 132,045 codes per slot, so the current dense Sage
representation needs a measured source-wide work and memory result
before it can enter a 600-second public-relation search. The bounded
pilot gives exact component costs, without extending those timings
into an unmeasured full-source performance claim.

## Independent replay and next implementation

[`direct_audit.cpp`](direct_audit.cpp) reconstructs the valid W20 codes
from the source support table, recomputes their products with the
independent native GF(2^131) kernel, and evaluates every frozen
resultant on the two 256-code and two 1,024-code Cartesian panels.
Its saved outputs are `ROW 0 1 3,16722` and `ROW 1 0` at each width.
[`verify.py`](verify.py) checks source and protocol hashes, all three
norm receipts, both complete native scans, and the 4,096 monitor flag.
The checked Sage runtime receipts precede the measured workers.

The next iteration should implement a packed or factored GCD/remainder
kernel for the same 4,096-code positive and public panels, with exact
code-pair replay and intact monitoring, then increase the subset under
the 4-GiB/600-second bound. A whole-source operation must be combined
with an output proposal law for the remaining free pair blocks before
the frozen public N131 point can yield an ordinary verified relation.
