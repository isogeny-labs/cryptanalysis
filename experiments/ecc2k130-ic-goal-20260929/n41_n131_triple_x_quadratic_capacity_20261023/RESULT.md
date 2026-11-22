# Quadratic screen capacity for W23 triple-sum sources

The squarefree quadratic lift of triple-sum x-coordinates preserves exact
exclusion for the frozen N131 public point across the first 270 W23 source-code
families. Its affine span reaches the full 8,646-dimensional feature space at
family 271, so this particular linear screen ceases to exclude any x-coordinate
after that prefix. Independent GF(2) elimination reproduced every rank and
every target decision for all 280 families.

## Method

The field, curve, subgroup, point encoding, public input, and W23 source law
are pinned by curve `EC1N131Ckb1heb5f1998f20b`, the source hashes in the
four protocol files, and the archived public-point protocol linked from the
prior prefix-capacity experiment. Two pair codes are fixed. Each varying
first pair code is disjoint from the folded columns of edges 1 through 5;
each valid family produces 32 distinct x-coordinates of three-pair sums.
The first five codes replay the earlier exact point sets, then eligible raw
masks are scanned in ascending order. These 280 families are alternative
first-pair choices; they are not one simultaneous six-pair decomposition.

For the 131 bits `x_i`, the screen computes
`phi_2(x) = (x_i, x_i x_j for 0 <= i < j < 131)` over GF(2), with
`131 + C(131,2) = 8,646` coordinates. One source coordinate anchors the
affine span, and each later source contributes its difference from that
anchor. A public x-coordinate outside the span cannot belong to the exact
union of the source coordinates. The screen is a necessary condition only.
The full explicit source sets also permit exact hash membership; any later
speedup must obtain a comparable constraint without enumerating all source
coordinates for each target.

| First-slot families | Distinct x | Affine rank | Codimension | Frozen public x in span | Frozen public x in exact set |
| ---: | ---: | ---: | ---: | --- | --- |
| 1 | 32 | 31 | 8,615 | no | no |
| 5 | 160 | 159 | 8,487 | no | no |
| 64 | 2,048 | 2,047 | 6,599 | no | no |
| 128 | 4,096 | 4,095 | 4,551 | no | no |
| 256 | 8,192 | 8,191 | 455 | no | no |
| 269 | 8,608 | 8,607 | 39 | no | no |
| 270 | 8,640 | 8,639 | 7 | no | no |
| 271 | 8,672 | 8,646 | 0 | yes | no |
| 280 | 8,960 | 8,646 | 0 | yes | no |

The second frozen public-panel point has the same span decisions at these
prefixes. A constructed positive remains in the exact set and span at every
prefix. N41 W8 replay gives eight prefixes with ranks 31, 63, 95, 127, 159,
191, 223, 255 in a feature width of 861; that is a correctness control for
the lift, not a natural-relation yield measurement.

## Timing and verification

All timings below are component diagnostics on this ordinary host. The source
sets are reusable preparation for these fixed codes. The checked Sage launcher
and saved `sage_runtime_info.json` were used before the source job. The 280
N131 families were generated in 46.664 seconds with observed process peak
265,682,944 bytes. The Python feature/rank/target pass took 14.849 seconds,
partitioned as 8.613 feature construction, 5.029 rank reduction, 1.108
target checks, and 0.099 other seconds. The independent replay took 22.660
seconds and used a different feature order and low-pivot elimination; it
matched 280 ranks and 840 target checks. Its observed process peak was
34,684,928 bytes. These process peaks are observations, not a 4 GiB host cap.

`verify.py` checks all frozen source hashes, the 280 exact source sets, row
counts and rank boundaries, target decisions, and the independent audit
status. `PROOF_MAP.md` maps the checked structural Lean statements and the
remaining concrete rank proof obligation. `candidate_id` stays `null` because
this diagnostic does not specify a complete IC pipeline; online one-target
time, relation yield, rank gain, and same-point rho ratio are unknown here.

## Next experiment

Freeze an N41 W8 unpinned positive and ordinary negative query set, then
jointly constrain both three-pair partial sums under the public target rather
than screening one partial sum in isolation. The decisive measurement is
whether a compact exact compatibility condition rejects entire source-code
families before their 32 x-coordinates are enumerated, while retaining all
known valid decompositions. Record setup, target-dependent query and
enumeration work, false-positive families, complete witness replay, and a
same-input exact lookup baseline. Only then transfer the surviving design to
the N131 public point and its frozen 600-second/4-GiB envelope.
