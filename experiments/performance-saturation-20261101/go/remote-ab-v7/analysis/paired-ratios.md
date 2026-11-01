# Go coordinator remote A/B paired ratios

The frozen v7 campaign completed 120 measured pairs.  Candidate/baseline is
reported for allocation metrics; baseline/candidate is reported for wall and
process CPU time.  The frozen allocation threshold is at most `0.05` for both
allocation metrics in every case.  The frozen timing threshold is a median of
at least `1.05` plus a simultaneous lower bound above `1.0` for both clocks.

| Case | B/op C/B | allocs/op C/B | wall B/C | wall lower | CPU B/C | CPU lower |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| VersionVector/1024 | 0.001050153 | 0.143375174 | 14.792324x | 14.581290x | 14.800999x | 14.601912x |
| VersionVector/8192 | 0.000551148 | 0.142921913 | 15.556604x | 15.216288x | 15.551712x | 15.215209x |
| DeltaSince caught-up/1024 | 0.001049685 | 0.143235704 | 16.005901x | 15.850019x | 16.062301x | 15.883681x |
| DeltaSince caught-up/8192 | 0.000551089 | 0.142904475 | 16.573567x | 16.435902x | 16.570993x | 16.432595x |
| DeltaSince one-behind/1024 | 0.001059056 | 0.143494631 | 16.055981x | 15.872837x | 16.073516x | 15.910291x |
| DeltaSince one-behind/8192 | 0.000552261 | 0.142936858 | 16.626776x | 16.349834x | 16.631657x | 16.346380x |

All 120 fingerprint pairs matched.  Allocated bytes pass the 95% reduction
gate, but allocation event counts do not: their ratios are about `0.143`, so
the frozen combined allocation claim is unsupported.  Every individual timing
pair exceeds `12.75x`; the numeric timing conclusion is not sensitive to the
interval implementation.

## Deterministic sensitivity interval

V7 froze `analysis_plan.script` as null and did not specify a resample count,
RNG, percentile definition, or exact Holm interval construction.  The lower
bounds above are therefore explicitly post-hoc sensitivity results, not a
missing canonical preregistered output.

For each 20-ratio case/clock distribution, the analyzer exactly integrates the
joint empirical distribution of the 10th and 11th order statistics in 20
with-replacement draws.  Their average is the bootstrap median.  It reports the
lower quantile `0.05 / (2 * 12) = 1/480` using exact rational arithmetic.  This
two-sided Bonferroni family bound is stricter than Holm, so every lower bound
remaining far above one establishes the numerical gate under a percentile-
bootstrap interpretation.  No RNG or Monte Carlo tolerance is involved.

See [`paired-ratios.json`](paired-ratios.json) for exact numerators,
denominators, pair ranges, input hashes, isolation fields, and limitations.
