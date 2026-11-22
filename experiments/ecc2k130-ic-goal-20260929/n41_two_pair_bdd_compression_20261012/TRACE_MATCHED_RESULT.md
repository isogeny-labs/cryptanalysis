# Trace-matched correction to the N41 two-pair BDD census

**Result.** The 200,000-value pair-output BDD has **1,237,720 nodes**, compared with **1,237,078** for random trace-zero reciprocals and **1,237,339** for random reciprocals with both `Tr(u)=0` and `Tr(1/u)=0`. The pair output is only **0.052%** and **0.031%** larger than these matched controls. The earlier 13% apparent saving came from controls that mixed trace classes. The sampled two-pair output BDD shows no measurable compression attributable to this source geometry under the tested bit order and sample sizes.

## Why the control changed

For the binary curve `y²+xy=x³+1`, `Tr(x(P+Q))=Tr(x(P))+Tr(x(Q))` is the established group character in the [prior exact trace experiment](../n41_pair_trace_xor_20261006/RESULT.md). The frozen source points are in the odd-order subgroup, so their sums have `Tr(x)=0`. Curve solvability for nonzero x gives `Tr(x)=Tr(1/x)`. In the chosen `GF(2)[t]/(t^41+t³+1)` polynomial basis, the absolute trace is the low coordinate bit. The [matched census](matched_census.py) recomputes the trace of all 41 basis vectors and checks that **all 200,000** sampled sum x-coordinates and reciprocals have low bit zero.

The original [result](RESULT.md) and [raw record](result.json) remain frozen. Its unrestricted and curve-valid controls describe broader populations; neither matches this subgroup trace property. The unrestricted control also converted its generated set to a list before taking prefixes, so its prefix ordering was not the draw order; its complete 200,000-value set is unaffected. This follow-up uses two fixed-seed native controls: 200,000 distinct nonzero reciprocals with `Tr(u)=0`, and 200,000 with both `Tr(u)=Tr(1/u)=0`. An independent Python path checks the field trace mask and 64 inverse/trace control values. Prefixes are taken in generation order, keeping each control's sampling law fixed.

| Distinct values | Pair BDD nodes | Trace-zero control | Point-trace control | Pair / point-trace |
| ---: | ---: | ---: | ---: | ---: |
| 25,000 | 300,645 | 300,136 | 300,409 | 1.000786 |
| 50,000 | 501,650 | 500,948 | 500,692 | 1.001913 |
| 100,000 | 806,345 | 806,134 | 806,147 | 1.000246 |
| 200,000 | 1,237,720 | 1,237,078 | 1,237,339 | 1.000308 |

The two source slots each contain 30,952 signed pair states. The 200,000 distinct sampled outputs are a subset of their 958,026,304 ordered Cartesian combinations. This measurement describes the sampled reciprocal coordinate sets; it does not measure an exact full-population BDD, a group-point and witness representation, or a target-dependent relation search. Timings in `matched_result.json` are ordinary-host construction diagnostics. The IC candidate ID remains null.

## Reproduce

From `/Volumes/SSD990/cryptanalysis` with the frozen `samples.tsv` already in this directory:

```sh
c++ -O3 -std=c++17 -o experiments/ecc2k130-ic-goal-20260929/n41_two_pair_bdd_compression_20261012/trace_control experiments/ecc2k130-ic-goal-20260929/n41_two_pair_bdd_compression_20261012/trace_control.cpp
experiments/ecc2k130-ic-goal-20260929/n41_two_pair_bdd_compression_20261012/trace_control experiments/ecc2k130-ic-goal-20260929/n41_two_pair_bdd_compression_20261012/trace_zero.tsv experiments/ecc2k130-ic-goal-20260929/n41_two_pair_bdd_compression_20261012/point_trace_zero.tsv 200000
python3 experiments/ecc2k130-ic-goal-20260929/n41_two_pair_bdd_compression_20261012/matched_census.py
```

`matched_result.json` records every input and source hash, full-sample parity checks, the 64 control checks, node counts, exploratory time, and macOS process RSS. `matched.stdout` retains the four output rows. The native generator recorded 400,690 attempts for the trace-zero control and 799,104 for the point-trace control. The executable is rebuilt from source and is not committed.

## Research decision

Coordinate-set BDD compression is not a promising route for the needed target-conditioned family constraint on this source. The next gate should operate on joint source witnesses and the public target before output enumeration. A smaller N41 test is an exact target-conditioned seed-family predicate that retains an eight-column witness and measures rejection while at least one pair source remains unresolved. Its cost must be source-bound before N131 promotion.
