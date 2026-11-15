# Q1592: incremental normal-basis updates for fixed-midpoint S3 inversion

Q1592 reduces the native kernel's N83 basis XOR count from 24,512,444 to
8,698,948 on 16 exact Q1480 ordinary right-pair states. The seven paired
replays have a 155.959 ms baseline median and a 134.478 ms incremental
median for the kernel interval, a 1.16× exploratory component ratio. Both
arms return the same exact pair set as direct enumeration on every state.
The archived positive-witness inputs each return one identical pair.

The implementation caches the `n` coefficients of the linear map
`a ↦ a² + s a` and the product branch as the sparse sum `s` changes. For
each changed normal-basis bit it XORs one precomputed product column into
each coefficient, rather than rebuilding each coefficient from every set
bit of `s`. This changes the computation of a fixed-midpoint inverse only;
it leaves all field multiplications, squares, inversions and Gaussian
elimination operations unchanged in the compared states.

## Exact workloads and accounting

The baseline is Q1461 compiled with the same flags. The new kernel uses the same
normal-basis field files, compiler flags, midpoint, leaf masks, weight
bounds and direct enumeration reference. The first 16 ordinary Q1480
right-pair snapshots are fixed for each degree. The input lines are checked
against Q1480's receipts during protocol freeze. Seven repetitions alternate
process order; setup and direct reference intervals are separate from the
reported kernel interval. These are shared-host exploratory timings, with
no CPU isolation receipt. The snapshots are an archived search prefix,
not a sample of successful decompositions.

| Field | Curve ID | Exact Q1480 base | Actual B | Folded K | Base SHA-256 |
| --- | --- | --- | ---: | ---: | --- |
| N53 | `EC1N53Ckb1hf77aab617904` | W≤4 | 324,042 | 3,057 | `9e12afb51aaf2bbf47640554ce88b3653903375c33489ce8b1e07abe6a649cae` |
| N83 | `EC1N83Ckb1h876c2921cb64` | W≤6 | 408,131,750 | 2,458,625 | `c1ee6d1064935976fc0d3e479f895fe4832722b5991ba148a6d6cb003b76330d` |

This is proposal `Q1592`, with `candidate_id: null`, `run_id: null`, and
`isogeny: "none"`. Its base sizes are the actual subgroup-usable point
counts before sign/Frobenius folding; the `K` values are matrix columns.
The [design](design.json), [source](incremental_sum.hpp),
[probe](probe.cpp) and [protocol](protocol.json) were frozen in commit
`28a5d82` before the paired runs. The positive-control
[amendment](positive_protocol.json) was frozen in `9bbf15c`, and the
independent raw-record [audit](audit.py) in `1495201` before its check.
The [result](result.json), [positive result](positive_result.json),
[audit result](audit_result.json), and 28 paired plus four positive raw
JSONL files preserve the operation counts and exact witness lists.

| Degree | Arm | Basis XORs | Elimination XORs | Field mul / sqr / inv | Seven-run median kernel interval | Median direct interval |
| ---: | --- | ---: | ---: | --- | ---: | ---: |
| 53 | Q1461 baseline | 142,196 | 176,127 | 992 / 1,712 / 16 | 1.352 ms | 31.018 ms |
| 53 | Q1592 incremental | 91,372 | 176,127 | 992 / 1,712 / 16 | 1.201 ms | 30.293 ms |
| 83 | Q1461 baseline | 24,512,444 | 29,976,208 | 1,488 / 2,672 / 16 | 155.959 ms | 147.285 ms |
| 83 | Q1592 incremental | 8,698,948 | 29,976,208 | 1,488 / 2,672 / 16 | 134.478 ms | 147.586 ms |

The audit compares all 224 paired ordinary state records, including
pair candidates, trace rejections, linear solutions, field operation
counts and witness lists. It also checks the N53 and N83 positive pair
sets against the archived Q1461 controls. The first 16 ordinary states at
each degree all have zero fixed-midpoint pair support. Thus this gain
improves one exact subroutine but does not determine successful ordinary
decomposition cost, N83 relation yield, novel rank, final matrix work,
target descent or a complete N131 `2^x`. The challenge gap remains unknown.

The next solver experiment must link the target and both broad pair
domains before fixing one midpoint. Reusing this kernel becomes useful
when that solver reaches a supported midpoint state and the sparse-sum
candidate bound is below its direct pair-product bound. Measure successful
ordinary relations and the charged cost per novel row on matched N53/N83
inputs before extrapolating to N131.

## Replay

```sh
python3 experiments/compact-s3-m4-20261003/q20261115_q1592_incremental_sum/run.py audit
python3 experiments/compact-s3-m4-20261003/q20261115_q1592_incremental_sum/positive.py audit
python3 experiments/compact-s3-m4-20261003/q20261115_q1592_incremental_sum/audit.py check
```

These commands validate the frozen files without overwriting the runs.
