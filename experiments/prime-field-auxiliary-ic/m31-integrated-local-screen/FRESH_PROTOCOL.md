# Fresh-target inline witness confirmation

Freeze before generating target coordinates. Generate five distinct nonzero
scalars from `random.Random(2026112743)` modulo N=2147505293 and publish only
their public points to the worker. Keep evaluator scalars separate until all
worker outputs are saved. On the fixed curve y²=x³+2x+14, generator
(1,814455902), compare six paths on each point and seeds 0,1,2:

1. Original PairIndex, B256 interval, m2, 64 lanes.
2. Original PairIndex, B384 interval, m2, 64 lanes.
3. Inline-first-witness PairIndex, B384 interval, m2, 64 lanes.
4. Original PairIndex, B768 interval, m2, 64 lanes.
5. Inline-first-witness PairIndex, B768 interval, m2, 64 lanes.
6. Archived C++ rho on the same public coordinates.

Use 4M query and 5s online caps for IC, 20s process deadline for all arms,
and one fresh process per arm. Charge wall and parent-plus-child CPU from
before process launch through exit and parsing; include IC basis generation,
pair-index construction, online search, certificate replay and teardown.
Compile binaries before timing. Balance arm order by target index and seed,
then shuffle the 15 blocks with `random.Random(2026112744)`. Preserve all
results, failures and censored arms. Each same-size original/inline pair must agree on exact
certificate, work counts and answer; verify all solved answers with an
independent group multiplication. Report paired wall and CPU ratios separately
for inline/original B384 and B768, each inline size/original B256, and each
inline size/rho, along with
success counts and target-level values. Do not turn a censored denominator
into a finite speed ratio. This is a single-host exploratory confirmation,
not a general prime-field or asymptotic claim.

Amendment before target generation: the original four-arm draft omitted B384,
which had the best same-target cold median in the exploratory size screen.
This six-arm version was fixed before any held-out coordinates were drawn.
