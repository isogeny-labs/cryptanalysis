# Disclosures beside the section 5a band (run 39882571652)

Computed by `disclosures.py` from the archived receipts; the frozen band (`band.py`) is unchanged and stays the record. Case SHF-20261106-a114e7. `[pcc:unverified]`

## 1. Every counter, mean per solved target (CAX-2)

Class is the frozen kind map (`band.py` `CLASSES`): group (priced at 1 GAE), unpriced (priced at w), reported (counted, not priced), bounded (rho scalar multiplications, 0 or 104 GAE).

**P**

| counter | class | mean count |
| --- | --- | ---: |
| `ec_add` | group | 40353.1 |
| `ec_double` | group | 61007.8 |
| `ec_scalar_mul` | reported | 1201 |
| `field_half_trace` | reported | 7.84914e+08 |
| `field_inv` | reported | 3.45312e+07 |
| `field_mul` | reported | 8.54463e+09 |
| `field_sqr` | reported | 1.56999e+09 |
| `la_row_eliminations` | reported | 64231 |
| `canonicalizations` | unpriced | 1.56972e+09 |
| `descent_mulmods` | unpriced | 4 |
| `ec_add_trivial` | unpriced | 1201 |
| `ec_frobenius` | unpriced | 0 |
| `ec_lift_x` | unpriced | 0 |
| `fold_rotations` | unpriced | 0 |
| `frobenius_x` | unpriced | 7.45987e+08 |
| `la_inversions` | unpriced | 600 |
| `la_mulmods` | unpriced | 1.71766e+07 |
| `relation_lifts` | unpriced | 601 |
| `root_filter_inserts` | unpriced | 0 |
| `root_filter_queries` | unpriced | 0 |
| `root_index_inserts` | unpriced | 5.976e+07 |
| `root_index_probes` | unpriced | 1.50996e+09 |
| `s3_root_solves` | unpriced | 7.84916e+08 |
| `s3_root_solves_library` | unpriced | 2647 |

Totals: field_kinds 1.093e+10, group 1.014e+05, reported 1.093e+10, unpriced 4.688e+09

**S**

| counter | class | mean count |
| --- | --- | ---: |
| `ec_add` | group | 40081.1 |
| `ec_double` | group | 61007.8 |
| `ec_scalar_mul` | reported | 1201 |
| `field_half_trace` | reported | 5.1597e+08 |
| `field_inv` | reported | 1.80611e+07 |
| `field_mul` | reported | 5.63106e+09 |
| `field_sqr` | reported | 1.03211e+09 |
| `la_row_eliminations` | reported | 60197 |
| `canonicalizations` | unpriced | 1.03194e+09 |
| `descent_mulmods` | unpriced | 4 |
| `ec_add_trivial` | unpriced | 1201 |
| `ec_frobenius` | unpriced | 0 |
| `ec_lift_x` | unpriced | 0 |
| `fold_rotations` | unpriced | 2.98559e+06 |
| `frobenius_x` | unpriced | 4.95042e+08 |
| `la_inversions` | unpriced | 600 |
| `la_mulmods` | unpriced | 1.56927e+07 |
| `relation_lifts` | unpriced | 601 |
| `root_filter_inserts` | unpriced | 0 |
| `root_filter_queries` | unpriced | 0 |
| `root_index_inserts` | unpriced | 2.98806e+07 |
| `root_index_probes` | unpriced | 1.00196e+09 |
| `s3_root_solves` | unpriced | 5.15971e+08 |
| `s3_root_solves_library` | unpriced | 2647 |

Totals: field_kinds 7.197e+09, group 1.011e+05, reported 7.197e+09, unpriced 3.093e+09

**rT**

| counter | class | mean count |
| --- | --- | ---: |
| `scalar_multiplications` | bounded | 35 |
| `group_additions` | group | 8.88215e+06 |
| `canonicalizations` | unpriced | 8.88215e+06 |
| `failed_collisions` | unpriced | 0 |
| `partition_hashes` | unpriced | 8.74155e+06 |
| `table_inserts` | unpriced | 138876 |
| `table_queries` | unpriced | 138877 |

Totals: bounded 35, field_kinds 0, group 8.882e+06, unpriced 1.79e+07

## 2. Field kinds charged at w (CAX-2 sensitivity)

| arm | map | gap w=0 | w=0.1 | w=1 | crossover w* (b=0) | w* (b=104) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| P | frozen_map | 0.01141 | 43.93 | 175 | 0.0018804 | 0.0018812 |
| S | frozen_map | 0.01138 | 29 | 115.5 | 0.0028551 | 0.0028563 |
| P | field_kinds_charged | 0.01141 | 146.4 | 583.3 | 0.00056274 | 0.00056297 |
| S | field_kinds_charged | 0.01138 | 96.43 | 384.2 | 0.00085479 | 0.00085514 |

