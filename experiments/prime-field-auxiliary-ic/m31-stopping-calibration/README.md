# Calibration of the uniform M31 stopping model

Seed 1 in the archived v2_batch runs reached its first dependent row at distinct row 14 after 19,300,166 queries. Under independent uniform group queries on the frozen 17-coordinate base, the probability of reaching 14 distinct classes by then is 0.00080632. The first-dependence model, before conditioning on the observed row count, puts its stopping time at the 3.015th percentile. This is a retrospective model diagnostic on three archived runs. It does not identify a cause of the discrepancy or measure a timing improvement.

| Seed | Queries | Distinct rows | Probability of first dependence by this query | Probability of this many distinct rows by this query |
|---:|---:|---:|---:|---:|
| 0 | 34,771,537 | 15 | 21.493% | 4.584% |
| 1 | 19,300,166 | 14 | 3.015% | 0.08063% |
| 2 | 45,496,514 | 9 | 45.089% | 84.981% |

There are m = k² classes, each represented by two group points, for the collision-free bases considered. Put N = 2,147,505,293. After q independent uniform queries, inclusion-exclusion gives the probability that precisely r classes have occurred as

```text
C(m,r) sum_{i=0..r} (-1)^(r-i) C(r,i) (1 - 2(m-i)/N)^q.
```

Conditional on this occupancy, the r-subset is uniform. Multiply its probability by the independent-subset fraction from the sibling m31-signed-graph-counts recurrence and sum to obtain the probability of still having independent rows. The waiting times for new classes are independent of their order of arrival under this model. The last column can therefore also be interpreted conditional on first dependence occurring at the indicated distinct row. The central 90% interval for queries to first dependence is 22.37–78.77 million for k=17 and 18.83–63.44 million for k=20.

For a separate bound on seed 1, any 14 distinct classes require at least 14 eligible hits. Let H be binomial with q trials and success probability p = 578/N. Above 14 hits, the ratio of consecutive probabilities is at most u = (q−14)p/[15(1−p)]. Also (1−p)^−(q−14) ≥ (1+p)^(q−14), which is bounded below by the first 17 terms of its binomial expansion. Hence P(H ≥ 14) is at most C(q,14)p^14 divided by this truncated expansion and by (1−u). Lean checks that this rational upper bound is below 0.001014. This bound assumes independent uniform queries and includes repeated hits.

Run `python3 calibration.py` for the discrete quantiles and archived-row replay. The inclusion-exclusion calculation uses 96-digit decimal arithmetic. A separate numerical absorbing-state transition matrix check agreed within 1e−7 for both base sizes at five query counts. Run Lean 4.28 with Mathlib on TailBound.lean to check the exact rational arithmetic of the binomial majorant.
