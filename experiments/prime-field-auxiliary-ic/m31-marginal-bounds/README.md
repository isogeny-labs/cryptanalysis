# Query bounds with dependent draws

The audited two-point protocol requires a certificate with at least three nonzero weights on distinct rows. With k base points in an odd-order group, at most 2k² group elements can yield a nonidentity signed pair. For the 17-coordinate M31 fixture there are 578 such elements among 2,147,505,293. Assume each query has a uniform marginal distribution on this group, with arbitrary dependence between queries. A per-query unconditional eligible-hit probability bounded by 2k²/N also suffices. These are hypotheses about a distribution over runs. An idealized walk started at an independently uniform group point and translated by offsets independent of that start has uniform marginals, since each fixed translation is a bijection. The recorded deterministic seeds alone do not prove these hypotheses. The archived certificates for seeds 0, 1 and 2 use eight, seven and five distinct rows respectively. Three is the protocol minimum used for the bound.

For q queries let H be the number of eligible hits, counting duplicates. The probability of a valid certificate is at most P(H ≥ 3), which is at most E[H]/3 ≤ q·2k²/(3N). This follows from summing the pointwise indicator inequality 3·1[certificate] ≤ H over trajectories. The Lean theorem budget proves the finite weighted inequality for any required number of hits. No independence or sampling-without-replacement premise is used.

| Base size | Upper bound on certificate probability by 100,000 queries | Lower bound on the median, in queries |
|---:|---:|---:|
| 17 | 0.8972% | 5,573,111 |
| 20 | 1.2418% | 4,026,573 |
| 32 | 3.1789% | 1,572,880 |

The median column rounds 3N/(4k²) upward. Collisions among pair sums can only tighten these upper probability bounds. The results apply to uniform marginals and the audited certificate condition. They are neither wall-clock comparisons nor predictions for a biased query distribution.

## Why the seed-1 surprise depends on independence

The archived seed 1 collected 14 distinct rows by query 19,300,166. For independent uniform draws the probability of accumulating 14 distinct classes this soon is 0.08063% (sibling m31-stopping-calibration). With uniform marginals alone the upper bound on this hit-count event is 37.10–37.11%. This larger bound is attainable for abstract correlated draws. With probability qh/14 choose 14 uniformly random distinct query positions and assign them 14 uniformly sampled distinct eligible row classes, selecting one of each class's two points at random. On all other positions draw uniformly from ineligible points. Here h=578/N and qh/14<1. Each position is eligible with probability h and each point has marginal probability 1/N. The event of 14 distinct rows then has exactly the chosen probability. This construction concerns hit counts and does not claim that the archived walk follows this distribution or that these rows are linearly dependent.

Use Lean 4.28 and Mathlib to check Marginals.lean. The protocol's certificate invariant is checked in snapshot/algebraic/end_to_end/benchmark.py. The bound and its numeric thresholds are independent of machine speed.