Pairs with field kinds charged: P vs S: S is cheaper than P at every weight of the band; P vs rT: unresolved: the order of P and rT is not the same at every weight (it changes by w = 0.1, 1); S vs rT: unresolved: the order of S and rT is not the same at every weight (it changes by w = 0.1, 1)

## 3. Phases the band unit does not charge (CAN-2)

The IC costs in the band, and so every IC gap at w >= 0.1, are **lower bounds**:

- Factor-base construction: every IC process loads the K600 base (base_source retained_header); `ec_frobenius` (base construction) totals seen in the IC records: [0]. X = 427.524 ms (docs/ic/baselines.json other_records[13].uncharged_phases.measurement_status (replay run 39007026856, Intel Xeon 8573C)) is 2.27e+06 GAE at this run's rT step of 188.33 ns if all of it were group additions (X is wall time on another host class; dividing it by this run's rho step mixes hosts and prices construction as if it were all group additions, so it is a bound for illustration, not a count).
  - S: gap at w=0 0.01138 in the band, at most 0.267 with X added; crossover w* then 0.002117.
  - P: gap at w=0 0.01141 in the band, at most 0.267 with X added; crossover w* then 0.0013943.
- Linear algebra: the unit takes cS / cP's checked cached-table load, not the rank process's solve.
  - S: the rank process's LA phase has 179700 unpriced operations outside the unit; gap at w=1 115.5026 -> 115.5093 with them.
  - P: the rank process's LA phase has 179700 unpriced operations outside the unit; gap at w=1 175.0188 -> 175.0255 with them.

No ruling changes: w=0 stays below 1 and w >= 0.1 above 1 for both arms.

## 4. Rank-seed variance and Monte-Carlo digits (CAN-3)

- The paired bootstrap resamples the 20 cold points only; kS and kP are one rank process each (seed 101), so their rank stage is a constant in every resample and the intervals carry no rank-seed variance.
- S: the rank stage is 97.44% of the unit's unpriced work. Archived twin rank probes seed 102 / seed 101 = 1.01377; scaling the rank stage by it (extrapolation, not a measurement) gives gaps 0.01138 / 29.38 / 117.1 at w = 0 / 0.1 / 1.
- P: the rank stage is 96.72% of the unit's unpriced work. Archived twin rank probes seed 102 / seed 101 = 0.97307; scaling the rank stage by it (extrapolation, not a measurement) gives gaps 0.01141 / 42.79 / 170.5 at w = 0 / 0.1 / 1.
- S < P at w = 0 is a single-seed order: S / P = 0.997317, a difference of 272 group operations between one kS and one kP rank draw (seed 101). It is not a ranking across rank seeds.
- Bootstrap bounds at b = 0 under other seeds and draw counts (quote them to 3 significant figures):

| arm | w | seed20261023_draws10000 | seed1_draws10000 | seed987654321_draws40000 |
| --- | --- | --- | --- | --- |
| S | 0 | 0.01138 [0.008767, 0.01552] | 0.01138 [0.008801, 0.01543] | 0.01138 [0.008803, 0.01531] |
| S | 0.1 | 29 [22.33, 39.54] | 29 [22.42, 39.3] | 29 [22.42, 39] |
| S | 1 | 115.5 [88.94, 157.5] | 115.5 [89.3, 156.5] | 115.5 [89.33, 155.3] |
| P | 0 | 0.01141 [0.00879, 0.01556] | 0.01141 [0.008825, 0.01547] | 0.01141 [0.008827, 0.01535] |
| P | 0.1 | 43.93 [33.83, 59.92] | 43.93 [33.97, 59.54] | 43.93 [33.98, 59.08] |
| P | 1 | 175 [134.8, 238.7] | 175 [135.3, 237.2] | 175 [135.4, 235.4] |

## 5. Memory (CAN-5)

| arm | runs | peak RSS min | median | max | stored table entries (mean) |
| --- | ---: | ---: | ---: | ---: | ---: |
| kS | 1 | 1876 MB | 1876 MB | 1876 MB | 2.98782e+07 |
| kP | 1 | 5813 MB | 5813 MB | 5813 MB | 2.98782e+07 |
| cS | 20 | 1875 MB | 1875 MB | 1876 MB | 2.98782e+07 |
| cP | 20 | 5813 MB | 5813 MB | 5814 MB | 2.98782e+07 |
| rT | 20 | 18.44 MB | 18.62 MB | 56.71 MB | 138876 |

IC / rT peak RSS against rT's median: kS 101x, kP 312x, cS 101x, cP 312x; against rT's maximum: kS 33x, kP 103x, cS 33x, cP 103x. On memory every IC arm is worse than rT, so the w = 0 end of the band (IC cheaper in GAE) is not a Pareto point: rT is undominated at every weight.

