# What a rho step costs, and what tuning can move

A worked application of [INSTRUCTION-COST-ACCOUNTING.md](INSTRUCTION-COST-ACCOUNTING.md)
to the library's hot loop. The conclusion is negative — the step is at its
arithmetic floor — and the point of writing it down is that the negative result
is checkable, not asserted.

## The ledger

`ca_rho_solve` on a native `E(F_p)` group runs 256 simultaneous walks and pays
one batch inversion per batch, so per step:

| row | per step | where |
|---|---|---|
| affine add | 3 muls | `lambda`, `x3`, `y3` in `ca_ec_add_with_di` |
| batch-inverse products | 3 muls | suffix product, `di`, running inverse |
| batch inversion | 0.703 muls | one `ca_mont_inv` per 256 steps, priced at 180 muls |
| **total** | **6.703 muls** | |

The inversion price is measured, not assumed: `ca_bench ops` reports 450 ns for
a single affine add (one inversion plus five muls), and the same benchmark's
batch figure implies about 2.5 ns per Montgomery multiplication, so an
inversion is about 180 multiplications — 10% of a step, and 42% if the batch
were 64 walks (`tools/cost/examples/rho-walk-w64.json`).

```sh
python3 tools/cost/ledger.py check tools/cost/examples/rho-walk-w*.json
```

## What was tried, and what it did

Measured by alternating two binaries built from the same sources, five paired
runs each, alternating order, median of the paired ratios (`rho_timing` at
2^40, single thread). On this machine the clock drifts from 3.7 GHz to under
1.3 GHz within a session, so only paired ratios mean anything.

| change | mechanism | median paired ratio |
|---|---|---|
| `RHO_CHAINS` 4 -> 8 | halve the serial inverse chains | 1.02 |
| `-march=native` | better scheduling | 1.02 |
| `-fno-unroll-loops` | clang unrolling a dependent chain | 1.000 |
| `-O2` instead of `-O3` | less aggressive scheduling | 1.005 |

None moved the step. That is consistent with the ledger: six multiplies at
2.5 ns is 15 ns, which is what the step measures (median 15.0 ns over 30
runs), so the loop is throughput-bound on the multiply, and re-arranging the
dependency chains cannot help.

## The row that does move: steps, not cost per step

Total cost is `steps x cost/step`. The step is fixed, so the only other lever
is `S = group ops / sqrt(order)`. Measured over 41 seeds at 2^40 with
`ca_rho_solve` on a fixed curve (operations, not seconds — the clock is not
trustworthy):

| walks | r | S |
|---|---|---|
| 256 | auto (512) | 1.16 |
| 256 | 512 | 1.128 |
| 128 | 128 | 0.967 |
| 64 | 32 | 0.830 |

The floor for a negation-map rho is about `1.25/sqrt(2) = 0.884` times
`sqrt(n)`; the default operating point sits 30% above it at this size, and the
small-walk configurations sit below it (DP-table sharing).

**It does not follow that the default should change.** Take the 64-walk point:
it finds the answer in about 25% fewer operations, but the ledger says it costs
2.11 more multiplications per step (+31%), and the inversion it saves is
priced at a 60-bit curve's inversion. At production sizes the inversion is
several times dearer and the table-sharing effect that produces the low `S`
disappears, so the trade turns negative. The auto rule that caps the
walk-table build at `sqrt(n)/16` operations is doing the right thing.

## What to do next

The honest lever is not in this file. `S` at production scale needs a machine
with stable clocks and an op-count harness, not wall-clock on a laptop:
`ca_bench generic --json` already emits the counts, so the comparison can be
made at 2^48+ where the setup effects are gone.

## A measurement caveat for `docs/BENCHMARKS.md`

The `zp 61-bit mulmod` row of `ca_bench ops` is `ca_group_op` through the
generic vtable on a 32-byte element, not a raw Montgomery multiply; the number
understates the arithmetic and overstates the dispatch. Worth renaming before
anyone quotes it as the multiplication cost.
