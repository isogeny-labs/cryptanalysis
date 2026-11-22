# Protocol: plain negation-map rho selection round (frozen before any data)

Frozen on 2026-10-24, before any row of this experiment exists. The exploratory trace that motivated the arms is
`experiments/rho-walk-trace-20261024/` (#1092); its data used seed 20261024 and is not reused here.

## Question

Which of a small set of changes to the plain negation-map Pollard rho (`ca_rho_solve`) lowers
the mean operation count on random generic curves at 20 to 40 bits, measured against current `main`?

## Arms (compile-time measurement build, default behaviour unchanged)

`measure-arms.patch` (sha256 in `PROTOCOL.sha256`) applies to `src/rho.c` at `main` `fb701711f5ee`. Built with
`-DCA_RHO_MEASURE_ARMS` it reads these environment variables once per solve; unset, every variable keeps the
`main` behaviour exactly.

| variable | meaning | default |
|---|---|---|
| `CA_RHO_TABLE_DIV` | table budget `sqrt(n) / (div * lg)`, r the largest power of two within it, in [8, 1024] | 48 |
| `CA_RHO_R_SQRT` | k x 100; r = the power of two nearest to `k * sqrt(sqrt(n) / lg)`, within [8, 1024]; 0 keeps the budget rule | 0 |
| `CA_RHO_FAST_CYCLE` | 1: escape as soon as a walk's new point equals its point 2 or 4 committed steps back (same escape routine as the 64-step window) | 0 |
| `CA_RHO_FIXED_BASE` | 1: the multiplier table, walk starts and restarts take k*base and k*target as sums of stored 2^b*base and 2^b*target over the set bits of k. Each set bit costs one operation, exactly as `ca_group_mul` charges it; the 2 (bitlength - 1) doublings that build the stored tables are charged to setup. The walk and its random choices are unchanged. | 0 |
| `CA_RHO_DP_DIV` | distinguished points targeted per walk in the `dp_bits` rule | 32 |

Arms (each compared with `base`):

| arm | settings |
|---|---|
| `base` | no variable set |
| `control` | every variable set to its default: must equal `base` on every solve (identity control) |
| `T12` | TABLE_DIV=12 |
| `R1.0` | R_SQRT=100 |
| `F` | FAST_CYCLE=1 |
| `B` | FIXED_BASE=1 |
| `D128` | DP_DIV=128 |
| `F+B+D128` | the three above |
| `F+B+D128+T12` | + TABLE_DIV=12 |
| `F+B+D128+R0.7` | + R_SQRT=70 |
| `F+B+D128+R1.0` | + R_SQRT=100 |
| `F+B+D128+R1.5` | + R_SQRT=150 |

`main` is also run as a separate pass on the unflagged build of the same `main` source (`--arms main`); it must equal `base` on every solve.

## Workload

- Sizes (bits of the prime subgroup order r): 20, 24, 28, 32, 36, 40.
- 40 random curves per size x 50 targets each = 2,000 solves per size and arm. Curves are y^2 = x^3 + a x + b, a, b random non-zero over a prime p of about size+3 bits whose largest prime factor of #E has exactly `size` bits and cofactor <= 16 (`run.py: sample_curve`).
- Seed `20261025`. Curve stream `"<seed>:<bits>"`; target `"<seed>:<p>:<a>:<b>:<target index>"`; solver seed = target index + 1, one thread. Every arm solves the same targets with the same solver seed (paired).
- Metric: `group_ops` (`ca_stats.group_ops`), a deterministic count; no wall time is measured or claimed.

## Analysis (`analyze.py`, frozen with this protocol)

- Per size and arm: ratio of sums, arm / base, over all targets. Pooled: geometric mean over the 6 sizes of the per-size ratios.
- Intervals: bootstrap over curves (40 curves per size resampled with replacement, the same resamples for every arm, 10,000 resamples, numpy seed 20261025). Bonferroni over the m = 10 arm-versus-base comparisons: the (0.05/10, 1 - 0.05/10) percentiles, about 99.5% two-sided.
- An arm **meets the winner criteria** iff all of: (1) its pooled interval's upper bound is below 1; (2) no size has an interval whose lower bound is above 1 (no significant regression at any size); (3) every solve of every arm recovered the planted logarithm.
- The **selected** arm is the one meeting the criteria with the lowest pooled ratio. If none meets them, nothing is selected and the result is reported as negative.
- Checks reported with the result: `control` equals `base` on every solve; unflagged `main` equals `base` on every solve; all logarithms correct.

## Predictions written before the data (to be scored, not tuned to)

- `B` lowers operations at every size by the setup saving alone (no change to any walk): about 13% at 20 to 28 bits, 10% at 32 to 36 bits, 5% at 40 bits.
- `F` lowers operations where cycles are frequent (20 to 28 bits); about 0 at 36 and 40 bits.
- `R1.0` and `T12` lower operations at 24 and 28 bits; `T12` may raise them at 36 and 40 bits, where r reaches 1024.
- `D128` changes operations by at most 2%.

## Limits (declared in advance)

- Operation counts, not time. A larger table, a smaller DP spacing and a different start cost change cache and memory behaviour; wall time needs a Tier 1 run.
- Generic curves with the negation map only; no GLV structure. One thread.
- 40 curves per size; the per-size intervals are wide where the arms change the walk.
- The arm list was chosen after the exploratory trace of the same generator family (different seed).
